import requests
import os
import logging
from dotenv import load_dotenv
from app.services.notification_service import NotificationService

load_dotenv()
logger = logging.getLogger(__name__)

class SlackService(NotificationService):
    """Servicio para enviar mensajes a Slack via Incoming Webhooks"""
    
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    
    def send(self, message: str, username: str) -> dict:
        """Envía un mensaje a Slack firmado con el nombre del usuario"""
        
        if not self.webhook_url:
            logger.error("Error de configuración → SLACK_WEBHOOK_URL no está definida en el .env")
            return {
                "status": "failed",
                "provider_response": "SLACK_WEBHOOK_URL no configurada"
            }
        
        payload = {
            "text": f"*[{username}]*: {message}"
        }
        
        try:
            logger.info(f"Enviando mensaje a Slack → Usuario: {username}")
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Mensaje enviado exitosamente a Slack → Usuario: {username}")
                return {
                    "status": "success",
                    "provider_response": response.text
                }
            else:
                logger.warning(f"Slack rechazó el mensaje → Código: {response.status_code} | Respuesta: {response.text}")
                return {
                    "status": "failed",
                    "provider_response": f"Error {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            logger.error("Error al enviar a Slack → Tiempo de espera agotado")
            return {
                "status": "failed",
                "provider_response": "Timeout: Slack no respondió a tiempo"
            }
        except requests.exceptions.ConnectionError:
            logger.error("Error al enviar a Slack → No se pudo conectar con el servidor")
            return {
                "status": "failed",
                "provider_response": "Error de conexión con Slack"
            }