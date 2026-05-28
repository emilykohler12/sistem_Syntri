from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.services.slack_service import SlackService
from app.services.discord_service import DiscordService
from typing import Optional
from fastapi import Query
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/messages", tags=["Mensajes"])

AVAILABLE_SERVICES = {
    "slack": SlackService,
    "discord": DiscordService,
}


def _get_effective_limit(user: models.User, db: Session) -> int:
    """Devuelve el límite que aplica al usuario: personalizado o global."""
    if user.daily_limit is not None:
        return user.daily_limit
    config = db.query(models.Config).filter(models.Config.id == 1).first()
    return config.daily_message_limit if config else 100


def _check_and_increment(user_id: int, limit: int, db: Session) -> int:
    """
    Verifica el límite y incrementa el contador de forma atómica con upsert.
    Devuelve el conteo actualizado, o lanza 429 si ya se alcanzó el límite.
    """
    today = date.today()

    # Primero chequeamos sin incrementar todavía
    usage = db.query(models.DailyUsage).filter(
        models.DailyUsage.user_id == user_id,
        models.DailyUsage.usage_date == today
    ).first()

    current_count = usage.message_count if usage else 0

    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Límite diario de {limit} mensajes alcanzado. Volvé mañana."
        )

    # Upsert atómico: INSERT si no existe, UPDATE si existe
    db.execute(text("""
        INSERT INTO daily_usage (user_id, usage_date, message_count)
        VALUES (:uid, :today, 1)
        ON CONFLICT (user_id, usage_date)
        DO UPDATE SET message_count = daily_usage.message_count + 1
    """), {"uid": user_id, "today": today})

    return current_count + 1


@router.post("/", response_model=schemas.MessageResponse, status_code=201)
def send_message(
    message_data: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Envía un mensaje a múltiples plataformas"""

    logger.info(f"Pedido de envío → Usuario: {current_user.username} | Destinos: {message_data.destinations}")

    # Validar que el contenido no esté vacío ni sea solo espacios
    if not message_data.content or not message_data.content.strip():
        logger.warning(f"Contenido vacío → Usuario: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacío."
        )

    # Validar que se envíe al menos un destino y que ninguno sea string vacío
    destinos_limpios = [d.strip() for d in message_data.destinations if d.strip()]
    if not destinos_limpios:
        logger.warning(f"Lista de destinos vacía o inválida → Usuario: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Debe indicar al menos un destino válido. Disponibles: {list(AVAILABLE_SERVICES.keys())}"
        )
    message_data.destinations = destinos_limpios



    # Verificar límite e incrementar contador (atómico)
    limit = _get_effective_limit(current_user, db)
    new_count = _check_and_increment(current_user.id, limit, db)

    remaining = limit - new_count
    logger.info(f"Rate limit → Usuario: {current_user.username} | Mensajes restantes hoy: {remaining}")

    # Guardar el mensaje
    new_message = models.Message(user_id=current_user.id, content=message_data.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    logger.info(f"Mensaje guardado → ID: {new_message.id} | Usuario: {current_user.username}")

    # Enviar a cada destino (cada uno es independiente, un fallo no bloquea los demás)
    deliveries = []
    for destination in message_data.destinations:
        try:
            if destination not in AVAILABLE_SERVICES:
                logger.warning(f"Destino desconocido '{destination}' → registrado como failed | Usuario: {current_user.username}")
                result = {"status": "failed", "provider_response": f"Destino '{destination}' no reconocido"}
            else:
                service = AVAILABLE_SERVICES[destination]()
                logger.info(f"Enviando a {destination} → Usuario: {current_user.username}")
                result = service.send(message=message_data.content, username=current_user.username)

        except Exception as e:
            logger.error(f"Error inesperado en '{destination}' → {str(e)} | Usuario: {current_user.username}")
            result = {"status": "failed", "provider_response": f"Error inesperado: {str(e)}"}

        try:
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
        except Exception as e:
            db.rollback()
            logger.error(f"Error al guardar delivery de '{destination}' → {str(e)}")
            # Igual agregamos el delivery en memoria para incluirlo en la respuesta
            deliveries.append(models.MessageDelivery(
                message_id=new_message.id,
                service=destination,
                status="failed",
                provider_response=f"Error al guardar: {str(e)}"
            ))

        logger.info(f"Resultado → Servicio: {destination} | Estado: {result['status']} | Usuario: {current_user.username}")

    return schemas.MessageResponse(
        id=new_message.id,
        content=new_message.content,
        created_at=new_message.created_at,
        deliveries=[
            schemas.DeliveryResponse(service=d.service, status=d.status, provider_response=d.provider_response)
            for d in deliveries
        ]
    )


@router.get("/", response_model=list)
def get_my_messages(
    status: Optional[str] = Query(None, description="Filtrar por estado: success, pending, failed"),
    service: Optional[str] = Query(None, description="Filtrar por servicio: slack, discord"),
    from_date: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Usuario: lista sus propios mensajes con filtros"""

    logger.info(f"Usuario '{current_user.username}' consultando sus mensajes")

    query = db.query(models.Message).filter(models.Message.user_id == current_user.id)

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
            "content": msg.content,
            "created_at": msg.created_at,
            "deliveries": [
                {"service": d.service, "status": d.status, "provider_response": d.provider_response}
                for d in msg.deliveries
            ]
        })

    logger.info(f"Usuario '{current_user.username}' obtuvo {len(result)} mensajes")
    return result