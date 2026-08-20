from typing import TypedDict, Optional, Dict, Any, List
import json
import logging

from langgraph.graph import StateGraph, START, END

from .llm_client import call_llm
from .schemas import (
    MarketIntelligenceOutput,
    SkillDeltaOutput,
    RoadmapOutput,
    AdaptiveEvaluatorOutput
)
from .prompts import (
    MIA_SYSTEM_PROMPT,
    SPA_SYSTEM_PROMPT,
    GSA_SYSTEM_PROMPT,
    AEA_SYSTEM_PROMPT
)

logger = logging.getLogger("skillbridge.agents.graph")

class AgentState(TypedDict):
    resume_text: str
    target_role: str
    
    # Optional outputs populated by agents
    market_data: Optional[Dict[str, Any]]
    skill_delta: Optional[Dict[str, Any]]
    roadmap: Optional[Dict[str, Any]]
    evaluator: Optional[Dict[str, Any]]
    
    error: Optional[str]

async def mia_node(state: AgentState) -> AgentState:
    """Market Intelligence Agent node."""
    logger.info("Executing MIA node")
    target_role = state.get("target_role", "Software Engineer")
    
    user_prompt = f"Analyze the market for the following role: {target_role}"
    
    try:
        result = await call_llm(
            system_prompt=MIA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=MarketIntelligenceOutput,
            model="gpt-4o-mini"
        )
        return {"market_data": result}
    except Exception as e:
        logger.error(f"MIA failed: {e}")
        return {"error": f"MIA Error: {str(e)}"}

async def spa_node(state: AgentState) -> AgentState:
    """Skill Delta Agent node."""
    logger.info("Executing SPA node")
    if "error" in state and state["error"]:
        return state
        
    resume_text = state.get("resume_text", "")
    market_data = state.get("market_data", {})
    
    user_prompt = f"""
    Resume Text:
    {resume_text}
    
    Market Data for Target Role:
    {json.dumps(market_data, indent=2)}
    
    Compare the resume against the market data and provide a skill gap analysis.
    """
    
    try:
        result = await call_llm(
            system_prompt=SPA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=SkillDeltaOutput,
            model="gpt-4o-mini"
        )
        return {"skill_delta": result}
    except Exception as e:
        logger.error(f"SPA failed: {e}")
        return {"error": f"SPA Error: {str(e)}"}

async def gsa_node(state: AgentState) -> AgentState:
    """Generator Agent node."""
    logger.info("Executing GSA node")
    if "error" in state and state["error"]:
        return state
        
    skill_delta = state.get("skill_delta", {})
    target_role = state.get("target_role", "")
    
    user_prompt = f"""
    Target Role: {target_role}
    
    Skill Gap Analysis:
    {json.dumps(skill_delta, indent=2)}
    
    Generate a personalized upskilling roadmap based on these skill gaps.
    """
    
    try:
        result = await call_llm(
            system_prompt=GSA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=RoadmapOutput,
            model="gpt-4o-mini"
        )
        return {"roadmap": result}
    except Exception as e:
        logger.error(f"GSA failed: {e}")
        return {"error": f"GSA Error: {str(e)}"}

async def aea_node(state: AgentState) -> AgentState:
    """Adaptive Evaluator Agent node."""
    logger.info("Executing AEA node")
    if "error" in state and state["error"]:
        return state
        
    roadmap = state.get("roadmap", {})
    
    user_prompt = f"""
    Learning Roadmap:
    {json.dumps(roadmap, indent=2)}
    
    Create an adaptive assessment and grading rubric for this roadmap.
    """
    
    try:
        result = await call_llm(
            system_prompt=AEA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=AdaptiveEvaluatorOutput,
            model="gpt-4o-mini"
        )
        return {"evaluator": result}
    except Exception as e:
        logger.error(f"AEA failed: {e}")
        return {"error": f"AEA Error: {str(e)}"}

def should_continue(state: AgentState) -> str:
    """Routing function to check for errors and halt execution if needed."""
    if "error" in state and state["error"]:
        return "end"
    return "continue"

# Build the LangGraph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("MIA", mia_node)
workflow.add_node("SPA", spa_node)
workflow.add_node("GSA", gsa_node)
workflow.add_node("AEA", aea_node)

# Define Edges
workflow.add_edge(START, "MIA")
workflow.add_edge("MIA", "SPA")
workflow.add_edge("SPA", "GSA")
workflow.add_edge("GSA", "AEA")
workflow.add_edge("AEA", END)

# Compile the graph
app = workflow.compile()
