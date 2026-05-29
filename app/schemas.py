from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None


# ── Usuarios ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: Optional[RoleResponse] = None

    # Alias para que FastAPI mapee role_rel → role
    @classmethod
    def from_orm_user(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            role=RoleResponse.model_validate(user.role_rel) if user.role_rel else None
        )

class Token(BaseModel):
    access_token: str
    token_type: str


# ── Mensajes ──────────────────────────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str
    destinations: List[str]

class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service: str
    status: str
    provider_response: Optional[str] = None
    attempt: int = 1

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime
    deliveries: List[DeliveryResponse]