from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.auth import verify_password, hash_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.services.email_service import EmailService
from app import schemas
from collections import defaultdict
import logging
import random
import threading
import time

logger = logging.getLogger(__name__)

RESET_CODE_LENGTH = 6
RESET_CODE_EXPIRE_MINUTES = 15

# ── Límite de intentos de login ────────────────────────────────────────────────
# En memoria, por proceso (mismo patrón que el rate limit por IP de main.py).
# Bloquea por username, no por IP: evita que alguien fuerce mil contraseñas
# contra una cuenta puntual aunque rote de IP.
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300  # 5 minutos

_login_attempts: dict = defaultdict(lambda: {"count": 0, "locked_until": 0.0})
_login_attempts_lock = threading.Lock()


class AuthService:
    """Lógica de negocio de autenticación."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.email_service = EmailService()

    def _check_lockout(self, email: str) -> None:
        with _login_attempts_lock:
            locked_until = _login_attempts[email]["locked_until"]
        remaining = locked_until - time.time()
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos fallidos. Probá de nuevo en {int(remaining) + 1}s."
            )

    def _register_failed_attempt(self, email: str) -> None:
        with _login_attempts_lock:
            entry = _login_attempts[email]
            entry["count"] += 1
            if entry["count"] >= MAX_LOGIN_ATTEMPTS:
                entry["locked_until"] = time.time() + LOGIN_LOCKOUT_SECONDS
                entry["count"] = 0
                logger.warning(f"Cuenta bloqueada temporalmente por intentos fallidos → '{email}'")

    def _clear_attempts(self, email: str) -> None:
        with _login_attempts_lock:
            _login_attempts.pop(email, None)

    def register(self, email: str, password: str) -> schemas.UserResponse:
        email = email.strip().lower()
        logger.info(f"Intento de registro → Email: {email}")

        if self.repo.get_by_email(email):
            logger.warning(f"Registro fallido → '{email}' ya existe")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ese email ya está registrado"
            )

        default_role = self.repo.get_role_by_name("user")
        # El username sigue existiendo internamente (lo usan las rutas de
        # admin y el JWT), pero ya no se le pide al usuario: usamos el email.
        user = self.repo.create(email, email, password, default_role.id)

        logger.info(f"Registro exitoso → '{email}' | ID: {user.id}")
        return schemas.UserResponse.from_orm_user(user)

    def login(self, email: str, password: str) -> schemas.Token:
        email = email.strip().lower()
        logger.info(f"Intento de login → Email: {email}")

        self._check_lockout(email)

        user = self.repo.get_by_email(email)

        if not user or not verify_password(password, user.password):
            logger.warning(f"Login fallido → credenciales incorrectas para '{email}'")
            self._register_failed_attempt(email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos"
            )

        if not user.is_active:
            logger.warning(f"Login fallido → '{email}' está cancelado")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta fue cancelada. Contactá al administrador."
            )

        self._clear_attempts(email)
        token = create_access_token(data={
            "sub": user.username,
            "role": user.role_name,
            "permissions": user.all_permissions,
        })
        logger.info(f"Login exitoso → '{email}' | Rol: {user.role_name}")
        return schemas.Token(access_token=token, token_type="bearer")

    def forgot_password(self, email: str) -> dict:
        email = email.strip().lower()
        user = self.repo.get_by_email(email)

        # Siempre la misma respuesta exista o no el email: si no, alguien
        # podría usar este endpoint para averiguar qué emails están
        # registrados probando uno por uno.
        generic_response = {"message": "Si el email está registrado, te enviamos un código."}

        if not user or not user.is_active:
            logger.info(f"Pedido de recuperación para email no registrado o inactivo → '{email}'")
            return generic_response

        code = f"{random.randint(0, 999999):06d}"
        expires_at = datetime.utcnow() + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)
        self.repo.create_reset_code(user.id, hash_password(code), expires_at)

        self.email_service.send_password_reset_code(user.email, code)
        logger.info(f"Código de recuperación generado → '{email}'")
        return generic_response

    def reset_password(self, email: str, code: str, new_password: str) -> dict:
        email = email.strip().lower()
        user = self.repo.get_by_email(email)

        invalid_code_error = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido o vencido."
        )

        if not user:
            raise invalid_code_error

        reset_code = self.repo.get_active_reset_code(user.id)
        if not reset_code:
            raise invalid_code_error

        if reset_code.expires_at < datetime.utcnow():
            raise invalid_code_error

        if not verify_password(code, reset_code.code_hash):
            raise invalid_code_error

        self.repo.mark_reset_code_used(reset_code)
        self.repo.update_password(user, new_password)
        logger.info(f"Contraseña restablecida vía código → '{email}'")
        return {"message": "Contraseña actualizada. Ya podés iniciar sesión."}