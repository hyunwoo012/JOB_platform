from __future__ import annotations  # forward reference 허용

import enum  # Enum 기본
from typing import List, Optional  # 타입 힌트

from sqlalchemy import (  # SQLAlchemy 컬럼/타입
    BigInteger,  # 큰 정수 타입
    Boolean,  # 불리언 타입
    DateTime,  # 날짜/시간 타입
    ForeignKey,  # 외래키
    Integer,  # 정수 타입
    String,  # 문자열 타입
    Text,  # 텍스트 타입
    UniqueConstraint,  # 유니크 제약
    func,  # DB 함수
)
from sqlalchemy.dialects.postgresql import JSONB  # Postgres JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship  # ORM 매핑
from sqlalchemy import Enum as SAEnum  # SQLAlchemy Enum

from .database import Base  # ORM 베이스


class UserRole(str, enum.Enum):  # 사용자 역할 Enum
    STUDENT = "STUDENT"  # 학생
    COMPANY = "COMPANY"  # 회사
    ADMIN = "ADMIN"  # 관리자


class JobPostStatus(str, enum.Enum):  # 공고 상태 Enum
    OPEN = "OPEN"  # 모집 중
    CLOSED = "CLOSED"  # 마감


class ApplicationStatus(str, enum.Enum):  # 지원 상태 Enum
    REQUESTED = "REQUESTED"  # 요청됨
    ACCEPTED = "ACCEPTED"  # 수락됨
    REJECTED = "REJECTED"  # 거절됨


class User(Base):  # 사용자 모델
    __tablename__ = "users"  # 테이블명

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # PK

    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)  # 이메일
    phone: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True)  # 전화번호
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # 비밀번호 해시

    role: Mapped[UserRole] = mapped_column(  # 역할 컬럼
        SAEnum(UserRole, name="user_role", native_enum=True),  # Enum 타입
        nullable=False,  # 필수
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # 활성 여부
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 생성 시각

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(  # 학생 프로필 1:1
        "StudentProfile", back_populates="user", uselist=False  # 역참조 설정
    )

    job_posts: Mapped[List["JobPost"]] = relationship("JobPost", back_populates="company")  # 회사 공고 목록
    sent_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="sender")  # 보낸 메시지

    student_applications: Mapped[List["Application"]] = relationship(  # 학생이 보낸 지원
        "Application", foreign_keys="Application.student_id", back_populates="student"  # FK 지정
    )
    company_applications: Mapped[List["Application"]] = relationship(  # 회사가 받은 지원
        "Application", foreign_keys="Application.company_id", back_populates="company"  # FK 지정
    )


class StudentProfile(Base):  # 학생 프로필 모델
    __tablename__ = "student_profiles"  # 테이블명

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)  # PK=FK

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 이름
    school: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)  # 학교
    major: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)  # 전공

    skills: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)  # 기술 목록(JSONB)
    available_time: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 가능 시간

    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 갱신 시각

    user: Mapped["User"] = relationship("User", back_populates="student_profile")  # 사용자 역참조


class JobPost(Base):  # 공고 모델
    __tablename__ = "job_posts"  # 테이블명

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # PK
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)  # 회사 FK

    title: Mapped[str] = mapped_column(String(200), nullable=False)  # 제목
    wage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 시급/급여
    description: Mapped[str] = mapped_column(Text, nullable=False)  # 상세 설명
    region: Mapped[str] = mapped_column(String(100), nullable=False)  # 지역

    status: Mapped[JobPostStatus] = mapped_column(  # 상태
        SAEnum(JobPostStatus, name="job_post_status", native_enum=True),  # Enum 타입
        nullable=False,  # 필수
        server_default="OPEN",  # 기본값
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # 논리 삭제

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 생성 시각
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 수정 시각

    company: Mapped["User"] = relationship("User", back_populates="job_posts")  # 회사 역참조
    images: Mapped[List["JobPostImage"]] = relationship(  # 이미지 목록
        "JobPostImage", back_populates="job_post", cascade="all, delete-orphan"  # 자식 삭제 연쇄
    )

    chat_rooms: Mapped[List["ChatRoom"]] = relationship("ChatRoom", back_populates="job_post")  # 공고 기준 채팅방

    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job_post")  # 공고 지원 목록


class JobPostImage(Base):  # 공고 이미지 모델
    __tablename__ = "job_post_images"  # 테이블명

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # PK
    job_post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False)  # 공고 FK

    image_url: Mapped[str] = mapped_column(Text, nullable=False)  # 이미지 URL
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 생성 시각

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="images")  # 공고 역참조


