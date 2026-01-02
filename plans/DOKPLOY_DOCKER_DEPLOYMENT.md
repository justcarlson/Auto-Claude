# Auto-Claude Dokploy Docker Deployment Plan

> TDD-First, Delegation-Based Implementation Plan

## Overview

Transform Auto-Claude from an Electron desktop app to a containerized web application deployable via Dokploy.

**Principles:**
- **TDD**: Red-Green-Refactor for every feature
- **Delegation**: Use specialized agents for implementation
- **Fast Feedback**: Unit tests in ms, integration tests with real collaborators
- **No Mocking in Unit Tests**: Design for testability with pure functions

---

## Architecture

### Current (Electron)
```
┌──────────────────────────────────────────────────────────────┐
│                    Electron Desktop App                       │
│  ┌──────────────────┐  ┌──────────────────┐                  │
│  │   React Renderer │◄─┤   Electron IPC   │                  │
│  │   (Frontend UI)  │  │   (Main Process) │                  │
│  └──────────────────┘  └────────┬─────────┘                  │
│                                 │                             │
│                    ┌────────────▼────────────┐               │
│                    │   Python Backend        │               │
│                    │   (apps/backend/)       │               │
│                    └─────────────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

### Target (Docker/Dokploy)
```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Dokploy (via Traefik)                            │
│   Browser ◄──── https://auto-claude.domain.com ────►  Container         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         auto-claude Container                            │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                         Caddy (Reverse Proxy)                        ││
│  │  - Serves React SPA static files                                    ││
│  │  - Proxy: /api/* → FastAPI :8000                                    ││
│  │  - Proxy: /ws/* → FastAPI :8000                                     ││
│  └──────────────────────────┬──────────────────────────────────────────┘│
│                             │                                            │
│  ┌──────────────────────────▼──────────────────────────────────────────┐│
│  │                        FastAPI Backend                               ││
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ ││
│  │  │  REST API   │  │  WebSocket   │  │     PTY Manager            │ ││
│  │  │  /api/*     │  │  /ws/*       │  │  (Python ptyprocess)       │ ││
│  │  └─────────────┘  └──────────────┘  └────────────────────────────┘ ││
│  │                          │                                          ││
│  │  ┌──────────────────────────────────────────────────────────────┐  ││
│  │  │              Auto-Claude Python Core (existing)               │  ││
│  │  └──────────────────────────────────────────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                          │
│  Volumes: /projects, /data, /home/claude/.claude                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 0: Test Infrastructure Setup

### Task 0.1: Backend Pytest Infrastructure

**Files to Create:**
- `apps/backend/api/tests/conftest.py`
- `apps/backend/api/tests/pytest.ini`

**Existing Infrastructure (leverage):**
- `tests/pytest.ini` - has markers: `slow`, `integration`, `asyncio`
- `tests/conftest.py` - SDK mocking patterns

**Dependencies:**
```
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Create pytest infrastructure for FastAPI API tests
EXPECTED OUTCOME: 
- conftest.py with async_client fixture using httpx ASGITransport
- pytest.ini with asyncio_mode = auto
- Test that imports work correctly
REQUIRED TOOLS: Read, Write, Bash (pytest --collect-only)
MUST DO:
- Use ASGITransport pattern from httpx
- Create reusable async_client fixture
- Follow existing patterns in tests/conftest.py
MUST NOT DO:
- Don't modify existing test files
- Don't add unnecessary dependencies
CONTEXT: 
- Existing pytest.ini at tests/pytest.ini
- Existing conftest.py at tests/conftest.py
- New API will be at apps/backend/api/
```

---

### Task 0.2: Frontend Vitest Infrastructure

**Existing Infrastructure (leverage):**
- `apps/frontend/vitest.config.ts` - already configured
- `apps/frontend/src/__mocks__/electron.ts` - Electron mocks

**Files to Create:**
- `apps/frontend/src/renderer/lib/api/__tests__/setup.ts`

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Add RITE Way assertion helper for Vitest
EXPECTED OUTCOME:
- Helper function for explicit assertions with given/should
- Test file demonstrating usage
REQUIRED TOOLS: Read, Write
MUST DO:
- Follow RITE Way pattern (Readable, Isolated, Thorough, Explicit)
- Create assert helper with given, should, actual, expected
MUST NOT DO:
- Don't modify existing vitest.config.ts
- Don't add new dependencies
CONTEXT:
- Vitest already configured at apps/frontend/vitest.config.ts
- Pattern: assert({ given: '...', should: '...', actual, expected })
```

---

### Task 0.3: GitHub Actions CI Workflow

**File to Create:** `.github/workflows/tdd-ci.yml`

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Create GitHub Actions workflow for TDD CI
EXPECTED OUTCOME:
- Workflow that runs on every push and PR
- Runs backend pytest tests
- Runs frontend vitest tests
- Runs Docker build test
REQUIRED TOOLS: Read, Write
MUST DO:
- Use matrix for Python 3.12 and Node 24
- Cache pip and npm dependencies
- Run tests in parallel where possible
- Fail fast on test failures
MUST NOT DO:
- Don't deploy anything
- Don't push to registries
CONTEXT:
- Existing workflows in .github/workflows/
- Backend tests: pytest apps/backend/api/tests/
- Frontend tests: npm test (in apps/frontend/)
```

---

### Task 0.4: Docker Test Infrastructure

**Files to Create:**
- `tests/docker/test_container.sh`
- `tests/docker/test_compose.py`

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Create Docker testing infrastructure
EXPECTED OUTCOME:
- Shell script to test container builds and health
- Python tests to validate docker-compose.yml structure
REQUIRED TOOLS: Write, Bash
MUST DO:
- Test container builds successfully
- Test health endpoint responds
- Validate compose has required services/volumes
MUST NOT DO:
- Don't require running containers for unit tests
- Don't test against production
CONTEXT:
- Docker files will be at project root
- Compose will define 'app' service on port 3000
```

---

## Phase 1: FastAPI Backend (TDD)

### Task 1.1: Health Endpoint

**TDD Cycle:**

**RED - Write Failing Test First:**
```python
# apps/backend/api/tests/routes/test_health.py
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_health_returns_status_ok():
    """
    Given: API server is running
    Should: Return {"status": "ok", "version": "x.x.x"}
    """
    from api.main import app
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "version" in response.json()
```

**GREEN - Minimal Implementation:**

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Implement health endpoint to pass test
EXPECTED OUTCOME:
- apps/backend/api/main.py with FastAPI app
- apps/backend/api/routes/health.py with health router
- Test passes
REQUIRED TOOLS: Read, Write, Bash (pytest)
MUST DO:
- Create minimal FastAPI app
- Mount router at /api prefix
- Return version from package or config
- Run pytest to verify
MUST NOT DO:
- Don't add extra endpoints
- Don't add middleware yet
CONTEXT:
- Test file: apps/backend/api/tests/routes/test_health.py
- Follow FastAPI router pattern
```

**REFACTOR:**
```
DELEGATE TO: oracle agent
TASK: Review health endpoint implementation
EXPECTED OUTCOME:
- Code review with suggestions
- Verify typing and error handling
REQUIRED TOOLS: Read
MUST DO:
- Check for proper typing
- Verify FastAPI best practices
- Suggest improvements
MUST NOT DO:
- Don't make changes (just review)
```

---

### Task 1.2: Projects CRUD API

**TDD Cycle - One Test at a Time:**

**Test 1: List empty projects**
```python
# apps/backend/api/tests/routes/test_projects.py
@pytest.mark.asyncio
async def test_list_projects_returns_empty_initially():
    """
    Given: No projects have been added
    Should: Return empty list
    """
    async with AsyncClient(...) as client:
        response = await client.get("/api/projects")
    
    assert response.status_code == 200
    assert response.json() == []
```

**Test 2: Add project**
```python
@pytest.mark.asyncio
async def test_add_project_creates_project():
    """
    Given: Valid project path
    Should: Return created project with id
    """
    async with AsyncClient(...) as client:
        response = await client.post(
            "/api/projects",
            json={"path": "/projects/my-app"}
        )
    
    assert response.status_code == 201
    assert response.json()["path"] == "/projects/my-app"
    assert "id" in response.json()
```

**Test 3: Get project**
```python
@pytest.mark.asyncio
async def test_get_project_by_id():
    """
    Given: Project exists
    Should: Return project details
    """
    # ... create project first, then get by id
```

**Test 4: Delete project**
```python
@pytest.mark.asyncio
async def test_delete_project_removes_it():
    """
    Given: Project exists
    Should: Remove and return 204
    """
```

**Delegation Prompt (per test):**
```
DELEGATE TO: general agent
TASK: Implement projects API to pass this test
EXPECTED OUTCOME:
- Route handler that makes test pass
- Pydantic models for request/response
REQUIRED TOOLS: Read, Write, Bash (pytest)
MUST DO:
- Store projects in /data/projects.json
- Use Pydantic for validation
- Generate UUID for project id
- Run test after implementation
MUST NOT DO:
- Don't implement more than needed for current test
- Don't add validation beyond what test requires
CONTEXT:
- Current failing test: [paste test]
- Existing routes: apps/backend/api/routes/
```

---

### Task 1.3: Tasks CRUD API

**Tests (one at a time):**

```python
# apps/backend/api/tests/routes/test_tasks.py

@pytest.mark.asyncio
async def test_create_task_for_project():
    """
    Given: Valid project ID and task data
    Should: Create task with pending status
    """
    
@pytest.mark.asyncio
async def test_list_tasks_for_project():
    """
    Given: Project with tasks
    Should: Return list of tasks
    """

@pytest.mark.asyncio
async def test_get_task_by_id():
    """
    Given: Task exists
    Should: Return task details with spec path
    """

@pytest.mark.asyncio
async def test_update_task_status():
    """
    Given: Task exists
    Should: Update status and return updated task
    """

@pytest.mark.asyncio
async def test_delete_task():
    """
    Given: Task exists
    Should: Remove task and return 204
    """
```

---

### Task 1.4: Terminal PTY Service

**Pure Function Tests (unit tests, fast):**

```python
# apps/backend/api/tests/services/test_terminal_service.py

def test_strip_ansi_removes_escape_codes():
    """
    Given: String with ANSI escape codes
    Should: Return clean string
    """
    from api.services.terminal_service import strip_ansi
    
    input_data = "\x1b[32mHello\x1b[0m World"
    expected = "Hello World"
    actual = strip_ansi(input_data)
    
    assert actual == expected

def test_to_pty_dimensions_converts_correctly():
    """
    Given: cols and rows dict
    Should: Return (rows, cols) tuple for ptyprocess
    """
    from api.services.terminal_service import to_pty_dimensions
    
    input_data = {"cols": 80, "rows": 24}
    expected = (24, 80)
    actual = to_pty_dimensions(input_data)
    
    assert actual == expected

def test_parse_terminal_message_handles_input():
    """
    Given: JSON message with type 'input'
    Should: Return parsed TerminalMessage
    """
    from api.services.terminal_service import parse_terminal_message
    
    input_data = '{"type": "input", "data": "ls\\n"}'
    result = parse_terminal_message(input_data)
    
    assert result.type == "input"
    assert result.data == "ls\n"
```

**Integration Tests (with real PTY):**

```python
# apps/backend/api/tests/services/test_terminal_integration.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_spawns_shell():
    """
    Given: Request to create terminal
    Should: Spawn bash and return terminal_id
    """
    from api.services.terminal_service import TerminalManager
    
    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")
    
    assert terminal_id is not None
    assert manager.is_alive(terminal_id)
    
    await manager.destroy(terminal_id)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_terminal_echoes_command():
    """
    Given: Terminal with echo command
    Should: Return command output
    """
    manager = TerminalManager()
    terminal_id = await manager.create_terminal(cwd="/tmp")
    
    await manager.write(terminal_id, "echo hello\n")
    
    output = []
    async for chunk in manager.read(terminal_id, timeout=2.0):
        output.append(chunk)
        if "hello" in "".join(output):
            break
    
    assert "hello" in "".join(output)
    await manager.destroy(terminal_id)
```

**Delegation Prompt:**
```
DELEGATE TO: general agent
TASK: Implement TerminalManager with ptyprocess
EXPECTED OUTCOME:
- Pure functions pass unit tests
- Integration tests pass with real PTY
REQUIRED TOOLS: Read, Write, Bash (pytest)
MUST DO:
- Use ptyprocess.PtyProcess for spawning
- Async generator for reading output
- Proper cleanup on destroy
- Handle EOFError gracefully
MUST NOT DO:
- Don't block event loop (use run_in_executor)
- Don't leak file descriptors
CONTEXT:
- Unit tests: apps/backend/api/tests/services/test_terminal_service.py
- Integration tests: apps/backend/api/tests/services/test_terminal_integration.py
```

---

### Task 1.5: WebSocket Terminal Handler

**Tests:**

```python
# apps/backend/api/tests/websocket/test_terminal_ws.py
from starlette.testclient import TestClient

def test_websocket_accepts_connection():
    """
    Given: WebSocket connection request
    Should: Accept and send connected message
    """
    from api.main import app
    
    with TestClient(app).websocket_connect("/ws/terminal/term_123") as ws:
        message = ws.receive_json()
    
    assert message["type"] == "connected"
    assert message["terminal_id"] == "term_123"

def test_websocket_forwards_input_to_pty():
    """
    Given: Input message sent to WebSocket
    Should: Execute in PTY and return output
    """
    from api.main import app
    
    with TestClient(app).websocket_connect("/ws/terminal/term_123") as ws:
        ws.receive_json()  # connected message
        ws.send_json({"type": "input", "data": "echo test\n"})
        
        outputs = []
        for _ in range(10):
            msg = ws.receive_json()
            if msg["type"] == "output":
                outputs.append(msg["data"])
            if "test" in "".join(outputs):
                break
    
    assert "test" in "".join(outputs)

def test_websocket_handles_resize():
    """
    Given: Resize message
    Should: Resize PTY dimensions
    """
    from api.main import app
    
    with TestClient(app).websocket_connect("/ws/terminal/term_123") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "resize", "cols": 120, "rows": 40})
        
        # No error means success
        ws.send_json({"type": "input", "data": "tput cols\n"})
        # Output should eventually show 120
```

---

### Task 1.6: Task Execution API

**Tests:**

```python
# apps/backend/api/tests/routes/test_task_execution.py

@pytest.mark.asyncio
async def test_start_task_changes_status_to_running():
    """
    Given: Task in pending status
    Should: Change to running and spawn agent
    """

@pytest.mark.asyncio  
async def test_stop_task_terminates_agent():
    """
    Given: Task in running status
    Should: Stop agent and change to stopped
    """

@pytest.mark.asyncio
async def test_task_events_stream_via_websocket():
    """
    Given: Running task
    Should: Stream progress events via WebSocket
    """
```

---

### Task 1.7: Worktree API

**Tests:**

```python
# apps/backend/api/tests/routes/test_worktrees.py

@pytest.mark.asyncio
async def test_get_worktree_diff():
    """
    Given: Task with worktree changes
    Should: Return git diff
    """

@pytest.mark.asyncio
async def test_merge_worktree():
    """
    Given: Approved task with worktree
    Should: Merge changes to main branch
    """

@pytest.mark.asyncio
async def test_discard_worktree():
    """
    Given: Task with worktree
    Should: Delete worktree and branch
    """
```

---

### Task 1.8: Settings API

**Tests:**

```python
# apps/backend/api/tests/routes/test_settings.py

@pytest.mark.asyncio
async def test_get_settings_returns_defaults():
    """
    Given: No settings file exists
    Should: Return default settings
    """

@pytest.mark.asyncio
async def test_update_settings_persists():
    """
    Given: New settings values
    Should: Save to file and return updated
    """
```

---

## Phase 2: React Frontend API Abstraction (TDD)

### Task 2.1: APIClient Interface + Factory

**Tests:**

```typescript
// apps/frontend/src/renderer/lib/api/__tests__/client.test.ts
import { describe, test, expect, vi, beforeEach, afterEach } from 'vitest';
import { createAPIClient } from '../client';

describe('createAPIClient', () => {
  afterEach(() => {
    delete (window as any).electronAPI;
  });

  test('returns ElectronAPIClient when electronAPI exists', () => {
    // Given: electronAPI is on window
    // Should: Return ElectronAPIClient
    
    (window as any).electronAPI = { getProjects: vi.fn() };
    
    const client = createAPIClient();
    
    expect(client.constructor.name).toBe('ElectronAPIClient');
  });

  test('returns WebAPIClient when electronAPI missing', () => {
    // Given: No electronAPI on window
    // Should: Return WebAPIClient
    
    const client = createAPIClient();
    
    expect(client.constructor.name).toBe('WebAPIClient');
  });
});
```

**Delegation Prompt:**
```
DELEGATE TO: frontend-ui-ux-engineer agent
TASK: Create APIClient interface and factory
EXPECTED OUTCOME:
- APIClient interface with all methods
- createAPIClient factory function
- Tests pass
REQUIRED TOOLS: Read, Write, Bash (npm test)
MUST DO:
- Define interface matching ElectronAPI
- Factory detects environment
- Export types properly
MUST NOT DO:
- Don't implement client classes yet (just interface)
CONTEXT:
- Test: apps/frontend/src/renderer/lib/api/__tests__/client.test.ts
- Existing API: apps/frontend/src/preload/api/index.ts
```

---

### Task 2.2: WebAPIClient Implementation

**Tests (one method at a time):**

```typescript
// apps/frontend/src/renderer/lib/api/__tests__/web-client.test.ts

describe('WebAPIClient', () => {
  describe('getProjects', () => {
    test('fetches from /api/projects', async () => {
      // Given: API returns projects
      // Should: Return parsed array
      
      const mockProjects = [{ id: '1', path: '/app' }];
      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjects,
      } as Response);
      
      const client = new WebAPIClient();
      const result = await client.getProjects();
      
      expect(result).toEqual(mockProjects);
      expect(fetch).toHaveBeenCalledWith('/api/projects');
    });

    test('throws on API error', async () => {
      // Given: API returns 500
      // Should: Throw error
      
      vi.spyOn(global, 'fetch').mockResolvedValueOnce({
        ok: false,
        status: 500,
      } as Response);
      
      const client = new WebAPIClient();
      
      await expect(client.getProjects()).rejects.toThrow();
    });
  });

  describe('createTask', () => {
    test('posts to /api/projects/{id}/tasks', async () => {
      // ...
    });
  });
  
  // ... more methods
});
```

---

### Task 2.3: ElectronAPIClient Wrapper

**Tests:**

```typescript
// apps/frontend/src/renderer/lib/api/__tests__/electron-client.test.ts

describe('ElectronAPIClient', () => {
  test('delegates getProjects to electronAPI', async () => {
    // Given: electronAPI.getProjects returns data
    // Should: Return same data
    
    const mockProjects = [{ id: '1', path: '/app' }];
    (window as any).electronAPI = {
      getProjects: vi.fn().mockResolvedValue(mockProjects)
    };
    
    const client = new ElectronAPIClient();
    const result = await client.getProjects();
    
    expect(result).toEqual(mockProjects);
    expect(window.electronAPI.getProjects).toHaveBeenCalled();
  });
});
```

---

### Task 2.4: TerminalWebSocket Client

**Tests:**

```typescript
// apps/frontend/src/renderer/lib/api/__tests__/terminal-ws.test.ts

describe('TerminalWebSocket', () => {
  test('connects to /ws/terminal/{id}', () => {
    const ws = new TerminalWebSocket('term_123');
    expect(ws.url).toBe('/ws/terminal/term_123');
  });

  test('calls onOutput when data received', () => {
    const ws = new TerminalWebSocket('term_123');
    const outputs: string[] = [];
    
    ws.onOutput((data) => outputs.push(data));
    ws.simulateMessage({ type: 'output', data: 'Hello' });
    
    expect(outputs).toEqual(['Hello']);
  });

  test('sends input as JSON message', () => {
    const ws = new TerminalWebSocket('term_123');
    const sent: any[] = [];
    ws.mockSend = (data) => sent.push(JSON.parse(data));
    
    ws.sendInput('ls\n');
    
    expect(sent).toEqual([{ type: 'input', data: 'ls\n' }]);
  });
});
```

---

### Task 2.5: Vite Web Build Config

**File:** `apps/frontend/vite.web.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.IS_WEB': 'true',
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src/renderer'),
      '@shared': resolve(__dirname, 'src/shared'),
      '@features': resolve(__dirname, 'src/renderer/features'),
      '@components': resolve(__dirname, 'src/renderer/shared/components'),
      '@hooks': resolve(__dirname, 'src/renderer/shared/hooks'),
      '@lib': resolve(__dirname, 'src/renderer/shared/lib'),
    },
  },
  build: {
    outDir: 'dist/web',
    rollupOptions: {
      input: resolve(__dirname, 'src/renderer/index.html'),
    },
  },
});
```

**Test:**
```bash
# Should build without errors
npm run build:web
# Output should exist
test -d dist/web && test -f dist/web/index.html
```

---

### Task 2.6: Update React Components

**Delegation Prompt:**
```
DELEGATE TO: frontend-ui-ux-engineer agent
TASK: Update React stores to use API abstraction
EXPECTED OUTCOME:
- Stores use createAPIClient() instead of window.electronAPI
- App works in both Electron and Web modes
REQUIRED TOOLS: Read, Write, Glob, Grep
MUST DO:
- Find all window.electronAPI usages in renderer/
- Replace with API client from lib/api/client
- Ensure IS_WEB conditional logic works
MUST NOT DO:
- Don't break Electron mode
- Don't change component logic, only API calls
CONTEXT:
- API client: src/renderer/lib/api/client.ts
- Stores likely in: src/renderer/features/*/store.ts
```

---

## Phase 3: Docker Configuration (TDD)

### Task 3.1: Dockerfile

**Test First:**
```bash
# tests/docker/test_container.sh
#!/bin/bash
set -e

