from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier for the user")
    username: str = Field(..., description="Display name of the user")
    role: Optional[str] = Field("user", description="User role, e.g., 'user' or 'admin'")

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: str

    class Config:
        from_attributes = True

class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=5, description="The body of the question being submitted")
    category: str = Field(..., description="Category tag (e.g. Account, Pricing, Bug, General)")
    user_identifier: str = Field(..., description="Unique ID of the user submitting the question")

class QuestionResponse(BaseModel):
    id: int
    question_text: str
    category: str
    cluster_id: Optional[int]
    user_identifier: str
    status: str
    created_at: str

    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    cluster_id: int = Field(..., description="The ID of the question cluster being upvoted")
    user_identifier: str = Field(..., description="Unique ID of the user casting the vote")

class VoteResponse(BaseModel):
    success: bool
    cluster_id: int
    new_score: float
    message: str

class ClusterResponse(BaseModel):
    id: int
    representative_question_id: Optional[int]
    representative_text: Optional[str] = None
    category: Optional[str] = None
    answer_text: Optional[str] = None
    ai_draft_text: Optional[str] = None
    priority_score: float
    created_at: str
    votes_count: int
    questions: List[QuestionResponse] = []

    class Config:
        from_attributes = True
