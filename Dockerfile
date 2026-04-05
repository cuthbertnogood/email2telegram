FROM python:3.12-slim-bookworm

RUN useradd --create-home --shell /bin/bash --uid 1000 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY VERSION ./VERSION
COPY src/ ./src/

ARG APP_VERSION=unknown
LABEL org.opencontainers.image.version="${APP_VERSION}"
RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    STATE_FILE=/data/.state.json

VOLUME ["/data"]

CMD ["python", "src/main.py"]
