# Multi-stage build for FastAPI backend
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDUNBUFFERED=1
ENV PYTHONDFAULTENCODING=utf-8

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Development stage
FROM builder as development
ENV ENVIRONMENT=development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM builder as production
ENV ENVIRONMENT=production

# Create non-root user
RUN useradd -m -u appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()"

# Run with gunicorn
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
