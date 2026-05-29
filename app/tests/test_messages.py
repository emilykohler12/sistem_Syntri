import pytest
from unittest.mock import patch

MOCK_SUCCESS = {"status": "success", "provider_response": "ok"}
MOCK_FAILED  = {"status": "failed",  "provider_response": "Error de conexión"}


# ── Validaciones ──────────────────────────────────────────────────────────────

def test_enviar_mensaje_sin_token(client):
    response = client.post("/api/v1/messages/", json={"content": "Hola", "destinations": ["slack"]})
    assert response.status_code == 401

def test_enviar_mensaje_vacio(client, user_token):
    """Mensaje vacío devuelve 400"""
    response = client.post(
        "/api/v1/messages/",
        json={"content": "", "destinations": ["slack"]},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400

def test_enviar_mensaje_solo_espacios(client, user_token):
    """Mensaje con solo espacios devuelve 400"""
    response = client.post(
        "/api/v1/messages/",
        json={"content": "   ", "destinations": ["slack"]},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400

def test_enviar_mensaje_destinos_vacios(client, user_token):
    """Lista de destinos vacía devuelve 400"""
    response = client.post(
        "/api/v1/messages/",
        json={"content": "Hola", "destinations": []},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400

def test_enviar_mensaje_destino_string_vacio(client, user_token):
    """Destino con string vacío devuelve 400"""
    response = client.post(
        "/api/v1/messages/",
        json={"content": "Hola", "destinations": [""]},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400


# ── Envío exitoso ─────────────────────────────────────────────────────────────

def test_enviar_mensaje_exitoso(client, user_token):
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS), \
         patch("app.services.discord_service.DiscordService.send", return_value=MOCK_SUCCESS):
        response = client.post(
            "/api/v1/messages/",
            json={"content": "Hola desde el test", "destinations": ["slack", "discord"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hola desde el test"
    assert len(data["deliveries"]) == 2
    assert all(d["status"] == "success" for d in data["deliveries"])


# ── Deliveries fallidas ───────────────────────────────────────────────────────

def test_delivery_fallida_se_guarda(client, user_token):
    """Un fallo en el envío se registra como failed, no tira 500"""
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_FAILED):
        response = client.post(
            "/api/v1/messages/",
            json={"content": "Test fallo", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 201
    data = response.json()
    assert data["deliveries"][0]["status"] == "failed"

def test_destino_desconocido_se_guarda_como_failed(client, user_token):
    """Destino desconocido se guarda como failed sin bloquear la respuesta"""
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1):
        response = client.post(
            "/api/v1/messages/",
            json={"content": "Test destino raro", "destinations": ["telegram"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 201
    assert response.json()["deliveries"][0]["status"] == "failed"

def test_fallo_en_un_destino_no_bloquea_el_otro(client, user_token):
    """Si slack falla, discord igual se intenta y viceversa"""
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_FAILED), \
         patch("app.services.discord_service.DiscordService.send", return_value=MOCK_SUCCESS):
        response = client.post(
            "/api/v1/messages/",
            json={"content": "Test mixto", "destinations": ["slack", "discord"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 201
    statuses = {d["service"]: d["status"] for d in response.json()["deliveries"]}
    assert statuses["slack"] == "failed"
    assert statuses["discord"] == "success"


# ── Rate limiting ─────────────────────────────────────────────────────────────

def test_rate_limit_configurable(client, user_token, admin_token):
    """El límite diario se respeta según la config de la BD"""
    # Bajar el límite global a 2 para no hacer 100 requests en el test
    client.patch(
        "/api/v1/admin/limits/global?new_limit=2",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS):
        for _ in range(2):
            client.post(
                "/api/v1/messages/",
                json={"content": "msg", "destinations": ["slack"]},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        response = client.post(
            "/api/v1/messages/",
            json={"content": "msg 3", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 429

def test_limite_personalizado_por_usuario(client, user_token, admin_token):
    """Un usuario con límite personalizado lo respeta"""
    client.patch(
        "/api/v1/admin/limits/user/testuser?new_limit=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    with patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS):
        client.post(
            "/api/v1/messages/",
            json={"content": "msg 1", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        response = client.post(
            "/api/v1/messages/",
            json={"content": "msg 2", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    assert response.status_code == 429


# ── Ver mensajes ──────────────────────────────────────────────────────────────

def test_ver_mis_mensajes(client, user_token):
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
         patch("app.services.slack_service.SlackService.send", return_value=MOCK_SUCCESS):
        client.post(
            "/api/v1/messages/",
            json={"content": "Mensaje de prueba", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    response = client.get("/api/v1/messages/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 1