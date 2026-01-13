"""add applications and link chat_room

Revision ID: a2acedeedd03
Revises:
Create Date: 2026-01-13 15:31:05.232181
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2acedeedd03"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. applications 테이블 생성
    op.create_table(
        "applications",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_post_id", sa.BigInteger(), nullable=False),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "REQUESTED",
                "ACCEPTED",
                "REJECTED",
                name="application_status",
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["job_post_id"], ["job_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "job_post_id",
            "student_id",
            name="uq_application_job_student",
        ),
    )

    # 2. chat_rooms에 application_id 추가
    op.add_column(
        "chat_rooms",
        sa.Column("application_id", sa.BigInteger(), nullable=False),
    )

    # 3. Application 1 : 1 ChatRoom 강제
    op.create_unique_constraint(
        "uq_chat_room_application",
        "chat_rooms",
        ["application_id"],
    )

    op.create_foreign_key(
        "fk_chat_rooms_application",
        "chat_rooms",
        "applications",
        ["application_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    # 1. FK / UNIQUE 제거
    op.drop_constraint(
        "fk_chat_rooms_application",
        "chat_rooms",
        type_="foreignkey",
    )
    op.drop_constraint(
        "uq_chat_room_application",
        "chat_rooms",
        type_="unique",
    )

    # 2. 컬럼 제거
    op.drop_column("chat_rooms", "application_id")

    # 3. applications 테이블 제거
    op.drop_table("applications")
