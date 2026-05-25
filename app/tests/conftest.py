import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Base de datos en memoria solo para tests
# No toca la base de datos real
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Reemplaza la base de datos real con la de tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def setup_database():
    """Crea las tablas antes de cada test y las borra después"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Cliente de prueba que simula pedidos HTTP"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_user(client):
    """Crea un usuario admin para tests"""
    from app.database import get_db
    from app import models
    from app.auth import hash_password
    
    db = TestingSessionLocal()
    admin = models.User(
        username="admin_test",
        password=hash_password("admin123"),
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.close()
    return {"username": "admin_test", "password": "admin123"}

@pytest.fixture
def user_token(client):
    """Registra un usuario y devuelve su token"""
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "test123"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "test123"
    })
    return response.json()["access_token"]

@pytest.fixture
def admin_token(client, admin_user):
    """Devuelve el token del admin"""
    response = client.post("/api/v1/auth/login", data={
        "username": admin_user["username"],
        "password": admin_user["password"]
    })
    return response.json()["access_token"]