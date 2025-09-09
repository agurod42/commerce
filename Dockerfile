FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user for security
RUN useradd -m -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install production-specific packages
RUN pip install --no-cache-dir \
    gunicorn \
    psycopg2-binary \
    structlog[dev]

# Copy application code
COPY . .

# Install the application
RUN pip install -e .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/data /app/backups && \
    chown -R appuser:appuser /app && \
    chmod +x /app/scripts/generate_mock_data.py

# Switch to non-root user
USER appuser

# Expose port (if running web server)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -m wholesale_agent.cli.main --config-check || exit 1

# Default command
CMD ["python", "-m", "wholesale_agent.cli.main"]