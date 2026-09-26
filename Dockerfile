FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    MEDGUARD_DB=/data/medguard.sqlite3 \
    MEDGUARD_UPLOAD_DIR=/data/private_uploads \
    MEDGUARD_COOKIE_SECURE=1

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app \
    && mkdir -p /data/private_uploads \
    && chown -R app:app /app /data

COPY --chown=app:app server.py index.html features.js decorations.js assetsmedical-background.mp4 ./

USER app
EXPOSE 8000
CMD ["python", "server.py"]
