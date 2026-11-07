# ---- Base image ----
# python:3.12-slim = Debian with only what Python needs. ~150 MB instead of ~1 GB.
FROM python:3.12-slim

# Don't write .pyc files; flush logs immediately (so `docker logs` shows them live).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ---- Layer 1: dependencies ----
# Copy ONLY requirements.txt first. This layer is cached as long as that file
# doesn't change, so editing Python code never re-runs pip install.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Layer 2: application code ----
# Changes often -> comes last so only this layer is rebuilt.
COPY mizan/ ./mizan/

# ---- Security: don't run as root inside the container ----
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Liveness check Docker runs itself (compose uses it for depends_on).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "mizan.main:app", "--host", "0.0.0.0", "--port", "8000"]
