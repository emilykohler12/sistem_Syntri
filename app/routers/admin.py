from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user, require_admin
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

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
                {
                    "service": d.service,
                    "status": d.status,
                    "provider_response": d.provider_response
                }
                for d in msg.deliveries
            ]
        })

    logger.info(f"Admin '{current_user.username}' obtuvo {len(result)} mensajes")
    return result


@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: métricas por usuario - total de mensajes y mensajes restantes hoy"""

    logger.info(f"Admin '{current_user.username}' consultando métricas")

    users = db.query(models.User).all()
    today = date.today()
    DAILY_LIMIT = 100

    metrics = []
    for user in users:
        total_messages = db.query(func.count(models.Message.id)).filter(
            models.Message.user_id == user.id
        ).scalar()

        messages_today = db.query(func.count(models.Message.id)).filter(
            models.Message.user_id == user.id,
            func.date(models.Message.created_at) == today
        ).scalar()

        remaining_today = max(0, DAILY_LIMIT - messages_today)

        metrics.append({
            "user_id": user.id,
            "username": user.username,
            "role": user.role_name,          # ← antes era user.role (string legacy)
            "total_messages": total_messages,
            "messages_today": messages_today,
            "remaining_today": remaining_today
        })

    logger.info(f"Admin '{current_user.username}' obtuvo métricas de {len(metrics)} usuarios")
    return metrics


@router.post("/users/promote")
def promote_user_to_admin(
    username: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """Admin: promueve un usuario existente al rol de admin"""

    logger.info(f"Admin '{current_user.username}' intenta promover al usuario '{username}'")

    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        logger.warning(f"Promoción fallida → El usuario '{username}' no existe")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El usuario '{username}' no existe"
        )

    if user.is_admin:
        logger.warning(f"Promoción innecesaria → '{username}' ya es admin")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{username}' ya es admin"
        )

    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    user.role_id = admin_role.id
    db.commit()
    db.refresh(user)

    logger.info(f"Promoción exitosa → '{username}' ahora es admin | Realizado por: '{current_user.username}'")

    return {
        "message": f"El usuario '{username}' fue promovido a admin exitosamente",
        "user_id": user.id,
        "username": user.username,
        "role": user.role_name
    }


# ── Gestión de roles (nuevo) ──────────────────────────────────────────────────

@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
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

    logger.info(f"Admin '{current_user.username}' intenta crear el rol '{name}'")

    if db.query(models.Role).filter(models.Role.name == name).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El rol '{name}' ya existe"
        )

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los roles 'user' y 'admin' no se pueden eliminar"
        )

    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"El rol '{role_name}' no existe")

    users_with_role = db.query(models.User).filter(models.User.role_id == role.id).count()
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No se puede eliminar: {users_with_role} usuario/s tienen este rol"
        )

    logger.info(f"Admin '{current_user.username}' eliminó el rol '{role_name}'")
    db.delete(role)
    db.commit()