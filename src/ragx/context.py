"""The tenant context: proof of authentication and the scope of every operation.

  Constructed only by the API layer's auth dependencies — one per request —
  and required by every service that touches tenant data. Code cannot reach
  tenant-scoped data without holding one: that is the isolation chokepoint.
  Exactly one of user_id / api_key_id is set, recording which door was used."""


from dataclasses import dataclass
import uuid


@dataclass(frozen=True, slots=True)
class TenantContext:
    tenant_id : uuid.UUID
    user_id : uuid.UUID | None = None
    api_key_id = uuid.UUID | None = None
