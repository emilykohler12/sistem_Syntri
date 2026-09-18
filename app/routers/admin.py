from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query
from pydantic import BaseModel
from app.database import get_db
from app.auth import require_permission
from app.services.admin_service import AdminService
from app import models

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class UpdateRoleRequest(BaseModel):
    role_name: str


class UpdatePermissionsRequest(BaseModel):
    permissions: list[str]


# ── Mensajes ──────────────────────────────────────────────────────────────────

@router.get("/messages")
def get_all_messages(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(20, ge=1, le=100, description="Resultados por página"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("messages"))
):
    """Admin: lista todos los mensajes con filtros, paginado"""
    return AdminService(db).get_all_messages(status, service, from_date, to_date, page, limit)


# ── Métricas ──────────────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("metrics"))):
    """Admin: métricas por usuario"""
    return AdminService(db).get_metrics()


@router.get("/metrics/daily")
def get_daily_metrics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("metrics"))
):
    """Admin: métricas diarias"""
    return AdminService(db).get_daily_metrics(from_date, to_date)


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.post("/users/promote")
def promote_user_to_admin(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("users"))):
    """Admin: promueve un usuario a admin"""
    return AdminService(db).promote_to_admin(username, current_user)


@router.patch("/users/{username}/role")
def update_user_role(username: str, payload: UpdateRoleRequest, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("users"))):
    """Admin: le asigna a un usuario cualquiera de los roles existentes"""
    return AdminService(db).update_user_role(username, payload.role_name, current_user)


@router.patch("/users/{username}/cancel")
def cancel_user(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("users"))):
    """Admin: cancela un usuario"""
    return AdminService(db).cancel_user(username, current_user)


@router.patch("/users/{username}/reactivate")
def reactivate_user(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("users"))):
    """Admin: reactiva un usuario cancelado"""
    return AdminService(db).reactivate_user(username, current_user)


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/permissions")
def list_permissions(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("roles"))):
    """Admin: lista las capacidades que se le pueden asignar a un rol"""
    return AdminService(db).list_permissions()


@router.get("/roles")
def list_roles(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("roles", "users"))):
    """Admin: lista todos los roles. También la usa la sección de Usuarios para el selector de rol."""
    return AdminService(db).list_roles()


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(name: str, description: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("roles"))):
    """Admin: crea un nuevo rol"""
    return AdminService(db).create_role(name, description, current_user)


@router.patch("/roles/{role_name}/permissions")
def update_role_permissions(role_name: str, payload: UpdatePermissionsRequest, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("roles"))):
    """Admin: define a qué secciones del panel puede acceder un rol"""
    return AdminService(db).update_role_permissions(role_name, payload.permissions, current_user)


@router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_name: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("roles"))):
    """Admin: elimina un rol por nombre"""
    return AdminService(db).delete_role(role_name, current_user)


# ── Límites ───────────────────────────────────────────────────────────────────

@router.get("/limits")
def get_limits(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("limits"))):
    """Admin: ve límites globales y por usuario"""
    return AdminService(db).get_limits()


@router.patch("/limits/global")
def update_global_limit(new_limit: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("limits"))):
    """Admin: cambia el límite global"""
    return AdminService(db).update_global_limit(new_limit, current_user)


@router.patch("/limits/user/{username}")
def update_user_limit(username: str, new_limit: Optional[int] = None, db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("limits"))):
    """Admin: cambia el límite de un usuario específico"""
    return AdminService(db).update_user_limit(username, new_limit, current_user)


@router.get("/limits/audit")
def get_audit(db: Session = Depends(get_db), current_user: models.User = Depends(require_permission("limits"))):
    """Admin: historial de cambios de límites"""
    return AdminService(db).get_audit()
