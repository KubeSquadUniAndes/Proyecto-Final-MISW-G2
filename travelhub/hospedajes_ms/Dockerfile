# Imagen base
FROM public.ecr.aws/docker/library/python:3.14-slim AS base

# Variables de entorno
# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# Crear directorio de la app
WORKDIR /

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Imagen base
FROM public.ecr.aws/docker/library/python:3.14-slim AS runner

WORKDIR /app
COPY --from=base /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

COPY hospedajes_model.py .
COPY main.py .
COPY postgres_db.py .

RUN groupadd -r noroot && useradd -r -g noroot noroot
RUN chown -R noroot:noroot /app
USER noroot

# Exponer el puerto Flask
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
