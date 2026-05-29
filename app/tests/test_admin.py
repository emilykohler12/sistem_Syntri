import pytest
from unittest.mock import patch

MOCK_SUCCESS = {"status": "success", "provider_response": "ok"}
MOCK_FAILED  = {"status": "failed",  "provider_response": "Error"}


# ── Permisos ──────────────────────────────────────────────────────────────────

def test_user_no_puede_ver_metricas(client, user_token):
    response = client.get("/api/v1/admin/metrics", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

def test_user_no_puede_ver_mensajes_admin(client, user_token):
    response = client.get("/api/v1/admin/messages", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

def test_user_no_puede_cambiar_limites(client, user_token):
    response = client.patch("/api/v1/admin/limits/global?new_limit=50", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

def test_user_no_puede_cancelar_usuarios(client, user_token):
    response = client.patch("/api/v1/admin/users/alguien/cancel", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403


# ── Métricas ──────────────────────────────────────────────────────────────────

def test_admin_ve_metricas(client, admin_token):
    response = client.get("/api/v1/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

def test_metricas_incluyen_deliveries(client, admin_token, user_token):
    """Las métricas muestran deliveries exitosas y fallidas por usuario"""
    with patch("app.routers.messages._check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS), \
         patch("app.services.discord_service.DiscordService.send", return_value=MOCK_FAILED):
        client.post(
            "/api/v1/messages/",
            json={"content": "test", "destinations": ["slack", "discord"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

    response = client.get("/api/v1/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    users = response.json()
    testuser = next((u for u in users if u["username"] == "testuser"), None)
    assert testuser is not None
    assert testuser["deliveries"]["successful"] == 1
    assert testuser["deliveries"]["failed"] == 1

def test_metricas_diarias(client, admin_token):
    """Métricas diarias devuelven estructura correcta"""
    response = client.get("/api/v1/admin/metrics/daily", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_success_rate(client, admin_token, user_token):
    """Verifica que successful + failed = total deliveries"""
    with patch("app.routers.messages._check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS), \
         patch("app.services.discord_service.DiscordService.send", return_value=MOCK_FAILED):
        client.post(
            "/api/v1/messages/",
            json={"content": "test rate", "destinations": ["slack", "discord"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )

    metrics = client.get("/api/v1/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"}).json()
    user = next(u for u in metrics if u["username"] == "testuser")
    d = user["deliveries"]
    assert d["successful"] + d["failed"] == d["total"]


# ── Gestión de usuarios ───────────────────────────────────────────────────────

def test_cancelar_usuario(client, admin_token):
    client.post("/api/v1/auth/register", json={"username": "usuario_a_cancelar", "password": "pass123"})
    response = client.patch(
        "/api/v1/admin/users/usuario_a_cancelar/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] == False

def test_cancelar_usuario_inexistente(client, admin_token):
    response = client.patch(
        "/api/v1/admin/users/noexiste/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_cancelar_propio_usuario_admin(client, admin_token):
    """El admin no puede cancelar su propia cuenta"""
    response = client.patch(
        "/api/v1/admin/users/admin_test/cancel",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_reactivar_usuario(client, admin_token):
    client.post("/api/v1/auth/register", json={"username": "usuario_reactivar", "password": "pass123"})
    client.patch("/api/v1/admin/users/usuario_reactivar/cancel", headers={"Authorization": f"Bearer {admin_token}"})
    response = client.patch(
        "/api/v1/admin/users/usuario_reactivar/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] == True

def test_reactivar_usuario_ya_activo(client, admin_token):
    client.post("/api/v1/auth/register", json={"username": "usuario_activo", "password": "pass123"})
    response = client.patch(
        "/api/v1/admin/users/usuario_activo/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409


# ── Límites ───────────────────────────────────────────────────────────────────

def test_cambiar_limite_global(client, admin_token):
    response = client.patch(
        "/api/v1/admin/limits/global?new_limit=200",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["new_limit"] == 200

def test_limite_global_invalido(client, admin_token):
    response = client.patch(
        "/api/v1/admin/limits/global?new_limit=0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_auditoria_registra_cambio(client, admin_token):
    client.patch("/api/v1/admin/limits/global?new_limit=150", headers={"Authorization": f"Bearer {admin_token}"})
    response = client.get("/api/v1/admin/limits/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    audit = response.json()
    assert len(audit) >= 1
    assert audit[0]["new_limit"] == 150