from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app import models
import logging

logger = logging.getLogger(__name__)


class AdminService:
    """Lógica de negocio del panel de administración."""

    def __init__(self, db: Session):
        self.db = db
        self.msg_repo = MessageRepository(db)
        self.user_repo = UserRepository(db)

    def _effective_limit(self, user: models.User) -> int:
        if user.daily_limit is not None:
            return user.daily_limit
        config = self.msg_repo.get_config()
        return config.daily_message_limit if config else 100

    # ── Mensajes ──────────────────────────────────────────────────────────────

    def get_all_messages(self, status, service, from_date, to_date) -> list:
        messages = self.msg_repo.get_all_messages(status, service, from_date, to_date)
        return [
            {
                "id": m.id, "user": m.user.username, "content": m.content,
                "created_at": m.created_at,
                "deliveries": [
                    {"service": d.service, "status": d.status,
                     "provider_response": d.provider_response}
                    for d in m.deliveries
                ]
            }
            for m in messages
        ]

    # ── Métricas ──────────────────────────────────────────────────────────────

    def get_metrics(self) -> list:
        users = self.user_repo.get_all()
        today = date.today()
        result = []
        for user in users:
            limit = self._effective_limit(user)
            usage = self.msg_repo.get_daily_usage(user.id, today)
            messages_today = usage.message_count if usage else 0
            result.append({
                "user_id": user.id, "username": user.username,
                "role": user.role_name, "is_active": bool(user.is_active),
                "daily_limit": limit,
                "total_messages": self.msg_repo.count_messages_by_user(user.id),
                "messages_today": messages_today,
                "remaining_today": max(0, limit - messages_today),
                "deliveries": {
                    "total": self.msg_repo.count_deliveries_by_user(user.id),
                    "successful": self.msg_repo.count_deliveries_by_user(user.id, "success"),
                    "failed": self.msg_repo.count_deliveries_by_user(user.id, "failed"),
                }
            })
        return result

    def get_daily_metrics(self, from_date, to_date) -> list:
        rows = self.msg_repo.get_daily_stats(from_date, to_date)
        return [
            {
                "dia": str(row.dia),
                "total_mensajes": row.total_mensajes,
                "deliveries_exitosas": self.msg_repo.count_deliveries_by_date_and_status(row.dia, "success"),
                "deliveries_fallidas": self.msg_repo.count_deliveries_by_date_and_status(row.dia, "failed"),
            }
            for row in rows
        ]

    # ── Usuarios ──────────────────────────────────────────────────────────────

    def promote_to_admin(self, username: str, admin: models.User) -> dict:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"El usuario '{username}' no existe")
        if user.is_admin:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"'{username}' ya es admin")
        admin_role = self.user_repo.get_role_by_name("admin")
        user.role_id = admin_role.id
        self.user_repo.update(user)
        logger.info(f"'{username}' promovido por '{admin.username}'")
        return {"message": f"'{username}' promovido a admin", "username": username, "role": user.role_name}

    def cancel_user(self, username: str, admin: models.User) -> dict:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"El usuario '{username}' no existe")
        if username == admin.username:
            raise HTTPException(status_code=400, detail="No podés cancelar tu propia cuenta")
        if not user.is_active:
            raise HTTPException(status_code=409, detail=f"'{username}' ya está cancelado")
        user.is_active = 0
        self.user_repo.update(user)
        logger.info(f"'{username}' cancelado por '{admin.username}'")
        return {"message": f"'{username}' cancelado", "username": username, "is_active": False}

    def reactivate_user(self, username: str, admin: models.User) -> dict:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"El usuario '{username}' no existe")
        if user.is_active:
            raise HTTPException(status_code=409, detail=f"'{username}' ya está activo")
        user.is_active = 1
        self.user_repo.update(user)
        logger.info(f"'{username}' reactivado por '{admin.username}'")
        return {"message": f"'{username}' reactivado", "username": username, "is_active": True}

    # ── Roles ─────────────────────────────────────────────────────────────────

    def list_roles(self) -> list:
        return [{"id": r.id, "name": r.name, "description": r.description}
                for r in self.user_repo.get_all_roles()]

    def create_role(self, name: str, description: str | None, admin: models.User) -> dict:
        if self.user_repo.get_role_by_name(name):
            raise HTTPException(status_code=409, detail=f"El rol '{name}' ya existe")
        role = self.user_repo.create_role(name, description)
        logger.info(f"Rol '{name}' creado por '{admin.username}'")
        return {"id": role.id, "name": role.name, "description": role.description}

    def delete_role(self, role_name: str, admin: models.User) -> None:
        if role_name in ("user", "admin"):
            raise HTTPException(status_code=400, detail="Los roles 'user' y 'admin' no se pueden eliminar")
        role = self.user_repo.get_role_by_name(role_name)
        if not role:
            raise HTTPException(status_code=404, detail=f"El rol '{role_name}' no existe")
        if self.user_repo.count_users_with_role(role.id):
            raise HTTPException(status_code=409, detail="No se puede eliminar: hay usuarios con este rol")
        self.user_repo.delete_role(role)
        logger.info(f"Rol '{role_name}' eliminado por '{admin.username}'")

    # ── Límites ───────────────────────────────────────────────────────────────

    def get_limits(self) -> dict:
        global_limit = self.msg_repo.get_config().daily_message_limit
        users = self.user_repo.get_all()
        return {
            "global_limit": global_limit,
            "users": [
                {"user_id": u.id, "username": u.username,
                 "custom_limit": u.daily_limit,
                 "effective_limit": self._effective_limit(u)}
                for u in users
            ]
        }

    def update_global_limit(self, new_limit: int, admin: models.User) -> dict:
        if new_limit < 1:
            raise HTTPException(status_code=400, detail="El límite debe ser mayor a 0")
        config = self.msg_repo.get_config()
        old_limit = config.daily_message_limit
        config.daily_message_limit = new_limit
        self.msg_repo.update_config(config)
        self.msg_repo.create_audit(admin.id, None, old_limit, new_limit)
        logger.info(f"Límite global: {old_limit} → {new_limit} por '{admin.username}'")
        return {"message": f"Límite global actualizado a {new_limit}", "old_limit": old_limit, "new_limit": new_limit}

    def update_user_limit(self, username: str, new_limit: int | None, admin: models.User) -> dict:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise HTTPException(status_code=404, detail=f"El usuario '{username}' no existe")
        if new_limit is not None and new_limit < 1:
            raise HTTPException(status_code=400, detail="El límite debe ser mayor a 0")
        old_limit = self._effective_limit(user)
        user.daily_limit = new_limit
        self.user_repo.update(user)
        effective = self._effective_limit(user)
        self.msg_repo.create_audit(admin.id, user.id, old_limit, effective)
        msg = f"Límite de '{username}' actualizado a {new_limit}" if new_limit else f"'{username}' vuelve al límite global ({effective})"
        return {"message": msg, "username": username, "effective_limit": effective}

    def get_audit(self) -> list:
        records = self.msg_repo.get_all_audits()
        result = []
        for r in records:
            admin = self.user_repo.get_by_id(r.changed_by)
            target = self.user_repo.get_by_id(r.target_user_id) if r.target_user_id else None
            result.append({
                "changed_by": admin.username if admin else r.changed_by,
                "target": target.username if target else "global",
                "old_limit": r.old_limit, "new_limit": r.new_limit,
                "changed_at": r.changed_at
            })
        return result