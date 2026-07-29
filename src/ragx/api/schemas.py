"""Wire contracts for the API boundary.

  Request models validate what enters; response models are allowlists for
  what leaves — ORM objects never serialize directly (that is how password
  hashes leak)."""

import uuid
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterRequest(BaseModel):
    tenant_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    is_active: bool

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)

class ApiKeyResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)

      id: uuid.UUID
      name: str
      key_prefix: str
      is_active: bool

class ApiKeyCreatedResponse(ApiKeyResponse):
      api_key: str