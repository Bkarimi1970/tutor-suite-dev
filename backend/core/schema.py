from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

Level = Literal["beginner", "intermediate", "advanced"]
Mode = Literal["solve", "attempt"]

class Meta(BaseModel):
    source: Optional[str] = "web"
    timestamp: Optional[str] = None

class TutorRequest(BaseModel):
    user_id: str
    level: Level = "beginner"
    mode: Mode = "solve"
    problem: str
    student_step: Optional[str] = None
    meta: Optional[Meta] = None

class TutorResponse(BaseModel):
    status: Literal["ok", "error"] = "ok"
    topic: str = ""
    final_answer: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    feedback: str = ""
    diagnosis: List[str] = Field(default_factory=list)
    next_practice: List[str] = Field(default_factory=list)
    mastery_update: Dict[str, float] = Field(default_factory=dict)
    error: Optional[str] = None
