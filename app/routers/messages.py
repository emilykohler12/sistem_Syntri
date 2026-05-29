from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Query
from app.database import get_db
from app import schemas
from app.auth import get_current_user
from app.services.message_service import MessageService
from app import models

router = APIRouter(prefix="/api/v1/messages", tags=["Mensajes"])


@router.post("/", response_model=schemas.MessageResponse, status_code=201)
def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Envía un mensaje a múltiples plataformas"""
    return MessageService(db).send(
        content=message_data.content,
        destinations=message_data.destinations,
        current_user=current_user
    )


@router.get("/", response_model=list)
def get_my_messages(
    status: Optional[str] = Query(None, description="Filtrar por estado: success, pending, failed"),
    service: Optional[str] = Query(None, description="Filtrar por servicio: slack, discord"),
    from_date: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Usuario: lista sus propios mensajes con filtros"""
    return MessageService(db).get_user_messages(
        current_user.id, status, service, from_date, to_date
    )