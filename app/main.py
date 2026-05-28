from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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

app.include_router(auth.router)
app.include_router(messages.router)
app.include_router(admin.router)

# Rutas que no requieren token
PUBLIC_ROUTES = {
    "/",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """
    Middleware de autenticación:
    - Rutas públicas: pasan sin token
    - Rutas protegidas: decodifica JWT, consulta BD, adjunta user y rol en request.state
    """
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

    # Consultar usuario en BD y adjuntarlo al request
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
        request.state.role = user.role_name   # "user" o "admin" (leído de la tabla roles via FK)
    finally:
        db.close()

    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware de logging: registra método, ruta, IP, token, código y duración."""
    inicio = time.time()

    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "desconocida")
    tiene_token = "Sí" if request.headers.get("authorization") else "No"

    response = await call_next(request)

    duracion = round((time.time() - inicio) * 1000, 2)
    codigo = response.status_code

    # user_id desde request.state si el middleware de auth ya lo adjuntó
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


@app.get("/")
def root():
    return {"message": "Sistem Syntri API"}