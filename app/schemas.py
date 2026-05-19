from pydantic import BaseModel
from typing import Optional

# DTO de entrada para registro y login
class UserCreate(BaseModel):
    username: str
    password: str

# DTO de salida cuando se devuelve un usuario
# Nunca incluimos el password en la respuesta
class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True

# DTO de salida para el login
class Token(BaseModel):
    access_token: str
    token_type: str