echo "=== Testing Dockerfile ==="

# Test 1: Build succeeds
echo "Test: Container builds..."
docker build -t auto-claude-test . || { echo "FAIL: Build failed"; exit 1; }
echo "PASS: Build succeeded"

# Test 2: Container starts
echo "Test: Container starts..."
docker run -d --name ac-test -p 3001:3000 auto-claude-test
sleep 10

# Test 3: Health endpoint responds
echo "Test: Health endpoint..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/api/health)
if [ "$response" != "200" ]; then
    echo "FAIL: Health returned $response"
    docker logs ac-test
    docker stop ac-test && docker rm ac-test
    exit 1
fi
echo "PASS: Health returned 200"

# Cleanup
docker stop ac-test && docker rm ac-test
echo "=== All tests passed ==="
```

**Dockerfile:**
```dockerfile
# Dockerfile
# ====== Frontend Build ======
FROM node:24-alpine AS frontend-build
WORKDIR /app
COPY apps/frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY apps/frontend/ ./
ENV VITE_API_URL=/api
ENV VITE_WS_URL=/ws
RUN npm run build:web

# ====== Python Base ======
FROM python:3.12-slim AS python-base
RUN apt-get update && apt-get install -y \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Claude CLI
RUN curl -fsSL https://claude.ai/install.sh | sh

