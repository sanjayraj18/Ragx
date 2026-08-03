"""Knowledge bases: tenant-scoped corpora and the per-corpus policy that
must be uniform within them (chunking, embedding model)."""

import uuid
from enum import StrEnum

from sqlalchemy import BigInteger, Enum, ForeignKey, String, Text, UniqueConstraint
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


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PARSING = "parsing"
    CHUNKED = "chunked"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("kb_id", "content_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
    kb_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(String(1024))
    content_type: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    content_hash: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False, length=32),
        default=DocumentStatus.PENDING,
    )
    error_message: Mapped[str | None] = mapped_column(String(2000), default=None)

class Chunk(Base, TimestampMixin):
      __tablename__ = "chunks"
      __table_args__ = (UniqueConstraint("document_id", "position"),)

      id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
      tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenants.id"), index=True)
      kb_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("knowledge_bases.id", ondelete="CASCADE"), index=True
      )
      document_id: Mapped[uuid.UUID] = mapped_column(
          ForeignKey("documents.id", ondelete="CASCADE"), index=True
      )
      position: Mapped[int]
      text: Mapped[str] = mapped_column(Text)
      page_start: Mapped[int | None] = mapped_column(default=None)
      page_end: Mapped[int | None] = mapped_column(default=None)