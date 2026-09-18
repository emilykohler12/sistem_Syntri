import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailService:
    """
    Envío de emails vía la API HTTP de Brevo (no SMTP crudo: no depende de
    un login/puerto SMTP, solo de la API key, y evita el bloqueo de puertos
    salientes que tienen algunos hosts).

    Si no hay BREVO_API_KEY configurada, no rompe el flujo: loguea el
    contenido del email como si lo hubiera enviado. Sirve para desarrollar y
    testear el flujo de recuperación de contraseña sin credenciales reales a
    mano (mismo criterio que Slack/Discord/TelegramService cuando falta su
    configuración).
    """

    def __init__(self):
        self.api_key = os.getenv("BREVO_API_KEY")
        self.from_email = os.getenv("BREVO_FROM_EMAIL", "no-reply@syntri.local")
        self.from_name = os.getenv("BREVO_FROM_NAME", "System Syntri")

    def send_password_reset_code(self, to_email: str, code: str) -> bool:
        subject = "Tu código para recuperar tu contraseña — System Syntri"
        html = f"""
            <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
              <h2>Recuperar contraseña</h2>
              <p>Usá este código para restablecer tu contraseña. Vence en 15 minutos:</p>
              <p style="font-size: 32px; font-weight: bold; letter-spacing: 6px;">{code}</p>
              <p>Si no pediste este código, podés ignorar este mensaje.</p>
            </div>
        """

        if not self.api_key:
            logger.warning(
                f"BREVO_API_KEY no configurada → no se envió el email de verdad. "
                f"Código de recuperación para {to_email}: {code}"
            )
            return True

        try:
            response = requests.post(
                BREVO_API_URL,
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "sender": {"name": self.from_name, "email": self.from_email},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "htmlContent": html,
                },
                timeout=10,
            )
            if response.status_code >= 300:
                logger.error(f"Brevo rechazó el email a {to_email} → {response.status_code}: {response.text}")
                return False
            logger.info(f"Email de recuperación enviado → {to_email}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando email de recuperación a {to_email} → {e}")
            return False
