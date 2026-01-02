# Auto-Claude Dockerfile
# ======================
# Multi-stage build for Dokploy/Docker deployment
# Serves React SPA via Caddy, proxies API to FastAPI

# ====== Stage 1: Frontend Build ======
FROM node:24-alpine AS frontend-build
WORKDIR /app

# Copy package files first (better caching)
COPY apps/frontend/package*.json ./

# Install dependencies (ignore postinstall scripts that need electron)
RUN npm ci --ignore-scripts

# Copy frontend source
COPY apps/frontend/ ./

# Build web bundle (outputs to dist/web/)
ENV VITE_API_URL=/api
ENV VITE_WS_URL=/ws
RUN npm run build:web

# ====== Stage 2: Python Base ======
FROM python:3.12-slim AS python-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies (better caching)
COPY apps/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy API-specific dependencies
COPY apps/backend/api/requirements.txt ./api-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

# Copy backend source
COPY apps/backend/ ./

# ====== Stage 3: Production ======
FROM python-base AS production

# Install Caddy
RUN apt-get update && apt-get install -y \
    debian-keyring \
    debian-archive-keyring \
    apt-transport-https \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg \
    && curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list \
    && apt-get update \
    && apt-get install -y caddy \
    && rm -rf /var/lib/apt/lists/*

# Copy built frontend from Stage 1
COPY --from=frontend-build /app/dist/web /var/www/html

# Copy Caddy config
COPY docker/Caddyfile /etc/caddy/Caddyfile

# Create directories for data persistence
RUN mkdir -p /data /projects /home/claude/.claude

# Create non-root user for security
RUN useradd -m -s /bin/bash claude \
    && chown -R claude:claude /data /projects /home/claude /var/www/html

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data
ENV PROJECTS_DIR=/projects
ENV PYTHONUNBUFFERED=1

# Expose Caddy port
EXPOSE 3000

# Health check against FastAPI through Caddy
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Copy entrypoint script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# Switch to non-root user
USER claude

# Start services
CMD ["/start.sh"]
