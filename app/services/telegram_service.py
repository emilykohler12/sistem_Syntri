import requests
import os
import logging
from dotenv import load_dotenv
from app.services.notification_service import NotificationService

load_dotenv()
logger = logging.getLogger(__name__)

class TelegramService(NotificationService):
    """Servicio para enviar mensajes a Telegram vía Bot API (sendMessage)"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send(self, message: str, username: str) -> dict:
        """Envía un mensaje a Telegram firmado con el nombre del usuario"""

        if not self.bot_token or not self.chat_id:
            logger.error("Error de configuración → TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no están definidos en el .env")
            return {
                "status": "failed",
                "provider_response": "Configuración de Telegram incompleta"
            }

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": f"[{username}]: {message}",
        }

        try:
            logger.info(f"Enviando mensaje a Telegram → Usuario: {username}")
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Mensaje enviado exitosamente a Telegram → Usuario: {username}")
                return {
                    "status": "success",
                    "provider_response": response.text
                }
            else:
                logger.warning(f"Telegram rechazó el mensaje → Código: {response.status_code} | Respuesta: {response.text}")
                return {
                    "status": "failed",
                    "provider_response": f"Error {response.status_code}: {response.text}"
                }

        except requests.exceptions.Timeout:
            logger.error("Error al enviar a Telegram → Tiempo de espera agotado")
            return {
                "status": "failed",
                "provider_response": "Timeout: Telegram no respondió a tiempo"
            }
        except requests.exceptions.ConnectionError:
            logger.error("Error al enviar a Telegram → No se pudo conectar con el servidor")
            return {
                "status": "failed",
                "provider_response": "Error de conexión con Telegram"
            }
