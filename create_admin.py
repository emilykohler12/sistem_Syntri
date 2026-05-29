from app.database import SessionLocal
from app import models
from app.auth import hash_password

db = SessionLocal()

existing = db.query(models.User).filter(
    models.User.username == "admin"
).first()

if existing:
    print("El usuario admin ya existe")
else:
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    admin = models.User(
        username="admin",
        password=hash_password("admin123"),
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    print("Usuario admin creado exitosamente")

db.close()