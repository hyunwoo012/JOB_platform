from __future__ import annotations  # forward reference 허용

from typing import List, Optional  # 타입 힌트
from datetime import datetime  # 시간 타입
from pydantic import BaseModel, Field  # Pydantic 기본/필드

from .models import (  # 모델의 Enum들
    UserRole,  # 사용자 역할
    JobPostStatus,  # 공고 상태
    ApplicationStatus,  # 지원 상태
)


# ---------- Auth ----------
class SignupRequest(BaseModel):  # 회원가입 요청
    email: Optional[str] = None  # 이메일(선택)
    phone: Optional[str] = None  # 전화번호(선택)
    password: str  # 비밀번호
    role: UserRole  # 사용자 역할


class LoginRequest(BaseModel):  # 로그인 요청
    email: Optional[str] = None  # 이메일(선택)
    phone: Optional[str] = None  # 전화번호(선택)
    password: str  # 비밀번호


class TokenResponse(BaseModel):  # 토큰 응답
    access_token: str  # JWT 토큰
    token_type: str = "bearer"  # 토큰 타입


# ---------- Users ----------
class UserOut(BaseModel):  # 사용자 응답
    id: int  # 사용자 ID
    email: Optional[str]  # 이메일
    phone: Optional[str]  # 전화번호
    role: UserRole  # 역할
    is_active: bool  # 활성화 여부

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


class StudentProfileUpsert(BaseModel):  # 학생 프로필 생성/수정
    name: str  # 이름
    school: Optional[str] = None  # 학교
    major: Optional[str] = None  # 전공
    skills: List[str] = Field(default_factory=list)  # 기술 목록
    available_time: Optional[str] = None  # 가능 시간


class StudentProfileOut(StudentProfileUpsert):  # 학생 프로필 응답
    user_id: int  # 사용자 ID

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


# ---------- Job Posts ----------
class JobPostCreate(BaseModel):  # 공고 생성 요청
    title: str  # 제목
    wage: Optional[int] = None  # 시급/급여
    description: str  # 상세 설명
    region: str  # 지역
    status: JobPostStatus = JobPostStatus.OPEN  # 상태


class JobPostUpdate(BaseModel):  # 공고 수정 요청
    title: Optional[str] = None  # 제목
    wage: Optional[int] = None  # 시급/급여
    description: Optional[str] = None  # 상세 설명
    region: Optional[str] = None  # 지역
    status: Optional[JobPostStatus] = None  # 상태
    is_deleted: Optional[bool] = None  # 삭제 여부


class JobPostImageCreate(BaseModel):  # 공고 이미지 생성 요청
    image_url: str  # 이미지 URL


class JobPostImageOut(BaseModel):  # 공고 이미지 응답
    id: int  # 이미지 ID
    job_post_id: int  # 공고 ID
    image_url: str  # 이미지 URL

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


class JobPostOut(BaseModel):  # 공고 응답
    id: int  # 공고 ID
    company_id: int  # 회사 ID
    title: str  # 제목
    wage: Optional[int]  # 시급/급여
    description: str  # 상세 설명
    region: str  # 지역
    status: JobPostStatus  # 상태
    is_deleted: bool  # 삭제 여부

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


# ---------- Application (채팅 요청) ----------
class ApplicationCreate(BaseModel):  # 지원 생성 요청
    job_post_id: int  # 공고 ID


class ApplicationOut(BaseModel):  # 지원 응답
    id: int  # 지원 ID
    job_post_id: int  # 공고 ID
    student_id: int  # 학생 ID
    company_id: int  # 회사 ID
    status: ApplicationStatus  # 지원 상태
    created_at: datetime  # 생성 시각
    responded_at: Optional[datetime]  # 응답 시각

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


# ---------- Chat ----------
class ChatRoomOut(BaseModel):  # 채팅방 응답
    id: int  # 채팅방 ID
    job_post_id: int  # 공고 ID
    company_id: int  # 회사 ID
    student_id: int  # 학생 ID

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원


class ChatMessageCreate(BaseModel):  # 채팅 메시지 생성 요청
    content: str  # 메시지 내용


class ChatMessageOut(BaseModel):  # 채팅 메시지 응답
    id: int  # 메시지 ID
    chat_room_id: int  # 채팅방 ID
    sender_id: int  # 발신자 ID
    content: str  # 메시지 내용

    class Config:  # Pydantic 설정
        from_attributes = True  # ORM 객체 지원
