import pytest
from app.auth import hash_password, verify_password, create_access_token
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()

# Tests de hasheo de contraseñas
def test_hash_password_genera_hash_diferente_al_original():
    """La contraseña hasheada no debe ser igual a la original"""
    password = "mipassword123"
    hashed = hash_password(password)
    assert password != hashed

def test_verify_password_correcta():
    """Verificar una contraseña correcta debe devolver True"""
    password = "mipassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) == True

def test_verify_password_incorrecta():
    """Verificar una contraseña incorrecta debe devolver False"""
    password = "mipassword123"
    hashed = hash_password(password)
    assert verify_password("otrapassword", hashed) == False

# Tests de JWT
def test_create_access_token_genera_token():
    """El token generado no debe estar vacío"""
    token = create_access_token(data={"sub": "testuser", "role": "user"})
    assert token is not None
    assert len(token) > 0

def test_create_access_token_contiene_datos_correctos():
    """El token debe contener el username y rol correctos"""
    token = create_access_token(data={"sub": "testuser", "role": "user"})
    payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"

# Tests de endpoints de autenticación
def test_registro_exitoso(client):
    """Registrar un usuario nuevo debe devolver 201"""
    response = client.post("/api/v1/auth/register", json={
        "username": "nuevo_usuario",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "nuevo_usuario"
    assert data["role"] == "user"
    assert "password" not in data

def test_registro_usuario_duplicado(client):
    """Registrar un usuario que ya existe debe devolver 409"""
    client.post("/api/v1/auth/register", json={
        "username": "usuario_dup",
        "password": "password123"
    })
    response = client.post("/api/v1/auth/register", json={
        "username": "usuario_dup",
        "password": "otrapassword"
    })
    assert response.status_code == 409

def test_login_exitoso(client):
    """Login con credenciales correctas debe devolver token"""
    client.post("/api/v1/auth/register", json={
        "username": "usuario_login",
        "password": "password123"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "usuario_login",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_password_incorrecta(client):
    """Login con contraseña incorrecta debe devolver 401"""
    client.post("/api/v1/auth/register", json={
        "username": "usuario_login2",
        "password": "password123"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "usuario_login2",
        "password": "passwordincorrecta"
    })
    assert response.status_code == 401

def test_login_usuario_inexistente(client):
    """Login con usuario que no existe debe devolver 401"""
    response = client.post("/api/v1/auth/login", data={
        "username": "noexiste",
        "password": "password123"
    })
    assert response.status_code == 401