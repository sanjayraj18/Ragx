"""All model modules must be imported here: importing this package is what
  registers every table on Base.metadata (Alembic autogenerate reads that)."""

from ragx.db.models.identity import Tenant, User

__all__ = ["Tenant", "User"]