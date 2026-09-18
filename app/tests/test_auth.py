import pytest
from unittest.mock import patch
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
        "email": "nuevo_usuario@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "nuevo_usuario@example.com"
    assert data["role"]["name"] == "user"
    assert "password" not in data

def test_registro_usuario_duplicado(client):
    client.post("/api/v1/auth/register", json={"email": "dup", "password": "pass123"})
    response = client.post("/api/v1/auth/register", json={"email": "dup", "password": "otrapass"})
    assert response.status_code == 409

# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_exitoso(client):
    client.post("/api/v1/auth/register", json={"email": "usuario_login", "password": "password123"})
    response = client.post("/api/v1/auth/login", data={"username": "usuario_login", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_password_incorrecta(client):
    client.post("/api/v1/auth/register", json={"email": "usuario_login2", "password": "password123"})
    response = client.post("/api/v1/auth/login", data={"username": "usuario_login2", "password": "incorrecta"})
    assert response.status_code == 401

def test_login_usuario_inexistente(client):
    response = client.post("/api/v1/auth/login", data={"username": "noexiste", "password": "pass"})
    assert response.status_code == 401

def test_login_usuario_cancelado(client, admin_user, admin_token):
    """Un usuario cancelado no puede iniciar sesión"""
    client.post("/api/v1/auth/register", json={"email": "usuario_cancelado", "password": "pass123"})
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
    r_register = client.post("/api/v1/auth/register", json={"email": "usuario_publico", "password": "pass123"})
    assert r_register.status_code == 201

    # Login con credenciales válidas debe devolver 200 sin token
    r_login = client.post("/api/v1/auth/login", data={"username": "usuario_publico", "password": "pass123"})
    assert r_login.status_code == 200

def test_health_check(client):
    """/health responde 200 sin token y confirma que la base de datos está accesible"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_login_se_bloquea_tras_varios_intentos_fallidos(client):
    """Tras 5 intentos fallidos seguidos, el login se bloquea aunque la contraseña sea correcta"""
    client.post("/api/v1/auth/register", json={"email": "usuario_bloqueo", "password": "correcta123"})

    for _ in range(5):
        r = client.post("/api/v1/auth/login", data={"username": "usuario_bloqueo", "password": "incorrecta"})
        assert r.status_code == 401

    r_bloqueado = client.post("/api/v1/auth/login", data={"username": "usuario_bloqueo", "password": "correcta123"})
    assert r_bloqueado.status_code == 429


# ── Recuperación de contraseña ──────────────────────────────────────────────────

def _pedir_codigo(client, email):
    captured = {}

    def fake_send(self, to_email, code):
        captured["code"] = code
        return True

    with patch("app.services.email_service.EmailService.send_password_reset_code", fake_send):
        response = client.post("/api/v1/auth/forgot-password", json={"email": email})
    return response, captured.get("code")

def test_forgot_password_y_reset_exitoso(client):
    client.post("/api/v1/auth/register", json={"email": "recupero@example.com", "password": "vieja123"})

    r_forgot, code = _pedir_codigo(client, "recupero@example.com")
    assert r_forgot.status_code == 200
    assert code is not None and len(code) == 6

    r_reset = client.post("/api/v1/auth/reset-password", json={
        "email": "recupero@example.com",
        "code": code,
        "new_password": "nueva123",
    })
    assert r_reset.status_code == 200

    r_login_vieja = client.post("/api/v1/auth/login", data={"username": "recupero@example.com", "password": "vieja123"})
    assert r_login_vieja.status_code == 401

    r_login_nueva = client.post("/api/v1/auth/login", data={"username": "recupero@example.com", "password": "nueva123"})
    assert r_login_nueva.status_code == 200

def test_reset_password_codigo_invalido(client):
    client.post("/api/v1/auth/register", json={"email": "recupero2@example.com", "password": "vieja123"})
    _pedir_codigo(client, "recupero2@example.com")

    r_reset = client.post("/api/v1/auth/reset-password", json={
        "email": "recupero2@example.com",
        "code": "000000",
        "new_password": "nueva123",
    })
    assert r_reset.status_code == 400

def test_forgot_password_email_inexistente_no_filtra_info(client):
    """Responde 200 igual si el email no existe: no hay que revelar qué emails están registrados"""
    response = client.post("/api/v1/auth/forgot-password", json={"email": "no_existe@example.com"})
    assert response.status_code == 200
    assert "message" in response.json()

def test_reset_password_no_reutiliza_codigo(client):
    client.post("/api/v1/auth/register", json={"email": "recupero3@example.com", "password": "vieja123"})
    _, code = _pedir_codigo(client, "recupero3@example.com")

    r1 = client.post("/api/v1/auth/reset-password", json={
        "email": "recupero3@example.com", "code": code, "new_password": "nueva123"
    })
    assert r1.status_code == 200

    r2 = client.post("/api/v1/auth/reset-password", json={
        "email": "recupero3@example.com", "code": code, "new_password": "otra456"
    })
    assert r2.status_code == 400