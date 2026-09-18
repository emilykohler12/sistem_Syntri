import os
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app import models
from app.auth import hash_password

DEFAULT_ADMIN_EMAIL = "admin@syntri.local"
DEFAULT_ADMIN_PASSWORD = "admin123"


def create_admin_if_missing() -> None:
    """
    Crea el usuario admin inicial si todavía no existe. Se llama sola al
    arrancar la app (así no hace falta entrar a una shell del hosting para
    correr create_admin.py a mano) y también puede correrse manual con
    `python create_admin.py`.

    El email/contraseña salen de ADMIN_EMAIL/ADMIN_PASSWORD si están
    definidas; si no, usa los valores por defecto documentados en el README.
    """
    email = os.getenv("ADMIN_EMAIL", DEFAULT_ADMIN_EMAIL)
    password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            print(f"El usuario admin ya existe ({email})")
            return

        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
        admin = models.User(
            username=email,
            email=email,
            password=hash_password(password),
            role_id=admin_role.id,
        )
        db.add(admin)
        try:
            db.commit()
            print(f"Usuario admin creado exitosamente ({email} / {password})")
        except IntegrityError:
            # Otro worker lo creó primero (varios procesos arrancan a la vez
            # en un deploy con WEB_CONCURRENCY > 1) — no es un error real.
            db.rollback()
            print(f"El usuario admin ya existe ({email})")
    finally:
        db.close()
