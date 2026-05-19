from app.database import SessionLocal
from app import models
from app.auth import hash_password

db = SessionLocal()

# Verificamos que no exista ya
existing = db.query(models.User).filter(
    models.User.username == "admin"
).first()

if existing:
    print("El usuario admin ya existe")
else:
    admin = models.User(
        username="admin",
        password=hash_password("admin123"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    print("Usuario admin creado exitosamente")

db.close()
