"""chunk text search (fts)

Revision ID: d188f1bb880d
Revises: eacb14f349d3
Create Date: 2026-08-05 11:40:51.312534

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d188f1bb880d"
down_revision: str | Sequence[str] | None = "eacb14f349d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE chunks ADD COLUMN text_search tsvector "
        "GENERATED ALWAYS AS (to_tsvector('english', text)) STORED"
    )
    op.create_index("ix_chunks_text_search", "chunks", ["text_search"], postgresql_using="gin")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_chunks_text_search", table_name="chunks")
    op.drop_column("chunks", "text_search")
