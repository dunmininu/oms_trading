# Multi-stage build for OMS Trading
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Set environment variables for memory efficiency
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_BUILD_ISOLATION=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements/base.txt /requirements.txt
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r /requirements.txt

# Copy application code for runtime
COPY backend/ ./backend/
COPY pyproject.toml README.md LICENSE ./

# Stage 2: Runtime image
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=apps.core.settings.prod

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r oms \
    && useradd -r -g oms oms

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application code and necessary files
COPY backend/ ./backend/
COPY Makefile .env.example ./

# Create necessary directories
RUN mkdir -p logs media staticfiles && \
    chown -R oms:oms /app

# Copy entrypoint script
COPY infra/scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER oms

# Collect static files (skip during build, will be done at runtime)
# RUN cd backend && python manage.py collectstatic --noinput --settings=apps.core.settings.prod

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Expose port
EXPOSE 8000

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "5", "--chdir", "backend", "apps.core.wsgi:application"]
