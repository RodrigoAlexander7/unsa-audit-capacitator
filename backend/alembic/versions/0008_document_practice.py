"""document practice reference columns

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-11 19:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0008"
down_revision: str | Sequence[str] | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("modules", sa.Column("reference_title", sa.String(length=200), nullable=True))
    op.add_column("modules", sa.Column("reference_md", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("modules", "reference_md")
    op.drop_column("modules", "reference_title")
