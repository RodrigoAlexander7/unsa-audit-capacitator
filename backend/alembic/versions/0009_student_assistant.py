"""student assistant messages

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-11 20:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: str | Sequence[str] | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=True),
        sa.Column("route_path", sa.String(length=200), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_assistant_messages_created_at"),
        "assistant_messages",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assistant_messages_role"), "assistant_messages", ["role"], unique=False
    )
    op.create_index(
        op.f("ix_assistant_messages_user_id"), "assistant_messages", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_assistant_messages_user_id"), table_name="assistant_messages")
    op.drop_index(op.f("ix_assistant_messages_role"), table_name="assistant_messages")
    op.drop_index(op.f("ix_assistant_messages_created_at"), table_name="assistant_messages")
    op.drop_table("assistant_messages")
