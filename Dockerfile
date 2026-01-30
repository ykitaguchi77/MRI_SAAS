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

# Create non-root user (HF Spaces requirement)
RUN useradd -m -u 1000 user

# Install PyTorch CPU (separate layer for caching)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install other Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Switch to non-root user
USER user
ENV HOME=/home/user
WORKDIR $HOME/app

# Copy backend code
COPY --chown=user backend/app ./app
COPY --chown=user backend/checkpoints ./checkpoints
COPY --chown=user backend/samples ./samples

# Copy frontend build output
COPY --from=frontend-builder --chown=user /app/frontend/dist ./static

# Create temp directory
RUN mkdir -p ./temp

# Environment
ENV MRI_SAAS_DEVICE=cpu
ENV MRI_SAAS_TEMP_DIR=/home/user/app/temp
ENV MRI_SAAS_MODEL_PATH=/home/user/app/checkpoints/final_model.pth

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
