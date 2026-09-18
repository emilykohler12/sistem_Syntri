import os
import smtplib
import logging
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class EmailService:
    """
    Envío de emails vía SMTP.

    Si no hay SMTP configurado (SMTP_HOST), no rompe el flujo: loguea el
    contenido del email como si lo hubiera enviado. Sirve para desarrollar y
    testear el flujo de recuperación de contraseña sin tener un servidor de
    correo real a mano (mismo criterio que SlackService/DiscordService
    cuando falta su configuración).
    """

    def __init__(self):
        self.host = os.getenv("SMTP_HOST")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.user = os.getenv("SMTP_USER")
        self.password = os.getenv("SMTP_PASSWORD")
        self.from_address = os.getenv("SMTP_FROM", "no-reply@syntri.local")

    def send_password_reset_code(self, to_email: str, code: str) -> bool:
        subject = "Tu código para recuperar tu contraseña — Sistem Syntri"
        body = (
            f"Usá este código para restablecer tu contraseña: {code}\n\n"
            "Vence en 15 minutos. Si no pediste este código, ignorá este mensaje."
        )

        if not self.host:
            logger.warning(
                f"SMTP no configurado → no se envió el email de verdad. "
                f"Código de recuperación para {to_email}: {code}"
            )
            return True

        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = self.from_address
        message["To"] = to_email

        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                if self.user and self.password:
                    server.login(self.user, self.password)
                server.sendmail(self.from_address, [to_email], message.as_string())
            logger.info(f"Email de recuperación enviado → {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error enviando email de recuperación a {to_email} → {e}")
            return False
