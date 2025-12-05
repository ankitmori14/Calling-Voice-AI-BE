FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libffi-dev \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Expose the port that the FastAPI app will run on
EXPOSE 8000

# Use a non-root user (optional but recommended)
RUN useradd --create-home appuser && chown -R appuser:appuser /app

# Ensure the entrypoint script is executable and owned by the non-root user
RUN chmod +x /app/start.sh && chown appuser:appuser /app/start.sh

USER appuser

# Entrypoint script starts LiveKit integration in background, then Uvicorn
ENTRYPOINT ["/app/start.sh"]
