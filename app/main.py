from fastapi import FastAPI, Request
from app.database import engine, Base
from app.routers import auth
import logging
import time

# Configuración del logger en español
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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.time()
    logger.info(f"Pedido entrante → Método: {request.method} | Ruta: {request.url.path}")
    
    response = await call_next(request)
    
    duracion = round((time.time() - inicio) * 1000, 2)
    
    if response.status_code >= 500:
        logger.error(f"Error del servidor → Código: {response.status_code} | Ruta: {request.url.path} | Duración: {duracion}ms")
    elif response.status_code >= 400:
        logger.warning(f"Error del cliente → Código: {response.status_code} | Ruta: {request.url.path} | Duración: {duracion}ms")
    else:
        logger.info(f"Respuesta exitosa → Código: {response.status_code} | Ruta: {request.url.path} | Duración: {duracion}ms")
    
    return response

@app.get("/")
def root():
    logger.info("Acceso a la raíz de la API")
    return {"message": "Sistem Syntri API"}