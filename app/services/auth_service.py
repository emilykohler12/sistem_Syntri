from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.auth import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app import schemas
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Lógica de negocio de autenticación."""

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

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

        user = self.repo.get_by_username(username)

        if not user or not verify_password(password, user.password):
            logger.warning(f"Login fallido → credenciales incorrectas para '{username}'")
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

        token = create_access_token(data={"sub": user.username, "role": user.role_name})
        logger.info(f"Login exitoso → '{username}' | Rol: {user.role_name}")
        return schemas.Token(access_token=token, token_type="bearer")