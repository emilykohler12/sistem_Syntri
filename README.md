# Syntri 🔔

Syntri es una API REST desarrollada con FastAPI que permite enviar notificaciones a múltiples plataformas de comunicación desde un único punto centralizado.

Actualmente soporta integraciones con Slack y Discord, permitiendo gestionar mensajes, autenticación, métricas y control de acceso mediante roles.

---

# 🚀 Características

- Autenticación con JWT
- Roles de usuario (`user` y `admin`)
- Envío de mensajes multi-plataforma
- Persistencia de mensajes y entregas
- Rate limiting por usuario
- Métricas y estadísticas
- Documentación automática con Swagger
- Docker support

---

# 🛠 Stack Tecnológico

- **Python 3.12**
- **FastAPI** — framework para la API REST
- **PostgreSQL** — base de datos relacional
- **SQLAlchemy** — ORM para acceso a datos
- **JWT** — autenticación y autorización
- **Docker** — containerización
- **Pytest** — testing

---

# 🔗 Integraciones

- ✅ Slack (Incoming Webhooks)
- ✅ Discord (Bot API)

---

# 📋 Requisitos

- Python 3.12+
- PostgreSQL
- pip
- Docker (opcional)

---

# ⚙️ Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/emilykohler12/sistema_Syntri.git
cd sistema_Syntri
```

---

## 2. Crear entorno virtual

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
DATABASE_URL=postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/syntri
SECRET_KEY=tu_clave_secreta_super_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

SLACK_WEBHOOK_URL=tu_slack_webhook

DISCORD_BOT_TOKEN=tu_discord_bot_token
DISCORD_CHANNEL_ID=tu_discord_channel_id
```

---

## 5. Crear la base de datos

Crear una base de datos llamada:

```text
syntri
```

---

## 6. Crear usuario administrador

```bash
python create_admin.py
```

---

## 7. Ejecutar la API

```bash
uvicorn app.main:app --reload
```

La API estará disponible en:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

---

# 🐳 Ejecutar con Docker

```bash
docker-compose up --build
```

---

# 🧪 Tests

```bash
pytest app/tests/ -v
```

---

# 📌 Endpoints Principales

| Método | Endpoint | Descripción | Acceso |
|--------|----------|-------------|---------|
| POST | `/api/v1/auth/register` | Registrar usuario | Público |
| POST | `/api/v1/auth/login` | Iniciar sesión | Público |
| POST | `/api/v1/messages/` | Enviar mensaje | User/Admin |
| GET | `/api/v1/messages/` | Obtener mis mensajes | User/Admin |
| GET | `/api/v1/admin/messages` | Obtener todos los mensajes | Admin |
| GET | `/api/v1/admin/metrics` | Ver métricas globales | Admin |
| POST | `/api/v1/admin/users/promote` | Promover usuario a admin | Admin |

---

# 🧩 Arquitectura y Patrones

## Patrones de diseño utilizados

- **Strategy Pattern** → servicios de notificación intercambiables
- **Dependency Injection** → gestión de dependencias con FastAPI
- **Repository Pattern** → separación de acceso a datos

## Principios aplicados

- **SOLID**
- **DRY**
- **Clean Code**
- Separación de responsabilidades
- Arquitectura modular y escalable

---

# 📖 Documentación

FastAPI genera automáticamente la documentación Swagger:

```text
http://localhost:8000/docs
```

Documentación alternativa ReDoc:

```text
http://localhost:8000/redoc
```

---

# 👨‍💻 Autor

Desarrollado por Emily Kohler.