FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY pyproject.toml README.md LICENSE /app/
COPY src /app/src

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir ".[web]"

ENV DSM_MEMORY_DIR=/data/memory \
    DSM_WEB_HOST=0.0.0.0 \
    DSM_WEB_PORT=8000

RUN mkdir -p /data/memory && chown -R appuser:appuser /app /data
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/stats', timeout=3)" || exit 1

CMD ["dsm-webui"]
