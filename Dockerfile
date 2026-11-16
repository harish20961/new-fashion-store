FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
COPY frontend/ frontend/

WORKDIR /app/backend

# Don't run as root
RUN useradd -m appuser
USER appuser

EXPOSE 5000

# Render/Railway set $PORT; fall back to 5000 locally
CMD ["sh", "-c", "gunicorn --workers 2 --bind 0.0.0.0:${PORT:-5000} \"app:create_app()\""]
