"""Knowledge bases: tenant-scoped corpora and the per-corpus policy that
must be uniform within them (chunking, embedding model)."""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from uuid_utils.compat import uuid7

from ragx.db.base import Base, TimestampMixin


class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"
    __table_args__ = (UniqueConstraint("tenant_id", "name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(2000), default="")
    chunk_size: Mapped[int] = mapped_column(default=1000)
    chunk_overlap: Mapped[int] = mapped_column(default=200)
    embedding_model: Mapped[str] = mapped_column(
        String(255), default="openai/text-embedding-3-small"
    )
