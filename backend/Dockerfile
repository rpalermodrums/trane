# Dockerfile.base - Common base image for backend services (Django & DSP)
FROM python:3.10-slim AS base

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    gcc \
    libpq-dev && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy common requirements.
# (Ensure these requirements are truly shared between your services)
COPY requirements.txt trane/realtime_dsp/requirements_dsp.txt ./

# Install common Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements_dsp.txt


FROM python:3.10-slim AS runtime

COPY --from=base /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libportaudio2 \
    libasound2-dev \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    NUMBA_CACHE_DIR=/tmp/numba_cache

WORKDIR /app

RUN groupadd -r trane && useradd -r -g trane -m -s /bin/bash trane && \
    mkdir -p /home/trane && \
    mkdir -p /tmp/librosa_cache /tmp/numba_cache && \
    chown -R trane:trane /home/trane /tmp/librosa_cache /tmp/numba_cache

COPY --chown=trane:trane . /app/

RUN chmod -R 755 /app && \
    chmod -R 777 /tmp/librosa_cache && \
    chmod -R 777 /tmp/numba_cache

USER trane

CMD ["gunicorn", "trane.wsgi:application", "--bind", "0.0.0.0:8000"]
