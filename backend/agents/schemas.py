from typing import List, Optional
from pydantic import BaseModel, Field

# ==========================================
# Market Intelligence Agent (MIA) Schemas
# ==========================================

class SkillTrend(BaseModel):
    skill_name: str = Field(..., description="Name of the skill")
    demand_score: int = Field(..., description="Score from 1-100 indicating market demand")
    category: str = Field(..., description="Category of the skill (e.g., Technical, Soft Skill, Tool)")

class MarketIntelligenceOutput(BaseModel):
    job_title: str = Field(..., description="The standardized job title analyzed")
    trending_skills: List[SkillTrend] = Field(..., description="List of trending skills for this role")
    average_salary_usd: Optional[int] = Field(None, description="Estimated average salary in USD")
    industry_insights: str = Field(..., description="Summary of current industry trends for this role")
    required_experience_years: str = Field(..., description="Typical years of experience required")


# ==========================================
# Skill Delta Agent (SPA) Schemas
# ==========================================

class SkillMatch(BaseModel):
    skill_name: str = Field(..., description="Name of the skill")
    match_level: str = Field(..., description="Level of match (e.g., Full, Partial, Missing)")
    priority_score: int = Field(..., description="Score from 1-10 indicating priority to learn")

class SkillDeltaOutput(BaseModel):
    readiness_score: int = Field(..., description="Overall readiness score from 1-100")
    skill_gaps: List[SkillMatch] = Field(..., description="List of skills analyzed against market requirements")
    delta_summary: str = Field(..., description="Summary of the candidate's skill gaps and strengths")


# ==========================================
# Generator Agent (GSA) Schemas
# ==========================================

class Module(BaseModel):
    title: str = Field(..., description="Title of the learning module")
    description: str = Field(..., description="Description of what will be learned")
    estimated_hours: int = Field(..., description="Estimated hours to complete")
    resources: List[str] = Field(..., description="List of recommended resources (links, books, courses)")

class RoadmapOutput(BaseModel):
    target_role: str = Field(..., description="The target job role for the roadmap")
    total_estimated_hours: int = Field(..., description="Total estimated hours for the entire roadmap")
    modules: List[Module] = Field(..., description="Sequential list of learning modules")
    capstone_project: str = Field(..., description="Description of a final hands-on project")


# ==========================================
# Adaptive Evaluator Agent (AEA) Schemas
# ==========================================

class Question(BaseModel):
    question_text: str = Field(..., description="The text of the assessment question")
    question_type: str = Field(..., description="Type of question (e.g., Multiple Choice, Coding, Short Answer)")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice questions")
    correct_answer: str = Field(..., description="The correct answer or expected logic")

class EvaluationRubric(BaseModel):
    criteria: str = Field(..., description="What is being evaluated")
    weight: int = Field(..., description="Weight or importance of this criteria (percentage)")

class AdaptiveEvaluatorOutput(BaseModel):
    assessment_title: str = Field(..., description="Title of the assessment")
    difficulty_level: str = Field(..., description="Overall difficulty level (Beginner, Intermediate, Advanced)")
    questions: List[Question] = Field(..., description="List of questions for the assessment")
    rubric: List[EvaluationRubric] = Field(..., description="Rubric used to grade the assessment")
