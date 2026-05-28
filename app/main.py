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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistem Syntri",
    description="API para envío de notificaciones a múltiples plataformas",
    version="1.0.0"
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