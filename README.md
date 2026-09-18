# Sistem Syntri

API REST para el envío centralizado de notificaciones a múltiples plataformas de comunicación.

Desarrollado por **Emily Noralí Kohler** como práctica de 5° año de Ingeniería en Sistemas de Información en **Sirius Software**.

---

## Descripción

Sistem Syntri permite a usuarios registrados enviar mensajes a Discord, Slack y Telegram desde un único endpoint. El sistema incluye autenticación con JWT, control de roles, límites diarios configurables, reintentos automáticos y un panel de administración completo.

---

## Tecnologías

- **Python 3.12**
- **FastAPI** — framework web
- **PostgreSQL** — base de datos principal
- **SQLAlchemy** — ORM
- **Alembic** — migraciones de base de datos
- **JWT (python-jose)** — autenticación
- **Swagger UI** — documentación interactiva
- **Docker / Docker Compose** — contenedorización
- **pytest** — tests unitarios
- **GitHub Actions** — CI/CD

---

## Requisitos

- Python 3.12+
- PostgreSQL 15+
- pip

---

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/emilykohler12/sistem_Syntri
cd sistem-syntri
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

# Opcionales: si no se configuran, el código de recuperación de contraseña
# queda logueado en la consola del servidor en vez de enviarse por email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_contraseña_de_aplicación
SMTP_FROM=tu_email@gmail.com
```

> Para generar una `SECRET_KEY` segura:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

> Cómo conseguir `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`:
> 1. Hablá con [@BotFather](https://t.me/BotFather) en Telegram, mandale `/newbot` y seguí los pasos. Te da un token tipo `123456789:ABCdefGhIJKlmNoPQRsTUVwxyz`.
> 2. Iniciá una conversación con tu bot recién creado (buscalo por el username que le pusiste) y mandale cualquier mensaje.
> 3. Abrí `https://api.telegram.org/bot<TU_TOKEN>/getUpdates` en el navegador y buscá `"chat":{"id":...}` en la respuesta — ese número es el `TELEGRAM_CHAT_ID`.
> 4. Para mandar a un grupo en vez de a vos: agregá el bot al grupo, mandá un mensaje ahí, y repetí el paso 3 (el chat_id de un grupo es negativo).

### 4. Crear la base de datos y correr migraciones

```bash
alembic upgrade head
```

### 5. Crear el usuario admin inicial

```bash
python create_admin.py
```

Credenciales por defecto:
- **Email:** `admin@syntri.local`
- **Contraseña:** `admin123`

> Se recomienda cambiar la contraseña después del primer login.

### 6. Levantar la aplicación

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`
Swagger UI en `http://localhost:8000/docs`

---

## Docker

### Levantar con Docker Compose

```bash
cp .env.example .env   # completar valores
docker compose up --build
```

Esto levanta la base de datos PostgreSQL y la API juntas.

---

## Frontend

El panel web vive en [`frontend/`](frontend/) (Vue 3 + TypeScript + Vite + Tailwind). Con el backend corriendo en `http://localhost:8000`:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Queda disponible en `http://localhost:5173`. Incluye login/registro, envío de mensajes con historial propio, y un panel de administración (usuarios, roles, límites diarios y auditoría, métricas). Ver [`frontend/README.md`](frontend/README.md) para más detalle.

---

## Endpoints principales

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario (con email) |
| `POST` | `/api/v1/auth/login` | Iniciar sesión con email (devuelve JWT) |
| `POST` | `/api/v1/auth/forgot-password` | Pedir código de 6 dígitos por email |
| `POST` | `/api/v1/auth/reset-password` | Cambiar contraseña con el código |

### Mensajes

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/messages/` | Enviar mensaje a Discord, Slack y/o Telegram |
| `GET` | `/api/v1/messages/` | Listar mis mensajes con filtros, paginado |

### Admin

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/admin/messages` | Listar todos los mensajes |
| `GET` | `/api/v1/admin/metrics` | Métricas por usuario |
| `GET` | `/api/v1/admin/metrics/daily` | Métricas diarias |
| `POST` | `/api/v1/admin/users/promote` | Promover usuario a admin |
| `PATCH` | `/api/v1/admin/users/{username}/cancel` | Cancelar usuario |
| `PATCH` | `/api/v1/admin/users/{username}/reactivate` | Reactivar usuario |
| `GET` | `/api/v1/admin/roles` | Listar roles |
| `POST` | `/api/v1/admin/roles` | Crear rol |
| `DELETE` | `/api/v1/admin/roles/{name}` | Eliminar rol |
| `GET` | `/api/v1/admin/limits` | Ver límites |
| `PATCH` | `/api/v1/admin/limits/global` | Cambiar límite global |
| `PATCH` | `/api/v1/admin/limits/user/{username}` | Cambiar límite por usuario |
| `GET` | `/api/v1/admin/limits/audit` | Historial de cambios |

---

## Tests

```bash
pytest app/tests/ -v
```

El proyecto incluye 50 tests que cubren autenticación, recuperación de contraseña, envío de mensajes, rate limiting, métricas, permisos y manejo de errores.

---

## Arquitectura

El sistema sigue el patrón **Router → Service → Repository**:

- **Routers** (`app/routers/`) — reciben el request HTTP y devuelven la respuesta
- **Services** (`app/services/`) — contienen la lógica de negocio
- **Repositories** (`app/repositories/`) — acceso a la base de datos

**Patrones de diseño aplicados:**
- **Strategy** — `NotificationService` como clase base abstracta implementada por `SlackService`, `DiscordService` y `TelegramService`
- **Factory** — diccionario `AVAILABLE_SERVICES` que instancia el servicio según el destino
- **Middleware chain** — autenticación, logging, seguridad HTTP y rate limit encadenados

---

## CI/CD

GitHub Actions corre los tests automáticamente en cada push a `main` o `develop`.
Ver `.github/workflows/tests.yml`.

---

## Estructura del proyecto

```
sistem_Syntri/
├── app/
│   ├── routers/          # Endpoints HTTP
│   ├── services/         # Lógica de negocio
│   ├── repositories/     # Acceso a la BD
│   ├── tests/            # Tests unitarios
│   ├── auth.py           # JWT y permisos
│   ├── models.py         # Modelos SQLAlchemy
│   ├── schemas.py        # Schemas Pydantic
│   ├── database.py       # Configuración BD
│   └── main.py           # Middlewares y app
├── alembic/              # Migraciones
├── .github/workflows/    # CI/CD
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── create_admin.py
└── requirements.txt
```