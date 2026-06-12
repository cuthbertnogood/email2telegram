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
ENV APP_VERSION="${APP_VERSION}"
RUN chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1 \
    E2T_STATE_FILE=/data/.state.json

HEALTHCHECK --interval=60s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import json, os, pathlib; p=pathlib.Path(os.getenv('E2T_STATE_FILE','/data/.state.json')); p.exists() and (json.loads(p.read_text(encoding='utf-8')) if p.stat().st_size else {})"

VOLUME ["/data"]

CMD ["python", "src/main.py"]
