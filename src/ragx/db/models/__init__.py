"""All model modules must be imported here: importing this package is what
registers every table on Base.metadata (Alembic autogenerate reads that)."""

from ragx.db.models.identity import ApiKey, Tenant, User
from ragx.db.models.knowledge import KnowledgeBase

__all__ = ["ApiKey", "Document", "KnowledgeBase", "Tenant", "User"]
