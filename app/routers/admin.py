from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query
from app.database import get_db
from app.auth import require_admin
from app.services.admin_service import AdminService
from app import models

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# ── Mensajes ──────────────────────────────────────────────────────────────────

@router.get("/messages")
def get_all_messages(
    status: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Admin: lista todos los mensajes con filtros"""
    return AdminService(db).get_all_messages(status, service, from_date, to_date)


# ── Métricas ──────────────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: métricas por usuario"""
    return AdminService(db).get_metrics()


@router.get("/metrics/daily")
def get_daily_metrics(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    """Admin: métricas diarias"""
    return AdminService(db).get_daily_metrics(from_date, to_date)


# ── Usuarios ──────────────────────────────────────────────────────────────────

@router.post("/users/promote")
def promote_user_to_admin(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: promueve un usuario a admin"""
    return AdminService(db).promote_to_admin(username, current_user)


@router.patch("/users/{username}/cancel")
def cancel_user(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: cancela un usuario"""
    return AdminService(db).cancel_user(username, current_user)


@router.patch("/users/{username}/reactivate")
def reactivate_user(username: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: reactiva un usuario cancelado"""
    return AdminService(db).reactivate_user(username, current_user)


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: lista todos los roles"""
    return AdminService(db).list_roles()


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(name: str, description: Optional[str] = None, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: crea un nuevo rol"""
    return AdminService(db).create_role(name, description, current_user)


@router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_name: str, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: elimina un rol por nombre"""
    return AdminService(db).delete_role(role_name, current_user)


# ── Límites ───────────────────────────────────────────────────────────────────

@router.get("/limits")
def get_limits(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: ve límites globales y por usuario"""
    return AdminService(db).get_limits()


@router.patch("/limits/global")
def update_global_limit(new_limit: int, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: cambia el límite global"""
    return AdminService(db).update_global_limit(new_limit, current_user)


@router.patch("/limits/user/{username}")
def update_user_limit(username: str, new_limit: Optional[int] = None, db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: cambia el límite de un usuario específico"""
    return AdminService(db).update_user_limit(username, new_limit, current_user)


@router.get("/limits/audit")
def get_audit(db: Session = Depends(get_db), current_user: models.User = Depends(require_admin)):
    """Admin: historial de cambios de límites"""
    return AdminService(db).get_audit()