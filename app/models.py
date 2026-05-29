from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)

    users = relationship("User", back_populates="role_rel")


@event.listens_for(Role.__table__, "after_create")
def seed_roles(target, connection, **kwargs):
    connection.execute(
        target.insert(),
        [
            {"name": "user",  "description": "Usuario estándar"},
            {"name": "admin", "description": "Administrador con acceso total"},
        ],
    )


class Config(Base):
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, default=1)
    daily_message_limit = Column(Integer, nullable=False, default=100)


@event.listens_for(Config.__table__, "after_create")
def seed_config(target, connection, **kwargs):
    connection.execute(target.insert(), [{"id": 1, "daily_message_limit": 100}])


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    daily_limit = Column(Integer, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())

    role_rel = relationship("Role", back_populates="users")
    messages = relationship("Message", back_populates="user")
    daily_usage = relationship("DailyUsage", back_populates="user")

    @property
    def role_name(self) -> str:
        return self.role_rel.name if self.role_rel else "user"

    def has_role(self, *role_names: str) -> bool:
        return self.role_name in role_names

    @property
    def is_admin(self) -> bool:
        return self.has_role("admin")


class DailyUsage(Base):
    __tablename__ = "daily_usage"
    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", name="uq_daily_usage_user_date"),
        Index("ix_daily_usage_user_date", "user_id", "usage_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usage_date = Column(Date, nullable=False)
    message_count = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="daily_usage")


class LimitAudit(Base):
    __tablename__ = "limit_audit"

    id = Column(Integer, primary_key=True, index=True)
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    old_limit = Column(Integer, nullable=False)
    new_limit = Column(Integer, nullable=False)
    changed_at = Column(DateTime, server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_user_id", "user_id"),
        Index("ix_messages_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="messages")
    deliveries = relationship("MessageDelivery", back_populates="message")


class MessageDelivery(Base):
    __tablename__ = "message_deliveries"
    __table_args__ = (
        Index("ix_deliveries_message_id", "message_id"),
        Index("ix_deliveries_status", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    service = Column(String, nullable=False)
    status = Column(String, default="pending")
    provider_response = Column(Text)
    attempt = Column(Integer, nullable=False, default=1)  # número de intento (1, 2, 3)

    message = relationship("Message", back_populates="deliveries")