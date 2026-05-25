from fastapi import APIRouter, Depends, Query
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
            "role": user.role,
            "total_messages": total_messages,
            "messages_today": messages_today,
            "remaining_today": remaining_today
        })
    
    logger.info(f"Admin '{current_user.username}' obtuvo métricas de {len(metrics)} usuarios")
    return metrics