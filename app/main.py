from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import engine, Base, SessionLocal
from app.routers import auth, messages, admin
from jose import JWTError, jwt
from dotenv import load_dotenv
import logging
import time
import os

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Handlers: siempre consola, en producción también archivo
_handlers = [logging.StreamHandler()]
if IS_PRODUCTION:
    import os as _os
    _os.makedirs("logs", exist_ok=True)
    _file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S"
    ))
    _handlers.append(_file_handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=_handlers
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

# En producción Swagger y Redoc se desactivan para no exponer la API públicamente
# Para volver a activarlos temporalmente, cambiá ENVIRONMENT=development
app = FastAPI(
    title="Sistem Syntri",
    description="API para envío de notificaciones a múltiples plataformas",
    version="1.0.0",
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Agregá origins de producción acá cuando tengas frontend:
# ALLOWED_ORIGINS = ["https://tu-frontend.com"]
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Headers de seguridad ──────────────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# ── Manejador global de excepciones ──────────────────────────────────────────
from fastapi import Request as _Request
from fastapi.responses import JSONResponse as _JSONResponse
import traceback as _traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: _Request, exc: Exception):
    # Loguea el stacktrace completo internamente
    logger.error(
        f"Excepción no controlada → "
        f"Método: {request.method} | "
        f"Ruta: {request.url.path} | "
        f"Tipo: {type(exc).__name__} | "
        f"Detalle: {str(exc)}\n"
        f"{_traceback.format_exc()}"
    )
    # Respuesta genérica al cliente: sin stacktrace ni info interna
    return _JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor. Por favor intentá más tarde."}
    )


# ── Rate limit por IP ────────────────────────────────────────────────────────
# Almacena en memoria: { ip: { "count": int, "reset_at": timestamp } }
# Se resetea cada 60 segundos. Límite: 60 requests por minuto por IP.
import time as _time
from collections import defaultdict

IP_RATE_LIMIT = 60        # requests por ventana
IP_RATE_WINDOW = 60       # segundos
_ip_counters: dict = defaultdict(lambda: {"count": 0, "reset_at": 0})
_ip_lock = None  # no necesitamos lock porque FastAPI corre en un solo hilo por worker

IP_WHITELIST = {"127.0.0.1", "testclient"}  # IPs que nunca se bloquean

@app.middleware("http")
async def ip_rate_limit_middleware(request: Request, call_next):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()  # x-forwarded-for puede tener múltiples IPs

    if ip not in IP_WHITELIST:
        now = _time.time()
        counter = _ip_counters[ip]

        # Resetear ventana si ya pasó el tiempo
        if now > counter["reset_at"]:
            counter["count"] = 0
            counter["reset_at"] = now + IP_RATE_WINDOW

        counter["count"] += 1

        if counter["count"] > IP_RATE_LIMIT:
            logger.warning(f"Rate limit por IP superado → IP: {ip} | Requests: {counter['count']}")
            return JSONResponse(
                status_code=429,
                content={"detail": f"Demasiadas solicitudes desde tu IP. Esperá {IP_RATE_WINDOW} segundos."}
            )

    return await call_next(request)


# ── Rate limit por IP ──────────────────────────────────────────
from collections import defaultdict
import threading

# Almacenamiento en memoria: {ip: {"count": N, "reset_at": timestamp}}
_ip_counters: dict = defaultdict(lambda: {"count": 0, "reset_at": 0})
_ip_lock = threading.Lock()

IP_RATE_LIMIT = 200        # máximo de requests por IP por ventana
IP_RATE_WINDOW = 60        # ventana en segundos

def _check_ip_rate_limit(ip: str) -> bool:
    """Devuelve True si la IP está dentro del límite, False si lo superó."""
    import time
    now = time.time()
    with _ip_lock:
        entry = _ip_counters[ip]
        if now > entry["reset_at"]:
            entry["count"] = 0
            entry["reset_at"] = now + IP_RATE_WINDOW
        entry["count"] += 1
        return entry["count"] <= IP_RATE_LIMIT


# ── Rutas públicas ────────────────────────────────────────────────────────────
PUBLIC_ROUTES = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


# ── Middleware de autenticación ───────────────────────────────────────────────
@app.middleware("http")
async def ip_rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limit por IP: máximo 200 requests por minuto."""
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")

    if not _check_ip_rate_limit(ip):
        logger.warning(f"Rate limit por IP superado → IP: {ip} | Ruta: {request.url.path}")
        return JSONResponse(
            status_code=429,
            content={"detail": f"Demasiadas solicitudes desde tu IP. Limitá a {IP_RATE_LIMIT} requests por {IP_RATE_WINDOW}s."}
        )
    return await call_next(request)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_ROUTES:
        request.state.user = None
        request.state.role = None
        return await call_next(request)

    token = None
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    if not token:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token de autenticación requerido"}
        )

    try:
        payload = jwt.decode(
            token,
            os.getenv("SECRET_KEY"),
            algorithms=[os.getenv("ALGORITHM")]
        )
        username: str = payload.get("sub")
        if not username:
            raise JWTError("sin subject")
    except JWTError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o expirado"}
        )

    db = SessionLocal()
    try:
        from app import models
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Usuario no encontrado"}
            )
        request.state.user = user
        request.state.role = user.role_name
    finally:
        db.close()

    return await call_next(request)


# ── Middleware de logging ─────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.time()
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "desconocida")
    tiene_token = "Sí" if request.headers.get("authorization") else "No"

    response = await call_next(request)

    duracion = round((time.time() - inicio) * 1000, 2)
    codigo = response.status_code
    user_info = f"Usuario: {request.state.user.username}" if getattr(request.state, "user", None) else "Usuario: anónimo"

    log = (
        f"Método: {request.method} | "
        f"Ruta: {request.url.path} | "
        f"IP: {ip} | "
        f"{user_info} | "
        f"Rol: {getattr(request.state, 'role', None) or 'ninguno'} | "
        f"Token: {tiene_token} | "
        f"Código: {codigo} | "
        f"Duración: {duracion}ms"
    )

    if codigo >= 500:
        logger.error(f"Error del servidor → {log}")
    elif codigo >= 400:
        logger.warning(f"Error del cliente → {log}")
    else:
        logger.info(f"OK → {log}")

    return response


app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"message": "Sistem Syntri API"}