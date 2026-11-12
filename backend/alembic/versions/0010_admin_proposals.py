"""admin curriculum restructuring proposals

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-11 20:55:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0010"
down_revision: str | Sequence[str] | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "curriculum_proposals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("target_route_code", sa.String(length=40), nullable=True),
        sa.Column("target_module_slug", sa.String(length=120), nullable=True),
        sa.Column("change_type", sa.String(length=32), nullable=False),
        sa.Column("proposed_change", sa.Text(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column(
            "evidence_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("review_note", sa.Text(), nullable=True),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_curriculum_proposals_created_at"),
        "curriculum_proposals",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_curriculum_proposals_status"),
        "curriculum_proposals",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_curriculum_proposals_status"), table_name="curriculum_proposals")
    op.drop_index(op.f("ix_curriculum_proposals_created_at"), table_name="curriculum_proposals")
    op.drop_table("curriculum_proposals")
