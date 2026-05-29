import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
import app.main as main_module

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    from app import models
    if not db.query(models.Role).first():
        db.add(models.Role(name="user", description="Usuario estándar"))
        db.add(models.Role(name="admin", description="Administrador"))
        db.commit()
    if not db.query(models.Config).first():
        db.add(models.Config(id=1, daily_message_limit=100))
        db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    # Override get_db para endpoints
    app.dependency_overrides[get_db] = override_get_db
    # Override SessionLocal para el middleware de auth
    main_module.SessionLocal = TestingSessionLocal
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    # Restaurar SessionLocal real
    from app.database import SessionLocal as RealSessionLocal
    main_module.SessionLocal = RealSessionLocal


@pytest.fixture
def admin_user(client):
    from app import models
    from app.auth import hash_password
    db = TestingSessionLocal()
    admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()
    admin = models.User(
        username="admin_test",
        password=hash_password("admin123"),
        role_id=admin_role.id
    )
    db.add(admin)
    db.commit()
    db.close()
    return {"username": "admin_test", "password": "admin123"}


@pytest.fixture
def user_token(client):
    client.post("/api/v1/auth/register", json={"username": "testuser", "password": "test123"})
    response = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "test123"})
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client, admin_user):
    response = client.post("/api/v1/auth/login", data={
        "username": admin_user["username"],
        "password": admin_user["password"]
    })
    return response.json()["access_token"]