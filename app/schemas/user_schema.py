from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.job_schema import JobResponse


class UserRegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    full_name: Optional[str] = Field(default=None, description="Optional full name")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id")
    email: EmailStr
    full_name: Optional[str] = None
    resume_uploaded: bool = False
    created_at: datetime
    updated_at: datetime
    saved_jobs_count: int = 0


class SavedJobsResponse(BaseModel):
    user_id: str
    total_saved_jobs: int
    jobs: list[JobResponse]
