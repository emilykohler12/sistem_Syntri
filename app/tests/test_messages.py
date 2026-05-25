import pytest
from unittest.mock import patch, MagicMock

def test_enviar_mensaje_sin_token(client):
    """Enviar mensaje sin token debe devolver 401"""
    response = client.post("/api/v1/messages/", json={
        "content": "Hola",
        "destinations": ["slack"]
    })
    assert response.status_code == 401

def test_enviar_mensaje_destino_invalido(client, user_token):
    """Enviar mensaje a destino inválido debe devolver 400"""
    response = client.post(
        "/api/v1/messages/",
        json={
            "content": "Hola",
            "destinations": ["whatsapp"]
        },
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400

def test_enviar_mensaje_exitoso(client, user_token):
    """Enviar mensaje válido debe devolver 201"""
    with patch("app.services.slack_service.SlackService.send") as mock_slack, \
         patch("app.services.discord_service.DiscordService.send") as mock_discord:
        
        mock_slack.return_value = {"status": "success", "provider_response": "ok"}
        mock_discord.return_value = {"status": "success", "provider_response": "Mensaje enviado correctamente"}
        
        response = client.post(
            "/api/v1/messages/",
            json={
                "content": "Hola desde el test",
                "destinations": ["slack", "discord"]
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Hola desde el test"
    assert len(data["deliveries"]) == 2

def test_ver_mis_mensajes(client, user_token):
    """Usuario debe poder ver sus propios mensajes"""
    with patch("app.services.slack_service.SlackService.send") as mock_slack:
        mock_slack.return_value = {"status": "success", "provider_response": "ok"}
        client.post(
            "/api/v1/messages/",
            json={"content": "Mensaje de prueba", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    
    response = client.get(
        "/api/v1/messages/",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

def test_rate_limit(client, user_token):
    """Superar el límite diario debe devolver 429"""
    with patch("app.services.slack_service.SlackService.send") as mock_slack:
        mock_slack.return_value = {"status": "success", "provider_response": "ok"}
        
        for i in range(100):
            client.post(
                "/api/v1/messages/",
                json={"content": f"Mensaje {i}", "destinations": ["slack"]},
                headers={"Authorization": f"Bearer {user_token}"}
            )
        
        response = client.post(
            "/api/v1/messages/",
            json={"content": "Mensaje 101", "destinations": ["slack"]},
            headers={"Authorization": f"Bearer {user_token}"}
        )
    
    assert response.status_code == 429

def test_admin_ve_metricas(client, admin_token):
    """Admin debe poder ver métricas"""
    response = client.get(
        "/api/v1/admin/metrics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

def test_user_no_puede_ver_metricas(client, user_token):
    """Usuario normal no debe poder ver métricas de admin"""
    response = client.get(
        "/api/v1/admin/metrics",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403