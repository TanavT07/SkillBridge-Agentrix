from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# Legacy placeholder classes so graph.py imports don't fail
class RoleDemand(BaseModel):
    pass

class CandidateProfile(BaseModel):
    pass

class SkillMetaItem(BaseModel):
    pass

class SkillGapItem(BaseModel):
    pass

class SprintItem(BaseModel):
    pass

# The flexible master response model for the API
class FinalAnalysisResponse(BaseModel):
    status: str = "success"
    role: Optional[Dict[str, Any]] = None
    candidate: Optional[Dict[str, Any]] = None
    skillMeta: Optional[Dict[str, Any]] = None
    skillGaps: Optional[List[Any]] = None
    learningRoadmap: Optional[Dict[str, Any]] = None