class Application(Base):  # 지원 모델
    __tablename__ = "applications"  # 테이블명

    id: Mapped[int] = mapped_column(  # PK
        BigInteger,  # 타입
        primary_key=True,  # PK 지정
        autoincrement=True,  # 자동 증가
        index=True,  # 인덱스
    )

    job_post_id: Mapped[int] = mapped_column(  # 공고 FK
        BigInteger,  # 타입
        ForeignKey("job_posts.id", ondelete="CASCADE"),  # FK
        nullable=False,  # 필수
    )

    student_id: Mapped[int] = mapped_column(  # 학생 FK
        BigInteger,  # 타입
        ForeignKey("users.id", ondelete="CASCADE"),  # FK
        nullable=False,  # 필수
    )

    company_id: Mapped[int] = mapped_column(  # 회사 FK
        BigInteger,  # 타입
        ForeignKey("users.id", ondelete="CASCADE"),  # FK
        nullable=False,  # 필수
    )

    status: Mapped[ApplicationStatus] = mapped_column(  # 지원 상태
        SAEnum(  # Enum 타입
            ApplicationStatus,  # Enum 클래스
            name="application_status",  # Enum 이름
            native_enum=True,  # DB Enum 사용
        ),
        nullable=False,  # 필수
        default=ApplicationStatus.REQUESTED,  # 기본값
    )

    created_at: Mapped[DateTime] = mapped_column(  # 생성 시각
        DateTime(timezone=True),  # 타임존 포함
        server_default=func.now(),  # 서버 기본값
        nullable=False,  # 필수
    )

    responded_at: Mapped[DateTime | None] = mapped_column(  # 응답 시각
        DateTime(timezone=True),  # 타임존 포함
        nullable=True,  # 선택
    )

    __table_args__ = (  # 테이블 제약
        UniqueConstraint(  # 유니크 제약
            "job_post_id",  # 공고 기준
            "student_id",  # 학생 기준
            name="uq_application_job_student",  # 제약 이름
        ),
    )

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="applications")  # 공고 역참조
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])  # 학생 역참조
    company: Mapped["User"] = relationship("User", foreign_keys=[company_id])  # 회사 역참조

    chat_room: Mapped[Optional["ChatRoom"]] = relationship(  # 지원-채팅방 1:1
        "ChatRoom",  # 대상 모델
        back_populates="application",  # 역참조
        uselist=False,  # 1:1
        cascade="all, delete-orphan",  # 연쇄 삭제
    )


class ChatRoom(Base):  # 채팅방 모델
    __tablename__ = "chat_rooms"  # 테이블명

    __table_args__ = (  # 테이블 제약
        UniqueConstraint("application_id", name="uq_chat_room_application"),  # 지원과 1:1
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # PK

    application_id: Mapped[int] = mapped_column(  # 지원 FK (필수)
        BigInteger,  # 타입
        ForeignKey("applications.id", ondelete="CASCADE"),  # FK
        nullable=False,  # 필수
        unique=True,  # 1:1 보장
    )

    job_post_id: Mapped[int] = mapped_column(  # 공고 FK
        BigInteger,  # 타입
        ForeignKey("job_posts.id", ondelete="CASCADE"),  # FK
        nullable=False,  # 필수
    )

    company_id: Mapped[int] = mapped_column(  # 회사 FK
        BigInteger,  # 타입
        ForeignKey("users.id", ondelete="RESTRICT"),  # FK
        nullable=False,  # 필수
    )

    student_id: Mapped[int] = mapped_column(  # 학생 FK
        BigInteger,  # 타입
        ForeignKey("users.id", ondelete="RESTRICT"),  # FK
        nullable=False,  # 필수
    )

    last_message_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)  # 마지막 메시지 시각
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 생성 시각

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="chat_rooms")  # 공고 역참조

    application: Mapped["Application"] = relationship(  # 지원 역참조
        "Application",  # 대상 모델
        back_populates="chat_room",  # 역참조
    )

    messages: Mapped[List["ChatMessage"]] = relationship(  # 메시지 목록
        "ChatMessage", back_populates="chat_room", cascade="all, delete-orphan"  # 연쇄 삭제
    )
    read_statuses: Mapped[List["ChatReadStatus"]] = relationship(  # 읽음 상태 목록
        "ChatReadStatus", back_populates="chat_room", cascade="all, delete-orphan"  # 연쇄 삭제
    )


class ChatMessage(Base):  # 채팅 메시지 모델
    __tablename__ = "chat_messages"  # 테이블명

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)  # PK
    chat_room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)  # 방 FK
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)  # 발신자 FK

    content: Mapped[str] = mapped_column(Text, nullable=False)  # 메시지 본문
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 생성 시각

    chat_room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")  # 방 역참조
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")  # 발신자 역참조


class ChatReadStatus(Base):  # 채팅 읽음 상태 모델
    __tablename__ = "chat_read_status"  # 테이블명

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)  # 사용자 PK
    chat_room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True)  # 방 PK

    last_read_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)  # 마지막 읽음 시각

    chat_room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="read_statuses")  # 방 역참조
