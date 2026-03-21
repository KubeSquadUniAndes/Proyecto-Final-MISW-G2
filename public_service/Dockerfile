# Imagen base
FROM public.ecr.aws/docker/library/python:3.14-slim AS base

WORKDIR /

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Imagen runner
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

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
