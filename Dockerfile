# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU (separate layer for caching)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install other Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Set working directory (backend expects to run from here)
WORKDIR /app/backend

# Copy backend code
COPY backend/app ./app
COPY backend/checkpoints ./checkpoints
COPY backend/samples ./samples

# Copy frontend build output
COPY --from=frontend-builder /app/frontend/dist ./static

# Create temp directory
RUN mkdir -p ./temp

# Environment
ENV MRI_SAAS_DEVICE=cpu
ENV PORT=10000

EXPOSE 10000

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
