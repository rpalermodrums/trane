# syntax=docker/dockerfile:1
FROM python:3.10-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
COPY requirements.txt trane/realtime_dsp/requirements_dsp.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_dsp.txt

FROM python:3.10-slim as runtime

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libportaudio2 \
    libasound2-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    NUMBA_CACHE_DIR=/tmp/numba_cache
    # NUMBA_DISABLE_JIT=1

WORKDIR /app

# Create non-root user
RUN groupadd -r trane && useradd -r -g trane -m -s /bin/bash trane && \
    mkdir -p /home/trane && \
    mkdir -p /tmp/librosa_cache /tmp/numba_cache && \
    chown -R trane:trane /home/trane /tmp/librosa_cache /tmp/numba_cache

# Copy application code
COPY --chown=trane:trane . /app/

# Set permissions
RUN chmod -R 755 /app && \
    chmod -R 777 /tmp/librosa_cache && \
    chmod -R 777 /tmp/numba_cache

USER trane

# Expose DSP service port for clarity and tooling support
EXPOSE 9000

CMD ["python", "-m", "trane.realtime_dsp.dsp_service"]
