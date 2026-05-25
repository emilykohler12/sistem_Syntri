import discord
import asyncio
import os
import logging
from dotenv import load_dotenv
from app.services.notification_service import NotificationService

load_dotenv()
logger = logging.getLogger(__name__)

class DiscordService(NotificationService):
    """Servicio para enviar mensajes a Discord via Bot"""
    
    def __init__(self):
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        self.channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
    
    def send(self, message: str, username: str) -> dict:
        """Envía un mensaje a Discord firmado con el nombre del usuario"""
        
        if not self.token or not self.channel_id:
            logger.error("Error de configuración → DISCORD_BOT_TOKEN o DISCORD_CHANNEL_ID no están definidos en el .env")
            return {
                "status": "failed",
                "provider_response": "Configuración de Discord incompleta"
            }
        
        try:
            logger.info(f"Enviando mensaje a Discord → Usuario: {username}")
            result = asyncio.run(self._send_message(message, username))
            return result
        except Exception as e:
            logger.error(f"Error al enviar a Discord → {str(e)}")
            return {
                "status": "failed",
                "provider_response": f"Error inesperado: {str(e)}"
            }
    
    async def _send_message(self, message: str, username: str) -> dict:
        """Función asíncrona que maneja la conexión con Discord"""
        
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        result = {}
        
        @client.event
        async def on_ready():
            nonlocal result
            try:
                channel = client.get_channel(self.channel_id)
                if not channel:
                    logger.error(f"Error → Canal de Discord con ID {self.channel_id} no encontrado")
                    result = {
                        "status": "failed",
                        "provider_response": f"Canal {self.channel_id} no encontrado"
                    }
                else:
                    await channel.send(f"**[{username}]**: {message}")
                    logger.info(f"Mensaje enviado exitosamente a Discord → Usuario: {username}")
                    result = {
                        "status": "success",
                        "provider_response": "Mensaje enviado correctamente"
                    }
            finally:
                await client.close()
        
        await client.start(self.token)
        return result