from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticación"])

@router.post("/register", response_model=schemas.UserResponse, status_code=201)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario con rol 'user' por defecto"""
    
    logger.info(f"Intento de registro → Usuario: {user_data.username}")
    
    existing_user = db.query(models.User).filter(
        models.User.username == user_data.username
    ).first()
    
    if existing_user:
        logger.warning(f"Registro fallido → El usuario '{user_data.username}' ya existe en el sistema")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El username ya está en uso"
        )
    
    new_user = models.User(
        username=user_data.username,
        password=hash_password(user_data.password),
        role="user"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Registro exitoso → Usuario '{new_user.username}' creado con rol '{new_user.role}' | ID: {new_user.id}")
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Inicia sesión y devuelve un JWT"""
    
    logger.info(f"Intento de login → Usuario: {user_data.username}")
    
    user = db.query(models.User).filter(
        models.User.username == user_data.username
    ).first()
    
    if not user:
        logger.warning(f"Login fallido → El usuario '{user_data.username}' no existe en el sistema")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    if not verify_password(user_data.password, user.password):
        logger.warning(f"Login fallido → Contraseña incorrecta para el usuario '{user_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    
    logger.info(f"Login exitoso → Usuario '{user.username}' | Rol: '{user.role}' | Token generado correctamente")
    return {"access_token": access_token, "token_type": "bearer"}