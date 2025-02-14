# backend/Dockerfile.dsp
FROM python:3.10-slim

# Install system dependencies including audio processing libraries and PostgreSQL
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libsndfile1 \
    libportaudio2 \
    libasound2-dev \
    python3-dev \
    gcc \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for better Python performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PYTHONPATH=/app \
    NUMBA_CACHE_DIR=/tmp/numba_cache \
    NUMBA_DISABLE_JIT=1

WORKDIR /app

# Create a non-root user
RUN groupadd -r trane && useradd -r -g trane -m -s /bin/bash trane && \
    mkdir -p /home/trane && chown -R trane:trane /home/trane

# Copy requirements first for better caching
COPY requirements.txt /app/
COPY trane/realtime_dsp/requirements_dsp.txt /app/trane/realtime_dsp/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r trane/realtime_dsp/requirements_dsp.txt

# Copy the rest of the application
COPY . /app/

# Create necessary directories with proper permissions
RUN mkdir -p /tmp/librosa_cache /tmp/numba_cache && \
    chown -R trane:trane /tmp/librosa_cache && \
    chown -R trane:trane /tmp/numba_cache && \
    chown -R trane:trane /app && \
    chmod -R 755 /app && \
    chmod -R 777 /tmp/librosa_cache && \
    chmod -R 777 /tmp/numba_cache

# Switch to non-root user
USER trane

# Default command (will be overridden by docker-compose for celery worker)
CMD ["python", "-m", "trane.realtime_dsp.dsp_service"]
