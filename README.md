# Sistem Syntri

API REST para el envío centralizado de notificaciones a múltiples plataformas de comunicación.

Desarrollado por **Emily Noralí Kohler** como práctica de 5° año de Ingeniería en Sistemas de Información en **Sirius Software**.

---

## Descripción

Sistem Syntri permite a usuarios registrados enviar mensajes a Discord y Slack desde un único endpoint. El sistema incluye autenticación con JWT, control de roles, límites diarios configurables, reintentos automáticos y un panel de administración completo.

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
ENVIRONMENT=development
```

> Para generar una `SECRET_KEY` segura:
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 4. Crear la base de datos y correr migraciones

```bash
alembic upgrade head
```

### 5. Crear el usuario admin inicial

```bash
python create_admin.py
```

Credenciales por defecto:
- **Usuario:** `admin`
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

## Endpoints principales

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario |
| `POST` | `/api/v1/auth/login` | Iniciar sesión (devuelve JWT) |

### Mensajes

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/v1/messages/` | Enviar mensaje a Discord y/o Slack |
| `GET` | `/api/v1/messages/` | Listar mis mensajes con filtros |

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

El proyecto incluye 42 tests que cubren autenticación, envío de mensajes, rate limiting, métricas, permisos y manejo de errores.

---

## Arquitectura

El sistema sigue el patrón **Router → Service → Repository**:

- **Routers** (`app/routers/`) — reciben el request HTTP y devuelven la respuesta
- **Services** (`app/services/`) — contienen la lógica de negocio
- **Repositories** (`app/repositories/`) — acceso a la base de datos

**Patrones de diseño aplicados:**
- **Strategy** — `NotificationService` como clase base abstracta implementada por `SlackService` y `DiscordService`
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