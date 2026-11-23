# Backend only. Build from the repo root so seed.json (which lives there) is in the build context:
#   docker build -f server/Dockerfile .
# Static files and TLS are nginx's job (see client/Dockerfile); this image serves the API alone.
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY server/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./
COPY seed.json ./seed.json

ENV SEED_FILE=/app/seed.json
RUN useradd --system --no-create-home app && chown -R app /app
USER app
EXPOSE 8000

# Migrate, load the seed (safe to rerun), then serve. Only nginx can reach this port, so it is safe to
# trust the X-Forwarded-* headers it sets (real client address and scheme).
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
