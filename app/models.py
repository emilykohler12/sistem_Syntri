from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)          # "user", "admin", etc.
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="role_rel")


# Seed de roles base después de crear la tabla
@event.listens_for(Role.__table__, "after_create")
def seed_roles(target, connection, **kwargs):
    connection.execute(
        target.insert(),
        [
            {"name": "user",  "description": "Usuario estándar"},
            {"name": "admin", "description": "Administrador con acceso total"},
        ],
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

    # FK al nuevo sistema de roles (nullable durante migración)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    role_rel = relationship("Role", back_populates="users")
    messages = relationship("Message", back_populates="user")

    # ── Helpers de permisos ──────────────────────────────────────────────────
    @property
    def role_name(self) -> str:
        """Nombre del rol como string; compatible con código existente."""
        return self.role_rel.name if self.role_rel else "user"

    def has_role(self, *role_names: str) -> bool:
        """Comprueba si el usuario posee alguno de los roles indicados."""
        return self.role_name in role_names

    @property
    def is_admin(self) -> bool:
        return self.has_role("admin")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="messages")
    deliveries = relationship("MessageDelivery", back_populates="message")


class MessageDelivery(Base):
    __tablename__ = "message_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    service = Column(String, nullable=False)
    status = Column(String, default="pending")
    provider_response = Column(Text)

    message = relationship("Message", back_populates="deliveries")