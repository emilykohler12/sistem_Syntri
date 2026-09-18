from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con rol 'user' por defecto"""
    return AuthService(db).register(user_data.email, user_data.password)


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Inicia sesión y devuelve un JWT. El campo 'username' del form es el email."""
    return AuthService(db).login(form_data.username, form_data.password)


@router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Genera un código de 6 dígitos y lo envía por email (vence en 15 minutos)"""
    return AuthService(db).forgot_password(payload.email)


@router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """Cambia la contraseña usando el código enviado por email"""
    return AuthService(db).reset_password(payload.email, payload.code, payload.new_password)