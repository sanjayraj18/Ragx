"""baseline

Revision ID: 2a44bd2a5b75
Revises:
Create Date: 2026-07-28 22:59:17.907608

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "2a44bd2a5b75"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
