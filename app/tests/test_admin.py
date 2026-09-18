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
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
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
    # Con retry son 3 intentos fallidos (MAX_RETRIES=3)
    assert testuser["deliveries"]["failed"] == 3

def test_metricas_diarias(client, admin_token):
    """Métricas diarias devuelven estructura correcta"""
    response = client.get("/api/v1/admin/metrics/daily", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_success_rate(client, admin_token, user_token):
    """Verifica que successful + failed = total deliveries"""
    with patch("app.services.message_service.MessageService.check_and_increment", return_value=1), \
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
    client.post("/api/v1/auth/register", json={"email": "usuario_a_cancelar", "password": "pass123"})
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
    client.post("/api/v1/auth/register", json={"email": "usuario_reactivar", "password": "pass123"})
    client.patch("/api/v1/admin/users/usuario_reactivar/cancel", headers={"Authorization": f"Bearer {admin_token}"})
    response = client.patch(
        "/api/v1/admin/users/usuario_reactivar/reactivate",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] == True

def test_reactivar_usuario_ya_activo(client, admin_token):
    client.post("/api/v1/auth/register", json={"email": "usuario_activo", "password": "pass123"})
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


# ── Roles y permisos ─────────────────────────────────────────────────────────

def test_listar_permisos_disponibles(client, admin_token):
    response = client.get("/api/v1/admin/permissions", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    keys = {p["key"] for p in response.json()}
    assert keys == {"messages", "metrics", "users", "roles", "limits"}

def test_rol_nuevo_arranca_sin_permisos(client, admin_token):
    response = client.post(
        "/api/v1/admin/roles?name=moderador&description=Rol de prueba",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    roles = client.get("/api/v1/admin/roles", headers={"Authorization": f"Bearer {admin_token}"}).json()
    moderador = next(r for r in roles if r["name"] == "moderador")
    assert moderador["permissions"] == []

def test_asignar_rol_a_un_usuario(client, admin_token, user_token):
    client.post("/api/v1/admin/roles?name=moderador", headers={"Authorization": f"Bearer {admin_token}"})
    response = client.patch(
        "/api/v1/admin/users/testuser/role",
        json={"role_name": "moderador"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "moderador"

def test_rol_sin_permisos_no_accede_a_nada_del_admin(client, admin_token, user_token):
    client.post("/api/v1/admin/roles?name=moderador", headers={"Authorization": f"Bearer {admin_token}"})
    client.patch(
        "/api/v1/admin/users/testuser/role",
        json={"role_name": "moderador"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    response = client.get("/api/v1/admin/roles", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

def test_rol_con_permiso_de_roles_solo_accede_a_roles(client, admin_token, user_token):
    """Un rol al que solo se le asignó 'roles' puede leer /admin/roles pero no /admin/messages"""
    client.post("/api/v1/admin/roles?name=moderador", headers={"Authorization": f"Bearer {admin_token}"})
    perm_response = client.patch(
        "/api/v1/admin/roles/moderador/permissions",
        json={"permissions": ["roles"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert perm_response.status_code == 200
    assert perm_response.json()["permissions"] == ["roles"]

    client.patch(
        "/api/v1/admin/users/testuser/role",
        json={"role_name": "moderador"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    r_roles = client.get("/api/v1/admin/roles", headers={"Authorization": f"Bearer {user_token}"})
    assert r_roles.status_code == 200

    r_messages = client.get("/api/v1/admin/messages", headers={"Authorization": f"Bearer {user_token}"})
    assert r_messages.status_code == 403

def test_no_se_puede_editar_permisos_del_rol_admin(client, admin_token):
    response = client.patch(
        "/api/v1/admin/roles/admin/permissions",
        json={"permissions": ["messages"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_permisos_invalidos_se_rechazan(client, admin_token):
    client.post("/api/v1/admin/roles?name=moderador2", headers={"Authorization": f"Bearer {admin_token}"})
    response = client.patch(
        "/api/v1/admin/roles/moderador2/permissions",
        json={"permissions": ["algo_que_no_existe"]},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400

def test_admin_no_puede_quitarse_su_propio_rol(client, admin_token, admin_user):
    response = client.patch(
        f"/api/v1/admin/users/{admin_user['username']}/role",
        json={"role_name": "user"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400