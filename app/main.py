from fastapi import FastAPI, Request
from app.database import engine, Base
from app.routers import auth, messages, admin
import logging
import time

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.time()

    # IP origen (considera proxies)
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "desconocida")

    # user_id desde el header Authorization si existe (sin decodificar el JWT acá)
    # El user_id real lo loguea cada endpoint; acá solo indicamos si hay token o no
    tiene_token = "Sí" if request.headers.get("authorization") else "No"

    response = await call_next(request)

    duracion = round((time.time() - inicio) * 1000, 2)
    codigo = response.status_code

    log = (
        f"Método: {request.method} | "
        f"Ruta: {request.url.path} | "
        f"IP: {ip} | "
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