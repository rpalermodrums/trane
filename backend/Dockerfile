# backend/Dockerfile
FROM python:3.10-slim

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

    # Set work directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project
COPY . .

# Expose port 8000 (Django's default port for gunicorn)
EXPOSE 8000

# Start gunicorn server
CMD ["gunicorn", "trane.wsgi:application", "--bind", "0.0.0.0:8000"]
