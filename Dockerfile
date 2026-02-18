# Multi-stage Dockerfile for Saloon Management System
# Stage 1: Build React Frontend
FROM node:18-alpine AS frontend-build

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy frontend source
COPY frontend/ ./

# Set VITE_PUBLIC_BASE_URL build argument (defaults to empty if not provided)
ARG VITE_PUBLIC_BASE_URL
ENV VITE_PUBLIC_BASE_URL=${VITE_PUBLIC_BASE_URL}

# Build React app
RUN npm run build

# Stage 2: Setup Python Backend and serve everything
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source (excluding static folder first)
COPY backend/*.py ./
COPY backend/migrations ./migrations
COPY backend/routes ./routes
COPY backend/templates ./templates
COPY backend/utils ./utils
COPY backend/services ./services

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist ./static

# Copy logo directory to static folder
COPY --from=frontend-build /app/frontend/logo ./static/logo

# NOW copy backend static files (fonts, CSS) - this ensures they're not overwritten
COPY backend/static/ ./static/

# Create instance directory for SQLite database
RUN mkdir -p instance

# Expose port (Cloud Run uses PORT env variable, defaults to 8080)
EXPOSE 8080

# Environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120", "--worker-class", "gthread", "app:app"]

