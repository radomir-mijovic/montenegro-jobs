"""enable pg_trgm extension

Revision ID: a8f4e2b19c3d
Revises: 27cead27bfc4
Create Date: 2026-01-29 08:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a8f4e2b19c3d'
down_revision: Union[str, Sequence[str], None] = '27cead27bfc4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Enable pg_trgm extension for fuzzy text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    """Downgrade schema."""
    # Drop pg_trgm extension
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
