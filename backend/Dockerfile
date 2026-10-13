# =============================================================================
# SETMS Backend Dockerfile
# Multi-stage: development (hot-reload) and production (optimized)
# =============================================================================

# ---- Base Stage ----
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependencies Stage ----
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Development Stage ----
FROM deps AS development

COPY . .

# Create scripts package
RUN mkdir -p scripts && touch scripts/__init__.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]

# ---- Production Stage ----
FROM deps AS production

COPY . .

# Non-root user for production
RUN groupadd -r setms && useradd -r -g setms setms && \
    chown -R setms:setms /app
USER setms

EXPOSE 8000

# Production: no reload, multiple workers
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log"]
