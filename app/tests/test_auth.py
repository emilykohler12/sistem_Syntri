import pytest
from app.auth import hash_password, verify_password, create_access_token
from jose import jwt
import os
from dotenv import load_dotenv

load_dotenv()

# ── Hasheo ────────────────────────────────────────────────────────────────────

def test_hash_password_genera_hash_diferente_al_original():
    password = "mipassword123"
    assert password != hash_password(password)

def test_verify_password_correcta():
    password = "mipassword123"
    assert verify_password(password, hash_password(password)) == True

def test_verify_password_incorrecta():
    hashed = hash_password("mipassword123")
    assert verify_password("otrapassword", hashed) == False

# ── JWT ───────────────────────────────────────────────────────────────────────

def test_create_access_token_genera_token():
    token = create_access_token(data={"sub": "testuser", "role": "user"})
    assert token is not None and len(token) > 0

def test_create_access_token_contiene_datos_correctos():
    token = create_access_token(data={"sub": "testuser", "role": "user"})
    payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
    assert payload["sub"] == "testuser"
    assert payload["role"] == "user"

# ── Registro ──────────────────────────────────────────────────────────────────

def test_registro_exitoso(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "nuevo_usuario",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "nuevo_usuario"
    assert data["role"]["name"] == "user"
    assert "password" not in data

def test_registro_usuario_duplicado(client):
    client.post("/api/v1/auth/register", json={"username": "dup", "password": "pass123"})
    response = client.post("/api/v1/auth/register", json={"username": "dup", "password": "otrapass"})
    assert response.status_code == 409

# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_exitoso(client):
    client.post("/api/v1/auth/register", json={"username": "usuario_login", "password": "password123"})
    response = client.post("/api/v1/auth/login", data={"username": "usuario_login", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_password_incorrecta(client):
    client.post("/api/v1/auth/register", json={"username": "usuario_login2", "password": "password123"})
    response = client.post("/api/v1/auth/login", data={"username": "usuario_login2", "password": "incorrecta"})
    assert response.status_code == 401

def test_login_usuario_inexistente(client):
    response = client.post("/api/v1/auth/login", data={"username": "noexiste", "password": "pass"})
    assert response.status_code == 401

def test_login_usuario_cancelado(client, admin_user, admin_token):
    """Un usuario cancelado no puede iniciar sesión"""
    client.post("/api/v1/auth/register", json={"username": "usuario_cancelado", "password": "pass123"})
    client.patch(
        "/api/v1/admin/users/usuario_cancelado/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.post("/api/v1/auth/login", data={"username": "usuario_cancelado", "password": "pass123"})
    assert response.status_code == 403

# ── Middleware de autenticación ───────────────────────────────────────────────

def test_ruta_protegida_sin_token(client):
    """Acceder a ruta protegida sin token devuelve 401"""
    response = client.get("/api/v1/messages/")
    assert response.status_code == 401

def test_ruta_protegida_con_token_invalido(client):
    """Token inválido devuelve 401"""
    response = client.get(
        "/api/v1/messages/",
        headers={"Authorization": "Bearer tokeninvalido"}
    )
    assert response.status_code == 401

def test_rutas_publicas_sin_token(client):
    """Login y register son accesibles sin token (el middleware no bloquea con 401 por falta de token)"""
    # Register debe devolver 201 sin necesitar token
    r_register = client.post("/api/v1/auth/register", json={"username": "usuario_publico", "password": "pass123"})
    assert r_register.status_code == 201

    # Login con credenciales válidas debe devolver 200 sin token
    r_login = client.post("/api/v1/auth/login", data={"username": "usuario_publico", "password": "pass123"})
    assert r_login.status_code == 200