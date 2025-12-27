from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from .models import UserRole, JobPostStatus


# ---------- Auth ----------
class SignupRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Users ----------
class UserOut(BaseModel):
    id: int
    email: Optional[str]
    phone: Optional[str]
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True


class StudentProfileUpsert(BaseModel):
    name: str
    school: Optional[str] = None
    major: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    available_time: Optional[str] = None


class StudentProfileOut(StudentProfileUpsert):
    user_id: int

    class Config:
        from_attributes = True


# ---------- Job Posts ----------
class JobPostCreate(BaseModel):
    title: str
    wage: Optional[int] = None
    description: str
    region: str
    status: JobPostStatus = JobPostStatus.OPEN


class JobPostUpdate(BaseModel):
    title: Optional[str] = None
    wage: Optional[int] = None
    description: Optional[str] = None
    region: Optional[str] = None
    status: Optional[JobPostStatus] = None
    is_deleted: Optional[bool] = None


class JobPostImageCreate(BaseModel):
    image_url: str


class JobPostImageOut(BaseModel):
    id: int
    job_post_id: int
    image_url: str

    class Config:
        from_attributes = True


# 🔴 images 제거한 버전 (핵심)
class JobPostOut(BaseModel):
    id: int
    company_id: int
    title: str
    wage: Optional[int]
    description: str
    region: str
    status: JobPostStatus
    is_deleted: bool

    class Config:
        from_attributes = True


# ---------- Chat ----------
class ChatRoomCreate(BaseModel):
    job_post_id: int
    student_id: int  # 기업이 열 때 필요


class ChatRoomOut(BaseModel):
    id: int
    job_post_id: int
    company_id: int
    student_id: int

    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: int
    chat_room_id: int
    sender_id: int
    content: str

    class Config:
        from_attributes = True
