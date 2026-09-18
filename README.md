# Sistem Syntri

API REST para el envío centralizado de notificaciones a múltiples plataformas de comunicación, con panel de administración y control de acceso por roles.

Creado por [Emily Kohler](https://github.com/emilykohler12).

🔗 **Demo en vivo**: [sistem-syntri.vercel.app](https://sistem-syntri.vercel.app/)

Para probarla, iniciá sesión con la cuenta de admin:
- **Email:** `admin@syntri.local`
- **Contraseña:** `admin123`

---

## Descripción

Sistem Syntri permite a usuarios registrados enviar mensajes a Slack, Discord y Telegram desde un único endpoint, con reintentos automáticos ante fallos. Incluye autenticación por email con JWT, recuperación de contraseña por código, límites diarios de envío (globales y por usuario, con auditoría de cambios) y un sistema de roles con permisos configurables por sección del panel de administración.

---

## Funcionalidades

- **Envío multiplataforma**: Slack, Discord y Telegram desde un mismo endpoint, con reintentos automáticos y registro de cada intento.
- **Autenticación por email**: registro y login con JWT; recuperación de contraseña con código de 6 dígitos enviado por email.
- **Roles y permisos**: cada rol puede tener acceso a secciones específicas del panel (mensajes, métricas, usuarios, roles, límites), asignables individualmente.
- **Límites configurables**: límite diario global y por usuario, con historial de auditoría de cada cambio.
- **Panel de administración**: métricas con gráficos, gestión de usuarios y roles, y consulta de mensajes con filtros y paginación.
- **Seguridad**: rate limiting por IP, bloqueo temporal tras intentos fallidos de login, headers de seguridad HTTP, manejo centralizado de excepciones.

---

## Tecnologías

**Backend**
- **Python 3.12** + **FastAPI**
- **PostgreSQL** + **SQLAlchemy** + **Alembic**
- **JWT (python-jose)** — autenticación
- **Docker / Docker Compose**
- **pytest** — tests automatizados
- **GitHub Actions** — CI/CD

**Frontend**
- **Vue 3** + **TypeScript** + **Vite**
- **Tailwind CSS**

---

## Requisitos

- Python 3.12+
- PostgreSQL 15+
- Node.js 20+ (para el frontend)

---

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/emilykohler12/sistem_Syntri
cd sistem_Syntri
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copiá el archivo de ejemplo y completá los valores:

```bash
cp .env.example .env
```

Variables requeridas en `.env`:

```
DATABASE_URL=postgresql+psycopg://postgres:tu_password@localhost:5432/sistemasyntri
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password
POSTGRES_DB=sistemasyntri
SECRET_KEY=tu_clave_secreta
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_BOT_TOKEN=tu_token
DISCORD_CHANNEL_ID=tu_channel_id
TELEGRAM_BOT_TOKEN=tu_token_de_botfather
TELEGRAM_CHAT_ID=tu_chat_id
ENVIRONMENT=development

# Opcionales: sin esto, el código de recuperación de contraseña
# queda logueado en la consola del servidor en vez de enviarse por email
BREVO_API_KEY=tu_api_key_de_brevo
BREVO_FROM_EMAIL=tu_email_verificado@ejemplo.com
BREVO_FROM_NAME=System Syntri
```

<details>
<summary>Cómo generar una <code>SECRET_KEY</code> segura</summary>

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
</details>

<details>
<summary>Cómo conseguir <code>TELEGRAM_BOT_TOKEN</code> y <code>TELEGRAM_CHAT_ID</code></summary>

1. Hablá con [@BotFather](https://t.me/BotFather) en Telegram, mandale `/newbot` y seguí los pasos. Te da un token tipo `123456789:ABCdefGhIJKlmNoPQRsTUVwxyz`.
2. Iniciá una conversación con tu bot recién creado y mandale cualquier mensaje.
3. Abrí `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` y buscá `"chat":{"id":...}` en la respuesta — ese número es el `TELEGRAM_CHAT_ID`.
4. Para mandar a un grupo en vez de a un usuario: agregá el bot al grupo, mandá un mensaje ahí, y repetí el paso 3 (el chat_id de un grupo es negativo).
</details>

### 4. Crear la base de datos y correr migraciones

```bash
alembic upgrade head
```

### 5. Usuario admin inicial

La app lo crea sola la primera vez que arranca (no hace falta correr nada a mano, ni tener acceso a una shell en el hosting). Si querés forzarlo manualmente igual podés correr:

```bash
python create_admin.py
```

Credenciales por defecto:
- **Email:** `admin@syntri.local`
- **Contraseña:** `admin123`

Se pueden cambiar antes del primer deploy con las variables `ADMIN_EMAIL` y `ADMIN_PASSWORD`. Se recomienda cambiar la contraseña después del primer login si se dejaron las de por defecto.

### 6. Levantar la aplicación

```bash
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`, con Swagger UI en `http://localhost:8000/docs`.

---

## Docker

```bash
cp .env.example .env   # completar valores
docker compose up --build
```

Esto levanta la base de datos PostgreSQL y la API juntas.

---

## Deploy

- **Backend**: [Render](https://render.com) detecta el `Dockerfile` del repo automáticamente. Configurar las variables de entorno de `.env.example` (con `ENVIRONMENT=production` y `FRONTEND_ORIGINS` apuntando a la URL del frontend).
- **Frontend**: [Vercel](https://vercel.com) o [Netlify](https://netlify.com), apuntando `VITE_API_URL` a la URL de Render.

---

## Frontend

Panel web en [`frontend/`](frontend/) (Vue 3 + TypeScript + Vite + Tailwind CSS). Con el backend corriendo en `http://localhost:8000`:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Queda disponible en `http://localhost:5173`. Incluye login/registro por email, recuperación de contraseña, envío de mensajes con historial y filtros, y un panel de administración completo: métricas con gráficos, gestión de usuarios y roles con permisos configurables, y auditoría de límites. Ver [`frontend/README.md`](frontend/README.md) para más detalle.

---

## Endpoints principales

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario con email |
| `POST` | `/api/v1/auth/login` | Iniciar sesión con email (devuelve JWT) |
| `POST` | `/api/v1/auth/forgot-password` | Pedir código de 6 dígitos por email |
| `POST` | `/api/v1/auth/reset-password` | Cambiar contraseña con el código |

### Mensajes

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/messages/` | Enviar mensaje a Slack, Discord y/o Telegram |
| `GET` | `/api/v1/messages/` | Listar mis mensajes con filtros, paginado |

### Admin

| Método | Ruta | Descripción | Permiso requerido |
|--------|------|-------------|--------------------|
| `GET` | `/api/v1/admin/messages` | Listar todos los mensajes | `messages` |
| `GET` | `/api/v1/admin/metrics` | Métricas por usuario | `metrics` |
| `GET` | `/api/v1/admin/metrics/daily` | Métricas diarias | `metrics` |
| `POST` | `/api/v1/admin/users/promote` | Promover usuario a admin | `users` |
| `PATCH` | `/api/v1/admin/users/{username}/role` | Asignar cualquier rol a un usuario | `users` |
| `PATCH` | `/api/v1/admin/users/{username}/cancel` | Cancelar usuario | `users` |
| `PATCH` | `/api/v1/admin/users/{username}/reactivate` | Reactivar usuario | `users` |
| `GET` | `/api/v1/admin/roles` | Listar roles | `roles` o `users` |
| `POST` | `/api/v1/admin/roles` | Crear rol | `roles` |
| `PATCH` | `/api/v1/admin/roles/{role_name}/permissions` | Definir permisos de un rol | `roles` |
| `DELETE` | `/api/v1/admin/roles/{name}` | Eliminar rol | `roles` |
| `GET` | `/api/v1/admin/permissions` | Listar permisos disponibles | `roles` |
| `GET` | `/api/v1/admin/limits` | Ver límites | `limits` |
| `PATCH` | `/api/v1/admin/limits/global` | Cambiar límite global | `limits` |
| `PATCH` | `/api/v1/admin/limits/user/{username}` | Cambiar límite por usuario | `limits` |
| `GET` | `/api/v1/admin/limits/audit` | Historial de cambios de límites | `limits` |

El rol `admin` tiene todos los permisos siempre. Los demás roles solo acceden a las secciones que se les hayan asignado explícitamente desde el panel de Roles.

---

## Tests

```bash
pytest app/tests/ -v
```

El proyecto incluye 59 tests que cubren autenticación, recuperación de contraseña, envío de mensajes, rate limiting, permisos por rol, límites y auditoría, y manejo de errores.

---

## Arquitectura

El backend sigue el patrón **Router → Service → Repository**:

- **Routers** (`app/routers/`) — reciben el request HTTP y devuelven la respuesta
- **Services** (`app/services/`) — contienen la lógica de negocio
- **Repositories** (`app/repositories/`) — acceso a la base de datos

**Patrones de diseño aplicados:**
- **Strategy** — `NotificationService` como clase base abstracta implementada por `SlackService`, `DiscordService` y `TelegramService`
- **Factory** — diccionario `AVAILABLE_SERVICES` que instancia el servicio según el destino
- **Middleware chain** — CORS, autenticación, logging, seguridad HTTP y rate limit encadenados
- **RBAC por permisos** — cada rol tiene una lista de capacidades (`app/permissions.py`); `require_permission()` protege cada endpoint del panel de administración según la capacidad que necesita

---

## CI/CD

GitHub Actions corre los tests automáticamente en cada push a `main` o `develop`. Ver `.github/workflows/tests.yml`.

---

## Estructura del proyecto

```
sistem_Syntri/
├── app/
│   ├── routers/          # Endpoints HTTP
│   ├── services/         # Lógica de negocio
│   ├── repositories/     # Acceso a la BD
│   ├── tests/             # Tests automatizados
│   ├── auth.py            # JWT y permisos
│   ├── permissions.py     # Capacidades asignables a un rol
│   ├── models.py          # Modelos SQLAlchemy
│   ├── schemas.py         # Schemas Pydantic
│   ├── database.py        # Configuración BD
│   └── main.py            # Middlewares y app
├── alembic/               # Migraciones
├── frontend/               # Panel web (Vue 3 + TypeScript)
├── .github/workflows/      # CI/CD
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── create_admin.py
└── requirements.txt
```
