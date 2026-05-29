from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Helpers de permisos ───────────────────────────────────────────────────────

def require_roles(*role_names: str):
    """
    Dependencia FastAPI reutilizable para proteger rutas por rol.

    Uso:
        @router.get("/admin", dependencies=[Depends(require_roles("admin"))])

    O combinado con get_current_user:
        @router.get("/mod")
        def endpoint(user = Depends(require_roles("admin", "moderator"))):
            ...
    """
    def _checker(current_user=Depends(_get_current_user_placeholder)):
        if not current_user.has_role(*role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(role_names)}",
            )
        return current_user
    return _checker


def _get_current_user_placeholder():
    """
    Reemplazá esta función por tu dependencia real de autenticación
    (la que decodifica el JWT y devuelve el User de la BD).
    """
    raise NotImplementedError(
        "Conectá require_roles() a tu dependencia get_current_user real."
    )