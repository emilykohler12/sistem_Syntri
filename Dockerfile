# Imagen base de Python 3.12
FROM python:3.12-slim

# Crear usuario no-root para no correr la app como root
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Instalar dependencias antes de copiar el código (aprovecha cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Crear carpeta de logs y darle permisos al usuario no-root
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app

# Cambiar al usuario no-root
USER appuser

EXPOSE 8000

# Healthcheck: verifica que la app responde cada 30 segundos
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

# Workers = (2 x núcleos) + 1, ajustá según tu servidor
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]