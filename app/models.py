from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .database import Base


class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    COMPANY = "COMPANY"
    ADMIN = "ADMIN"


class JobPostStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class ApplicationStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=True),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile", back_populates="user", uselist=False
    )

    job_posts: Mapped[List["JobPost"]] = relationship("JobPost", back_populates="company")
    sent_messages: Mapped[List["ChatMessage"]] = relationship("ChatMessage", back_populates="sender")


    student_applications: Mapped[List["Application"]] = relationship(
        "Application", foreign_keys="Application.student_id", back_populates="student"
    )
    company_applications: Mapped[List["Application"]] = relationship(
        "Application", foreign_keys="Application.company_id", back_populates="company"
    )


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    school: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    major: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    skills: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)  # 실제 DB는 JSONB [] 권장
    available_time: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="student_profile")


class JobPost(Base):
    __tablename__ = "job_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    wage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[JobPostStatus] = mapped_column(
        SAEnum(JobPostStatus, name="job_post_status", native_enum=True),
        nullable=False,
        server_default="OPEN",
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["User"] = relationship("User", back_populates="job_posts")
    images: Mapped[List["JobPostImage"]] = relationship(
        "JobPostImage", back_populates="job_post", cascade="all, delete-orphan"
    )

    # ChatRoom은 이제 Application 기반으로 생성되지만, job_post 기준 조회는 여전히 유용
    chat_rooms: Mapped[List["ChatRoom"]] = relationship("ChatRoom", back_populates="job_post")

    # (선택) 공고 기준으로 applications를 보고 싶으면 사용
    applications: Mapped[List["Application"]] = relationship("Application", back_populates="job_post")


class JobPostImage(Base):
    __tablename__ = "job_post_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False)

    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="images")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    job_post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        SAEnum(
            ApplicationStatus,
            name="application_status",
            native_enum=True,
        ),
        nullable=False,
        default=ApplicationStatus.REQUESTED,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    responded_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "job_post_id",
            "student_id",
            name="uq_application_job_student",
        ),
    )

    # relationships
    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="applications")
    student: Mapped["User"] = relationship("User", foreign_keys=[student_id])
    company: Mapped["User"] = relationship("User", foreign_keys=[company_id])

    # Application 1 : 1 ChatRoom (ACCEPTED일 때만 생성된다는 규칙은 서비스 로직이 담당)
    chat_room: Mapped[Optional["ChatRoom"]] = relationship(
        "ChatRoom",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    # ✅ 핵심: ChatRoom은 Application 기반으로만 존재해야 한다.
    # application_id UNIQUE로 1:1을 DB 레벨에서 강제한다.
    __table_args__ = (
        UniqueConstraint("application_id", name="uq_chat_room_application"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    application_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    job_post_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("job_posts.id", ondelete="CASCADE"),
        nullable=False,
    )

    company_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    last_message_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="chat_rooms")

    application: Mapped["Application"] = relationship(
        "Application",
        back_populates="chat_room",
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="chat_room", cascade="all, delete-orphan"
    )
    read_statuses: Mapped[List["ChatReadStatus"]] = relationship(
        "ChatReadStatus", back_populates="chat_room", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    chat_room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat_room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="messages")
    sender: Mapped["User"] = relationship("User", back_populates="sent_messages")


class ChatReadStatus(Base):
    __tablename__ = "chat_read_status"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("chat_rooms.id", ondelete="CASCADE"), primary_key=True)

    last_read_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    chat_room: Mapped["ChatRoom"] = relationship("ChatRoom", back_populates="read_statuses")
