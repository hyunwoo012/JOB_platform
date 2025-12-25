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
    chat_rooms: Mapped[List["ChatRoom"]] = relationship("ChatRoom", back_populates="job_post")


class JobPostImage(Base):
    __tablename__ = "job_post_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False)

    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="images")


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    __table_args__ = (
        UniqueConstraint("job_post_id", "company_id", "student_id", name="uq_chat_rooms_unique_pair"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_post_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("job_posts.id", ondelete="CASCADE"), nullable=False)

    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    student_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    last_message_at: Mapped[Optional[str]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    job_post: Mapped["JobPost"] = relationship("JobPost", back_populates="chat_rooms")
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
