from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from app.database import get_db
from app import models
from app.auth import require_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


# ── Helper interno ────────────────────────────────────────────────────────────

def _get_global_limit(db: Session) -> int:
    config = db.query(models.Config).filter(models.Config.id == 1).first()
    return config.daily_message_limit if config else 100

def _effective_limit(user: models.User, db: Session) -> int:
    """Devuelve el límite que aplica al usuario: personalizado o global."""
    return user.daily_limit if user.daily_limit is not None else _get_global_limit(db)


# ── Mensajes ──────────────────────────────────────────────────────────────────

@router.get("/messages")
def get_all_messages(
    status: Optional[str] = Query(None, description="Filtrar por estado: success, pending, failed"),
    service: Optional[str] = Query(None, description="Filtrar por servicio: slack, discord"),
    from_date: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: lista todos los mensajes de todos los usuarios con filtros"""
    logger.info(f"Admin '{current_user.username}' consultando todos los mensajes")

    query = db.query(models.Message)
    if from_date:
        query = query.filter(models.Message.created_at >= from_date)
    if to_date:
        query = query.filter(models.Message.created_at <= to_date)
    if service or status:
        query = query.join(models.MessageDelivery)
        if service:
            query = query.filter(models.MessageDelivery.service == service)
        if status:
            query = query.filter(models.MessageDelivery.status == status)

    messages = query.all()
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "user": msg.user.username,
            "content": msg.content,
            "created_at": msg.created_at,
            "deliveries": [
                {"service": d.service, "status": d.status, "provider_response": d.provider_response}
                for d in msg.deliveries
            ]
        })

    logger.info(f"Admin '{current_user.username}' obtuvo {len(result)} mensajes")
    return result


# ── Métricas ──────────────────────────────────────────────────────────────────

@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: métricas por usuario usando límites reales (sin hardcodeo)"""
    logger.info(f"Admin '{current_user.username}' consultando métricas")

    users = db.query(models.User).all()
    today = date.today()

    metrics = []
    for user in users:
        limit = _effective_limit(user, db)

        total_messages = db.query(func.count(models.Message.id)).filter(
            models.Message.user_id == user.id
        ).scalar()

        usage = db.query(models.DailyUsage).filter(
            models.DailyUsage.user_id == user.id,
            models.DailyUsage.usage_date == today
        ).first()
        messages_today = usage.message_count if usage else 0

        metrics.append({
            "user_id": user.id,
            "username": user.username,
            "role": user.role_name,
            "daily_limit": limit,
            "total_messages": total_messages,
            "messages_today": messages_today,
            "remaining_today": max(0, limit - messages_today)
        })

    logger.info(f"Admin '{current_user.username}' obtuvo métricas de {len(metrics)} usuarios")
    return metrics


# ── Promoción ─────────────────────────────────────────────────────────────────

@router.post("/users/promote")
def promote_user_to_admin(
    username: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: promueve un usuario existente al rol de admin"""
    logger.info(f"Admin '{current_user.username}' intenta promover al usuario '{username}'")

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"El usuario '{username}' no existe")
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El usuario '{username}' ya es admin")

    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    user.role_id = admin_role.id
    db.commit()
    db.refresh(user)

    logger.info(f"Promoción exitosa → '{username}' ahora es admin | Realizado por: '{current_user.username}'")
    return {"message": f"El usuario '{username}' fue promovido a admin exitosamente", "user_id": user.id, "username": user.username, "role": user.role_name}


# ── Roles ─────────────────────────────────────────────────────────────────────

@router.get("/roles")
def list_roles(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Admin: lista todos los roles existentes"""
    roles = db.query(models.Role).all()
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(
    name: str,
    description: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: crea un nuevo rol"""
    if db.query(models.Role).filter(models.Role.name == name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"El rol '{name}' ya existe")
    new_role = models.Role(name=name, description=description)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    logger.info(f"Rol '{name}' creado por admin '{current_user.username}'")
    return {"id": new_role.id, "name": new_role.name, "description": new_role.description}


@router.delete("/roles/{role_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: elimina un rol por nombre (no se pueden eliminar 'user' ni 'admin')"""
    if role_name in ("user", "admin"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Los roles 'user' y 'admin' no se pueden eliminar")
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"El rol '{role_name}' no existe")
    users_with_role = db.query(models.User).filter(models.User.role_id == role.id).count()
    if users_with_role:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"No se puede eliminar: {users_with_role} usuario/s tienen este rol")
    logger.info(f"Admin '{current_user.username}' eliminó el rol '{role_name}'")
    db.delete(role)
    db.commit()


# ── Límites ───────────────────────────────────────────────────────────────────

@router.get("/limits")
def get_limits(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Admin: muestra el límite global y los límites personalizados por usuario"""
    global_limit = _get_global_limit(db)
    users = db.query(models.User).all()
    return {
        "global_limit": global_limit,
        "users": [
            {
                "user_id": u.id,
                "username": u.username,
                "custom_limit": u.daily_limit,
                "effective_limit": _effective_limit(u, db)
            }
            for u in users
        ]
    }


@router.patch("/limits/global")
def update_global_limit(
    new_limit: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: cambia el límite diario global para todos los usuarios sin límite personalizado"""
    if new_limit < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El límite debe ser mayor a 0")

    config = db.query(models.Config).filter(models.Config.id == 1).first()
    old_limit = config.daily_message_limit

    config.daily_message_limit = new_limit

    audit = models.LimitAudit(
        changed_by=current_user.id,
        target_user_id=None,
        old_limit=old_limit,
        new_limit=new_limit
    )
    db.add(audit)
    db.commit()

    logger.info(f"Admin '{current_user.username}' cambió límite global: {old_limit} → {new_limit}")
    return {"message": f"Límite global actualizado a {new_limit}", "old_limit": old_limit, "new_limit": new_limit}


@router.patch("/limits/user/{username}")
def update_user_limit(
    username: str,
    new_limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: cambia el límite diario de un usuario específico. Enviar null para volver al global."""
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"El usuario '{username}' no existe")
    if new_limit is not None and new_limit < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El límite debe ser mayor a 0")

    old_limit = _effective_limit(user, db)
    user.daily_limit = new_limit
    effective = _effective_limit(user, db)

    audit = models.LimitAudit(
        changed_by=current_user.id,
        target_user_id=user.id,
        old_limit=old_limit,
        new_limit=effective
    )
    db.add(audit)
    db.commit()

    msg = f"Límite de '{username}' actualizado a {new_limit}" if new_limit else f"Límite de '{username}' vuelto al global ({effective})"
    logger.info(f"Admin '{current_user.username}': {msg}")
    return {"message": msg, "username": username, "effective_limit": effective}


@router.get("/limits/audit")
def get_audit(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    """Admin: historial de cambios de límites"""
    records = db.query(models.LimitAudit).order_by(models.LimitAudit.changed_at.desc()).all()
    result = []
    for r in records:
        admin = db.query(models.User).filter(models.User.id == r.changed_by).first()
        target = db.query(models.User).filter(models.User.id == r.target_user_id).first() if r.target_user_id else None
        result.append({
            "changed_by": admin.username if admin else r.changed_by,
            "target": target.username if target else "global",
            "old_limit": r.old_limit,
            "new_limit": r.new_limit,
            "changed_at": r.changed_at
        })
    return result