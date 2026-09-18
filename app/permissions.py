"""
Capacidades del panel de administración que se le pueden asignar a un rol.

El rol 'admin' siempre tiene todas (ver User.has_permission) — esta lista es
para los roles personalizados que se crean desde /admin/roles.
"""

PERMISSIONS = [
    {"key": "messages", "label": "Mensajes"},
    {"key": "metrics", "label": "Métricas"},
    {"key": "users", "label": "Usuarios"},
    {"key": "roles", "label": "Roles"},
    {"key": "limits", "label": "Límites"},
]

PERMISSION_KEYS = {p["key"] for p in PERMISSIONS}
