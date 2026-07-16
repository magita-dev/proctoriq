# ── System Siege — Cloud Run Dockerfile ──────────────────────
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system deps (needed by gTTS/requests)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
COPY . .

# Remove .env if accidentally included — secrets come from Cloud Run env vars
RUN rm -f .env

# Cloud Run sets PORT env var — default 8080
ENV PORT=8080

# Run with uvicorn — single worker for Cloud Run (scales via instances)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
