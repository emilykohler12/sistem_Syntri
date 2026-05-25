from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# DTOs de usuarios
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# DTOs de mensajes
class MessageCreate(BaseModel):
    content: str
    destinations: List[str]

class DeliveryResponse(BaseModel):
    service: str
    status: str
    provider_response: Optional[str]

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    deliveries: List[DeliveryResponse]

    class Config:
        from_attributes = True