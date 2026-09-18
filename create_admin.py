from app.database import SessionLocal
from app import models
from app.auth import hash_password

ADMIN_EMAIL = "admin@syntri.local"
ADMIN_PASSWORD = "admin123"

db = SessionLocal()

existing = db.query(models.User).filter(
    models.User.email == ADMIN_EMAIL
).first()

if existing:
    print(f"El usuario admin ya existe ({ADMIN_EMAIL})")
else:
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    admin = models.User(
        username=ADMIN_EMAIL,
        email=ADMIN_EMAIL,
        password=hash_password(ADMIN_PASSWORD),
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    print(f"Usuario admin creado exitosamente ({ADMIN_EMAIL} / {ADMIN_PASSWORD})")

db.close()
