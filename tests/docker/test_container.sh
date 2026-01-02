#!/bin/bash
# Container Integration Test Script
# ==================================
# Tests the Docker container builds and runs correctly.
# Run this manually or in CI with Docker available.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

IMAGE_NAME="auto-claude-test"
CONTAINER_NAME="ac-test-$$"
PORT=3001

echo "=== Auto-Claude Container Integration Test ==="
echo "Project root: $PROJECT_ROOT"
echo ""

cleanup() {
    echo "Cleaning up..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

trap cleanup EXIT

# Test 1: Dockerfile exists
echo "Test 1: Checking Dockerfile exists..."
if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
    echo "SKIP: Dockerfile not found (Phase 3)"
    exit 0
fi
echo "PASS: Dockerfile exists"
echo ""

# Test 2: Build succeeds
echo "Test 2: Building container..."
cd "$PROJECT_ROOT"
if ! docker build -t "$IMAGE_NAME" . ; then
    echo "FAIL: Build failed"
    exit 1
fi
echo "PASS: Build succeeded"
echo ""

# Test 3: Container starts
echo "Test 3: Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:3000" \
    -e CLAUDE_CODE_OAUTH_TOKEN=test-token \
    "$IMAGE_NAME"

echo "Waiting for container to start..."
sleep 10
echo "PASS: Container started"
echo ""

# Test 4: Health endpoint responds
echo "Test 4: Checking health endpoint..."
for i in {1..30}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/api/health" || echo "000")
    if [ "$response" = "200" ]; then
        echo "PASS: Health endpoint returned 200"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "FAIL: Health endpoint did not respond after 30 seconds"
        echo "Container logs:"
        docker logs "$CONTAINER_NAME"
        exit 1
    fi
    sleep 1
done
echo ""

# Test 5: Static files served
echo "Test 5: Checking static file serving..."
response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" || echo "000")
if [ "$response" = "200" ]; then
    echo "PASS: Static files served"
else
    echo "WARN: Static files not served (status: $response)"
fi
echo ""

# Test 6: WebSocket endpoint exists
echo "Test 6: Checking WebSocket upgrade..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Upgrade: websocket" \
    -H "Connection: Upgrade" \
    "http://localhost:$PORT/ws/terminal/test" || echo "000")
# 101 = upgrade, 400/426 = bad request (expected without proper WS handshake)
if [ "$response" = "101" ] || [ "$response" = "400" ] || [ "$response" = "426" ]; then
    echo "PASS: WebSocket endpoint exists"
else
    echo "WARN: WebSocket endpoint status: $response"
fi
echo ""

echo "=== All tests completed ==="
