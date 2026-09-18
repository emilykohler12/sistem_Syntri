from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.auth import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app import schemas
from collections import defaultdict
import logging
import threading
import time

logger = logging.getLogger(__name__)

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

    def _check_lockout(self, username: str) -> None:
        with _login_attempts_lock:
            locked_until = _login_attempts[username]["locked_until"]
        remaining = locked_until - time.time()
        if remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos fallidos. Probá de nuevo en {int(remaining) + 1}s."
            )

    def _register_failed_attempt(self, username: str) -> None:
        with _login_attempts_lock:
            entry = _login_attempts[username]
            entry["count"] += 1
            if entry["count"] >= MAX_LOGIN_ATTEMPTS:
                entry["locked_until"] = time.time() + LOGIN_LOCKOUT_SECONDS
                entry["count"] = 0
                logger.warning(f"Cuenta bloqueada temporalmente por intentos fallidos → '{username}'")

    def _clear_attempts(self, username: str) -> None:
        with _login_attempts_lock:
            _login_attempts.pop(username, None)

    def register(self, username: str, password: str) -> schemas.UserResponse:
        logger.info(f"Intento de registro → Usuario: {username}")

        if self.repo.get_by_username(username):
            logger.warning(f"Registro fallido → '{username}' ya existe")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El username ya está en uso"
            )

        default_role = self.repo.get_role_by_name("user")
        user = self.repo.create(username, password, default_role.id)

        logger.info(f"Registro exitoso → '{username}' | ID: {user.id}")
        return schemas.UserResponse.from_orm_user(user)

    def login(self, username: str, password: str) -> schemas.Token:
        logger.info(f"Intento de login → Usuario: {username}")

        self._check_lockout(username)

        user = self.repo.get_by_username(username)

        if not user or not verify_password(password, user.password):
            logger.warning(f"Login fallido → credenciales incorrectas para '{username}'")
            self._register_failed_attempt(username)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos"
            )

        if not user.is_active:
            logger.warning(f"Login fallido → '{username}' está cancelado")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu cuenta fue cancelada. Contactá al administrador."
            )

        self._clear_attempts(username)
        token = create_access_token(data={"sub": user.username, "role": user.role_name})
        logger.info(f"Login exitoso → '{username}' | Rol: {user.role_name}")
        return schemas.Token(access_token=token, token_type="bearer")