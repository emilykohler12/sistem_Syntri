from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from app.repositories.message_repository import MessageRepository
from app.repositories.user_repository import UserRepository
from app import models, schemas
from app.services.slack_service import SlackService
from app.services.discord_service import DiscordService
import time
import logging

logger = logging.getLogger(__name__)

AVAILABLE_SERVICES = {
    "slack": SlackService,
    "discord": DiscordService,
}

MAX_RETRIES = 3
RETRY_DELAY = 1


class MessageService:
    """Lógica de negocio de mensajes: límites, envío, reintentos."""

    def __init__(self, db: Session):
        self.db = db
        self.msg_repo = MessageRepository(db)
        self.user_repo = UserRepository(db)

    def get_effective_limit(self, user: models.User) -> int:
        if user.daily_limit is not None:
            return user.daily_limit
        config = self.msg_repo.get_config()
        return config.daily_message_limit if config else 100

    def check_and_increment(self, user_id: int, limit: int) -> int:
        today = date.today()
        usage = self.msg_repo.get_daily_usage(user_id, today)
        current_count = usage.message_count if usage else 0

        if current_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Límite diario de {limit} mensajes alcanzado. Volvé mañana."
            )

        self.db.execute(text("""
            INSERT INTO daily_usage (user_id, usage_date, message_count)
            VALUES (:uid, :today, 1)
            ON CONFLICT (user_id, usage_date)
            DO UPDATE SET message_count = daily_usage.message_count + 1
        """), {"uid": user_id, "today": today})

        return current_count + 1

    def send(
        self,
        content: str,
        destinations: list[str],
        current_user: models.User
    ) -> schemas.MessageResponse:

        # Validaciones
        if not content or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El mensaje no puede estar vacío."
            )

        destinos_limpios = [d.strip() for d in destinations if d.strip()]
        if not destinos_limpios:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Debe indicar al menos un destino válido. Disponibles: {list(AVAILABLE_SERVICES.keys())}"
            )

        # Verificar y registrar límite
        limit = self.get_effective_limit(current_user)
        new_count = self.check_and_increment(current_user.id, limit)
        logger.info(f"Rate limit → Usuario: {current_user.username} | Restantes hoy: {limit - new_count}")

        # Guardar mensaje
        message = self.msg_repo.create_message(current_user.id, content)
        logger.info(f"Mensaje guardado → ID: {message.id} | Usuario: {current_user.username}")

        # Enviar a cada destino con retry
        deliveries = []
        for destination in destinos_limpios:
            if destination not in AVAILABLE_SERVICES:
                logger.warning(f"Destino desconocido '{destination}' → failed")
                try:
                    delivery = self.msg_repo.create_delivery(
                        message.id, destination, "failed",
                        f"Destino '{destination}' no reconocido", 1
                    )
                    deliveries.append(delivery)
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error guardando delivery desconocido: {e}")
                continue

            service = AVAILABLE_SERVICES[destination]()
            last_result = None

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(f"Enviando a {destination} → Intento {attempt}/{MAX_RETRIES} | Usuario: {current_user.username}")
                    result = service.send(message=content, username=current_user.username)
                except Exception as e:
                    logger.error(f"Excepción en '{destination}' intento {attempt}: {e}")
                    result = {"status": "failed", "provider_response": f"Error inesperado: {str(e)}"}

                last_result = result

                try:
                    delivery = self.msg_repo.create_delivery(
                        message.id, destination,
                        result["status"], result["provider_response"], attempt
                    )
                    deliveries.append(delivery)
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Error guardando delivery intento {attempt} de '{destination}': {e}")

                logger.info(f"Intento {attempt} → {destination} | Estado: {result['status']}")

                if result["status"] == "success":
                    break
                if attempt < MAX_RETRIES:
                    logger.info(f"Reintentando '{destination}' en {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)

            if last_result and last_result["status"] == "failed":
                logger.warning(f"Todos los intentos fallaron para '{destination}'")

        return schemas.MessageResponse(
            id=message.id,
            content=message.content,
            created_at=message.created_at,
            deliveries=[
                schemas.DeliveryResponse(
                    service=d.service,
                    status=d.status,
                    provider_response=d.provider_response,
                    attempt=d.attempt if hasattr(d, "attempt") else 1
                )
                for d in deliveries
            ]
        )

    def get_user_messages(
        self, user_id: int,
        status: str | None, service: str | None,
        from_date: str | None, to_date: str | None
    ) -> list:
        messages = self.msg_repo.get_messages_by_user(
            user_id, status, service, from_date, to_date
        )
        return [self._format_message(m) for m in messages]

    def _format_message(self, msg: models.Message) -> dict:
        return {
            "id": msg.id,
            "content": msg.content,
            "created_at": msg.created_at,
            "deliveries": [
                {"service": d.service, "status": d.status,
                 "provider_response": d.provider_response, "attempt": d.attempt}
                for d in msg.deliveries
            ]
        }