WORKDIR /app
COPY apps/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# API dependencies
COPY apps/backend/api/requirements.txt ./api-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt

COPY apps/backend/ ./

# ====== Production ======
FROM python-base AS production
RUN apt-get update && apt-get install -y caddy && rm -rf /var/lib/apt/lists/*

COPY --from=frontend-build /app/dist/web /var/www/html
COPY docker/Caddyfile /etc/caddy/Caddyfile

RUN mkdir -p /data /projects /home/claude/.claude
RUN useradd -m -s /bin/bash claude && chown -R claude:claude /data /projects /home/claude

ENV PYTHONPATH=/app
ENV DATA_DIR=/data
ENV PROJECTS_DIR=/projects

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s \
    CMD curl -f http://localhost:3000/api/health || exit 1

COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

USER claude
CMD ["/start.sh"]
```

---

### Task 3.2: docker-compose.yml

**Test First:**
```python
# tests/docker/test_compose.py
import yaml
import pytest

def test_compose_has_app_service():
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    assert 'services' in compose
    assert 'app' in compose['services']

def test_compose_exposes_port_3000():
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    ports = compose['services']['app']['ports']
    assert any('3000' in str(p) for p in ports)

def test_compose_has_required_volumes():
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    assert 'volumes' in compose
    assert 'auto-claude-data' in compose['volumes']

def test_compose_has_env_vars():
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    env = compose['services']['app'].get('environment', [])
    env_str = str(env)
    assert 'CLAUDE_CODE_OAUTH_TOKEN' in env_str
```

**docker-compose.yml:**
```yaml
name: auto-claude

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: auto-claude
    ports:
      - "3000:3000"
    volumes:
      - ${PROJECTS_PATH:-./projects}:/projects
      - auto-claude-data:/data
      - auto-claude-claude:/home/claude/.claude
    environment:
      - CLAUDE_CODE_OAUTH_TOKEN=${CLAUDE_CODE_OAUTH_TOKEN:-}
      - GRAPHITI_ENABLED=${GRAPHITI_ENABLED:-true}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - LINEAR_API_KEY=${LINEAR_API_KEY:-}
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.auto-claude.rule=Host(`${DOMAIN:-localhost}`)"
      - "traefik.http.services.auto-claude.loadbalancer.server.port=3000"

volumes:
  auto-claude-data:
  auto-claude-claude:
```

---

### Task 3.3: Caddyfile

**Test First:**
```python
# tests/docker/test_caddy.py

def test_caddy_serves_spa():
    with open('docker/Caddyfile') as f:
        config = f.read()
    
    assert 'try_files {path} /index.html' in config

def test_caddy_proxies_api():
    with open('docker/Caddyfile') as f:
        config = f.read()
    
    assert '/api/*' in config
    assert 'reverse_proxy' in config
    assert 'localhost:8000' in config

def test_caddy_proxies_websocket():
    with open('docker/Caddyfile') as f:
        config = f.read()
    
    assert '/ws/*' in config
```

**docker/Caddyfile:**
```caddyfile
:3000 {
    root * /var/www/html
    file_server
    try_files {path} /index.html

    handle /api/* {
        reverse_proxy localhost:8000
    }

    handle /ws/* {
        reverse_proxy localhost:8000
    }
}
```

---

### Task 3.4: start.sh

**docker/start.sh:**
```bash
#!/bin/bash
set -e

echo "Starting Auto-Claude..."

# Start FastAPI
cd /app
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API
echo "Waiting for API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "API ready"
        break
    fi
    sleep 1
done

# Start Caddy (foreground)
echo "Starting Caddy..."
exec caddy run --config /etc/caddy/Caddyfile
```

---

## Phase 4: Integration Testing

### Task 4.1: Full Workflow Test

```python
# tests/integration/test_full_workflow.py

@pytest.mark.integration
@pytest.mark.asyncio
async def test_project_to_task_workflow():
    """
    Given: Running API
    Should: Create project -> Create task -> Get task
    """
    async with AsyncClient(base_url="http://localhost:3000") as client:
        # Add project
        resp = await client.post("/api/projects", json={"path": "/projects/test"})
        assert resp.status_code == 201
        project = resp.json()
        
        # Create task
        resp = await client.post(
            f"/api/projects/{project['id']}/tasks",
            json={"title": "Test", "description": "Test task"}
        )
        assert resp.status_code == 201
        task = resp.json()
        assert task["status"] == "pending"
        
        # Get task
        resp = await client.get(f"/api/tasks/{task['id']}")
        assert resp.status_code == 200
```

### Task 4.2: Terminal E2E Test

```python
# tests/integration/test_terminal_e2e.py

@pytest.mark.integration
def test_terminal_websocket_e2e():
    """
    Given: Running app with WebSocket
    Should: Execute command and get output
    """
    import websocket
    
    ws = websocket.create_connection("ws://localhost:3000/ws/terminal/test")
    
    # Receive connected
    msg = json.loads(ws.recv())
    assert msg["type"] == "connected"
    
    # Send command
    ws.send(json.dumps({"type": "input", "data": "echo e2e-test\n"}))
    
    # Receive output
    output = ""
    for _ in range(20):
        msg = json.loads(ws.recv())
        if msg["type"] == "output":
            output += msg["data"]
        if "e2e-test" in output:
            break
    
    assert "e2e-test" in output
    ws.close()
```

---

## Phase 5: Dokploy Deployment

### Task 5.1: Dokploy Compatibility

**Validation:**
```python
# tests/docker/test_dokploy.py

def test_no_host_network():
    """Dokploy requires bridge network"""
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    app = compose['services']['app']
    assert app.get('network_mode') != 'host'

def test_traefik_labels_present():
    """Dokploy uses Traefik for routing"""
    with open('docker-compose.yml') as f:
        compose = yaml.safe_load(f)
    
    labels = compose['services']['app'].get('labels', [])
    assert any('traefik.enable' in str(l) for l in labels)
```

### Task 5.2: Deployment Documentation

**Delegation Prompt:**
```
DELEGATE TO: document-writer agent
TASK: Create Dokploy deployment guide
EXPECTED OUTCOME:
- docs/DOKPLOY_DEPLOYMENT.md with step-by-step guide
REQUIRED TOOLS: Write
MUST DO:
- Prerequisites (Dokploy installed, domain configured)
- Step-by-step UI instructions
- Environment variables reference
- Troubleshooting section
MUST NOT DO:
- Don't include implementation details
- Don't include internal architecture
CONTEXT:
- Target audience: DevOps/Self-hosters
- Dokploy uses Docker Compose with Traefik
```

### Task 5.3: Environment Example

**File:** `.env.docker.example`
```bash
# Required
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token

# Project directory on host
PROJECTS_PATH=/home/user/projects

# Domain (for Dokploy/Traefik)
DOMAIN=auto-claude.example.com

# Optional - Graphiti Memory
GRAPHITI_ENABLED=true
OPENAI_API_KEY=sk-xxx

# Optional - Integrations
LINEAR_API_KEY=lin_api_xxx
```

---

## File Structure After Implementation

```
Auto-Claude/
├── apps/
│   ├── backend/
│   │   ├── api/                          # NEW
│   │   │   ├── __init__.py
│   │   │   ├── main.py                   # FastAPI app
│   │   │   ├── config.py                 # Settings
│   │   │   ├── requirements.txt          # API deps
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py
│   │   │   │   ├── projects.py
│   │   │   │   ├── tasks.py
│   │   │   │   ├── settings.py
│   │   │   │   └── worktrees.py
│   │   │   ├── websocket/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py
│   │   │   │   ├── terminal.py
│   │   │   │   └── events.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── terminal_service.py
│   │   │   │   ├── project_service.py
│   │   │   │   └── task_service.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── api_models.py
│   │   │   └── tests/                    # API tests
│   │   │       ├── conftest.py
│   │   │       ├── pytest.ini
│   │   │       ├── routes/
│   │   │       │   ├── test_health.py
│   │   │       │   ├── test_projects.py
│   │   │       │   ├── test_tasks.py
│   │   │       │   └── ...
│   │   │       ├── services/
│   │   │       │   ├── test_terminal_service.py
│   │   │       │   └── test_terminal_integration.py
│   │   │       └── websocket/
│   │   │           └── test_terminal_ws.py
│   │   └── ... (existing)
│   └── frontend/
│       ├── src/
│       │   └── renderer/
│       │       └── lib/
│       │           └── api/              # NEW
│       │               ├── client.ts
│       │               ├── types.ts
│       │               ├── web-client.ts
│       │               ├── electron-client.ts
│       │               ├── terminal-ws.ts
│       │               └── __tests__/
│       │                   ├── client.test.ts
│       │                   ├── web-client.test.ts
│       │                   └── terminal-ws.test.ts
│       ├── vite.web.config.ts            # NEW
│       └── ... (existing)
├── docker/                               # NEW
│   ├── Caddyfile
│   └── start.sh
├── tests/
│   ├── docker/                           # NEW
│   │   ├── test_container.sh
│   │   ├── test_compose.py
│   │   └── test_dokploy.py
│   └── integration/                      # NEW
│       ├── test_full_workflow.py
│       └── test_terminal_e2e.py
├── plans/
│   └── DOKPLOY_DOCKER_DEPLOYMENT.md      # This file
├── docs/
│   └── DOKPLOY_DEPLOYMENT.md             # NEW (user guide)
├── .github/
│   └── workflows/
│       └── tdd-ci.yml                    # NEW
├── Dockerfile                            # NEW
├── docker-compose.yml                    # NEW
├── docker-compose.test.yml               # NEW
└── .env.docker.example                   # NEW
```

---

## Delegation Reference

### Agent Selection Guide

| Task Type | Agent | Reason |
|-----------|-------|--------|
| Find code patterns | `explore` | Fast codebase search |
| Library docs/examples | `librarian` | External knowledge |
| Architecture review | `oracle` | Deep analysis |
| Python implementation | `general` | Standard coding |
| TypeScript/React | `frontend-ui-ux-engineer` | UI expertise |
| Documentation | `document-writer` | Technical writing |

### Delegation Prompt Template

```
DELEGATE TO: {agent} agent
TASK: {One sentence description}
EXPECTED OUTCOME:
- {Specific deliverable 1}
- {Specific deliverable 2}
REQUIRED TOOLS: {Tool whitelist}
MUST DO:
- {Requirement 1}
- {Requirement 2}
MUST NOT DO:
- {Forbidden action 1}
- {Forbidden action 2}
CONTEXT:
- {File path or existing code}
- {Relevant patterns}
```

---

## Execution Order

1. **Phase 0** (parallel):
   - 0.1 + 0.2 + 0.3 + 0.4 can run simultaneously

2. **Phase 1** (sequential TDD):
   - 1.1 → 1.2 → 1.3 → 1.4 → 1.5 → 1.6 → 1.7 → 1.8

3. **Phase 2** (sequential TDD):
   - 2.1 → 2.2 → 2.3 → 2.4 → 2.5 → 2.6

4. **Phase 3** (parallel after 1 & 2):
   - 3.1 + 3.2 + 3.3 + 3.4 + 3.5

5. **Phase 4** (after Phase 3):
   - 4.1 → 4.2 → 4.3

6. **Phase 5** (after Phase 4):
   - 5.1 → 5.2 → 5.3

---

## Success Criteria

- [ ] All unit tests pass (< 5 seconds total)
- [ ] All integration tests pass
- [ ] Docker container builds successfully
- [ ] Health endpoint responds in container
- [ ] Terminal WebSocket works end-to-end
- [ ] React app works in web mode
- [ ] Deploys to Dokploy without errors
- [ ] Can create and run tasks via web UI
