"""hnsw index on chunk embeddings

Revision ID: eacb14f349d3
Revises: f82662593501
Create Date: 2026-08-05 10:31:58.612709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eacb14f349d3'
down_revision: Union[str, Sequence[str], None] = 'f82662593501'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
      op.execute(
          "CREATE INDEX ix_chunks_embedding_hnsw ON chunks "
          "USING hnsw (embedding vector_cosine_ops) "
          "WITH (m = 16, ef_construction = 64)"
      )


def downgrade() -> None:
      op.execute("DROP INDEX ix_chunks_embedding_hnsw")
