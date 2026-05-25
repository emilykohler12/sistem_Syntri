from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services.slack_service import SlackService
from app.services.discord_service import DiscordService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/messages", tags=["Mensajes"])

AVAILABLE_SERVICES = {
    "slack": SlackService,
    "discord": DiscordService,
}

DAILY_LIMIT = 100

def check_rate_limit(user_id: int, db: Session):
    """Verifica que el usuario no haya superado el límite diario"""
    today = date.today()
    messages_today = db.query(func.count(models.Message.id)).filter(
        models.Message.user_id == user_id,
        func.date(models.Message.created_at) == today
    ).scalar()
    return messages_today

@router.post("/", response_model=schemas.MessageResponse, status_code=201)
def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Envía un mensaje a múltiples plataformas"""
    
    logger.info(f"Pedido de envío → Usuario: {current_user.username} | Destinos: {message_data.destinations}")
    
    # Verificar destinos válidos
    invalid_destinations = [
        d for d in message_data.destinations 
        if d not in AVAILABLE_SERVICES
    ]
    if invalid_destinations:
        logger.warning(f"Destinos inválidos → {invalid_destinations} | Usuario: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Destinos no válidos: {invalid_destinations}. Disponibles: {list(AVAILABLE_SERVICES.keys())}"
        )
    
    # Verificar rate limit
    messages_today = check_rate_limit(current_user.id, db)
    if messages_today >= DAILY_LIMIT:
        logger.warning(f"Límite diario superado → Usuario: {current_user.username} | Mensajes hoy: {messages_today}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite diario de {DAILY_LIMIT} mensajes alcanzado. Volvé mañana."
        )
    
    remaining = DAILY_LIMIT - messages_today - 1
    logger.info(f"Rate limit → Usuario: {current_user.username} | Mensajes restantes hoy: {remaining}")
    
    # Guardar el mensaje en la base de datos
    new_message = models.Message(
        user_id=current_user.id,
        content=message_data.content,
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    
    logger.info(f"Mensaje guardado en base de datos → ID: {new_message.id} | Usuario: {current_user.username}")
    
    # Enviar a cada destino y guardar el resultado
    deliveries = []
    for destination in message_data.destinations:
        service = AVAILABLE_SERVICES[destination]()
        logger.info(f"Enviando a {destination} → Usuario: {current_user.username}")
        
        result = service.send(
            message=message_data.content,
            username=current_user.username
        )
        
        delivery = models.MessageDelivery(
            message_id=new_message.id,
            service=destination,
            status=result["status"],
            provider_response=result["provider_response"]
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        deliveries.append(delivery)
        
        logger.info(f"Resultado → Servicio: {destination} | Estado: {result['status']} | Usuario: {current_user.username}")
    
    # Construir la respuesta
    return schemas.MessageResponse(
        id=new_message.id,
        content=new_message.content,
        created_at=new_message.created_at,
        deliveries=[
            schemas.DeliveryResponse(
                service=d.service,
                status=d.status,
                provider_response=d.provider_response
            )
            for d in deliveries
        ]
    )