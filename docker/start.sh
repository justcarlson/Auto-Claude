#!/bin/bash
# Auto-Claude Container Entrypoint
# =================================
# Starts FastAPI backend and Caddy reverse proxy

set -e

echo "================================"
echo "Starting Auto-Claude..."
echo "================================"

# Change to app directory
cd /app

# Start FastAPI in background
echo "Starting FastAPI on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "API is ready!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "ERROR: API failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Start Caddy in foreground (will be PID 1)
echo "Starting Caddy on port 3000..."
exec caddy run --config /etc/caddy/Caddyfile
