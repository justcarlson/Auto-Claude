# Prime Prompt: Auto-Claude Dokploy Docker Deployment

Copy everything below the line to start a new session.

---

## Context

I'm refactoring Auto-Claude (Electron desktop app) to be deployable via **Dokploy** (Docker-based PaaS). 

**Key files:**
- Plan: `/plans/DOKPLOY_DOCKER_DEPLOYMENT.md` - Complete TDD implementation plan
- Existing design: `/shared_docs/DOCKER_NATIVE_DESIGN.md` - Architecture reference
- Backend: `/apps/backend/` - Python agents, Claude SDK integration
- Frontend: `/apps/frontend/` - Electron + React app

## Architecture Change

**From:** Electron IPC → Python backend  
**To:** React SPA → FastAPI (REST + WebSocket) → Python backend → Docker container

## Methodology

1. **TDD**: Red-Green-Refactor. Write failing test FIRST, then implement.
2. **No mocking in unit tests**: Design pure functions for testability.

---

## Current Progress (1044 tests passing)

### Completed Phases

| Phase | Description | Tests | Status |
|-------|-------------|-------|--------|
| 0.1 | Backend Pytest Infrastructure | - | ✅ |
| 0.2 | Frontend Vitest Infrastructure | - | ✅ |
| 0.3 | GitHub Actions TDD CI | - | ✅ |
| 0.4 | Docker Test Infrastructure | - | ✅ |
| 1.1 | Health Endpoint | 3 | ✅ |
| 1.2 | Projects CRUD API | 9 | ✅ |
| 1.3 | Tasks CRUD API | 17 | ✅ |
| 1.4 | Terminal PTY Service | 23 | ✅ |
| 1.5 | WebSocket Terminal Handler | 8 | ✅ |
| 2.1 | APIClient Interface | - | ✅ |
| 2.2 | WebAPIClient | - | ✅ |
| 2.3 | ElectronAPIClient | - | ✅ |
| 2.4 | TerminalWebSocket Client | 21 | ✅ |
| 2.5 | Vite Web Build Config | - | ✅ |
| 2.6 | Update React Components (Core Stores) | - | ✅ |
| 3.1 | Dockerfile | 10 | ✅ |
| 3.2 | docker-compose.yml | 9 | ✅ |
| 3.3 | Caddyfile (Reverse Proxy) | - | ✅ |
| 3.4 | start.sh (Entrypoint) | - | ✅ |

| 4.1 | UI Smoke Test (Playwriter MCP) | - | ✅ |
| 4.2 | Full Workflow Test (Playwriter MCP) | - | ✅ |
| 4.3 | Terminal E2E Test (Playwriter MCP) | - | ✅ |
| 5.1 | Web Mode Detection Fix | - | ✅ |
| 5.2 | Ollama Model Selector Web Mode Fix | - | ✅ |

### Next Pending (High Priority)

| Phase | Description |
|-------|-------------|
| **5.3** | Dokploy Deployment Guide |

---

## Key File Locations

### Backend API (apps/backend/api/)
```
api/
├── main.py                 # FastAPI app with routers + WebSocket
├── routes/
│   ├── health.py           # GET /api/health
│   ├── projects.py         # CRUD /api/projects
│   └── tasks.py            # CRUD /api/projects/{id}/tasks
├── services/
│   ├── project_service.py  # Project storage (singleton)
│   ├── task_service.py     # Task storage (singleton)
│   └── terminal_service.py # TerminalManager + PTY
├── websocket/
│   ├── __init__.py         # Exports terminal_websocket
│   └── terminal.py         # WebSocket handler for PTY
├── models/
│   └── api_models.py       # Pydantic models
└── tests/
    ├── conftest.py         # Fixtures, service reset
    ├── routes/
    │   ├── test_health.py      # 3 tests
    │   ├── test_projects.py    # 9 tests
    │   └── test_tasks.py       # 17 tests
    ├── services/
    │   ├── test_terminal_service.py      # 13 unit tests
    │   └── test_terminal_integration.py  # 10 PTY tests
    └── websocket/
        └── test_terminal_ws.py           # 8 WebSocket tests
```

### Frontend API Client (apps/frontend/src/renderer/lib/api/)
```
api/
├── index.ts            # getAPIClient() singleton, isWebMode()
├── types.ts            # APIClient interface
├── client.ts           # createAPIClient() factory
├── web-client.ts       # WebAPIClient (fetch)
├── electron-client.ts  # ElectronAPIClient (IPC)
├── terminal-client.ts  # TerminalWebSocket (WebSocket)
└── __tests__/
    └── terminal-ws.test.ts # 21 WebSocket tests
```

### Frontend Stores Using API Client (apps/frontend/src/renderer/stores/)
```
stores/
├── project-store.ts    # Uses API client for CRUD
├── task-store.ts       # Uses API client for CRUD
└── settings-store.ts   # Uses API client for get/save
```

### Frontend Build Configs (apps/frontend/)
```
├── electron.vite.config.ts  # Electron build (main/preload/renderer)
├── vite.web.config.ts       # Web-only build (IS_WEB=true) → dist/web/
└── package.json             # build:web script added
```

### Docker Configuration (project root)
```
├── Dockerfile              # Multi-stage build (frontend → python → production)
├── docker-compose.yml      # Service definition with volumes, env vars, Traefik labels
└── docker/
    ├── Caddyfile           # Reverse proxy: SPA + /api/* + /ws/* → FastAPI
    └── start.sh            # Entrypoint: uvicorn + caddy
```

### Docker Tests (tests/docker/)
```
tests/docker/
├── __init__.py
├── test_dockerfile.py      # 10 structure/security tests
├── test_compose.py         # 9 compose validation tests
└── test_container.sh       # Integration test (requires Docker daemon)
```

---

## How to Run Tests

```bash
# Backend API tests (60 tests, ~6s)
cd apps/backend
.venv/bin/pytest api/tests/ -v

# Docker tests (19 tests, <1s) - from project root
apps/backend/.venv/bin/pytest tests/docker/ -v

# Frontend tests (965 tests, ~20s)
cd apps/frontend
npm test -- --run

# Frontend API tests only (21 tests, <1s)
cd apps/frontend
npm test -- --run src/renderer/lib/api/

# Build web bundle (outputs to dist/web/)
cd apps/frontend
npm run build:web

# TypeScript check
cd apps/frontend
npm run typecheck

# Container integration test (requires Docker daemon)
bash tests/docker/test_container.sh
```

---

## Instructions

1. Run `todoread` to see current task status
2. Find the next `pending` high-priority task
3. Follow TDD cycle:
   - **RED**: Write failing test first
   - **GREEN**: Implement to make test pass
   - **REFACTOR**: Clean up while tests pass
4. Run tests: `.venv/bin/pytest api/tests/ -v`
5. Mark task `completed` when tests pass
6. Update this prime prompt with new progress before ending session

---

## Phase 2.6 Summary (COMPLETED)

Updated core React stores to use API abstraction layer:

**What was done:**
1. Created singleton API client (`getAPIClient()`) in `lib/api/index.ts`
2. Added `isWebMode()` helper to detect runtime environment
3. Updated `project-store.ts` - uses API client for getProjects, addProject, removeProject
4. Updated `task-store.ts` - uses API client for getTasks, createTask, deleteTask, startTask, stopTask
5. Updated `settings-store.ts` - uses API client for getSettings, saveSettings
6. Added web-mode guards for Electron-only features (graceful no-ops)

**Files modified:**
- `apps/frontend/src/renderer/lib/api/index.ts` - Added getAPIClient singleton
- `apps/frontend/src/renderer/stores/project-store.ts`
- `apps/frontend/src/renderer/stores/task-store.ts`
- `apps/frontend/src/renderer/stores/settings-store.ts`

**Scope note:** 446 usages of `window.electronAPI` exist across 98 files. Phase 2.6 focused on the 3 core stores matching the APIClient interface. Other features (GitHub, GitLab, roadmap, changelog, etc.) still use `window.electronAPI` directly - they won't work in web mode until backend endpoints are added in future phases.

## Phase 3 Summary (COMPLETED)

Docker Configuration for Dokploy deployment - all files created and validated.

**Files created:**
- `Dockerfile` - Multi-stage build (Node.js frontend → Python backend → Caddy production)
- `docker-compose.yml` - Service with volumes, env vars, Traefik labels
- `docker/Caddyfile` - Reverse proxy (SPA + API + WebSocket)
- `docker/start.sh` - Entrypoint (uvicorn + caddy)

**Test results:**
- 10 Dockerfile structure/security tests passing
- 9 docker-compose.yml validation tests passing
- Web build succeeds (dist/web/)

**Build command:**
```bash
docker build -t auto-claude .
docker run -d -p 3000:3000 \
  -e CLAUDE_CODE_OAUTH_TOKEN=your-token \
  -v ./projects:/projects \
  auto-claude
```

**Integration test:**
```bash
bash tests/docker/test_container.sh  # Requires Docker daemon
```

## Phase 5.2 Summary (COMPLETED)

Ollama Model Selector Web Mode Fix - Memory step now works correctly in Docker/Dokploy deployment.

**Problem:**
- Download/Select embedding model buttons didn't work in web mode
- Component called `window.electronAPI.checkOllamaInstalled()`, `pullOllamaModel()` etc. which don't exist in web mode

**Solution:**
- Added `isWebMode()` check to `OllamaModelSelector.tsx`
- In web mode, shows "External Ollama Required" info card
- Provides manual model name/dimensions input fields
- User can configure model settings and click "Apply" to proceed

**Files Modified:**
- `apps/frontend/src/renderer/components/onboarding/OllamaModelSelector.tsx`

**Web Mode UI:**
- Shows instructions for running Ollama externally (host or sidecar container)
- Input fields for model name (default: nomic-embed-text) and dimensions (default: 768)
- Apply button to confirm selection
- "Selected: <model>" confirmation shown after apply

**Test Results:**
| Test | Result |
|------|--------|
| Web mode info card shows | ✅ |
| Model name input works | ✅ |
| Dimensions input works | ✅ |
| Apply button works | ✅ |
| Save & Continue proceeds to Done step | ✅ |

---

## Phase 5.1 Summary (COMPLETED)

Web Mode Detection Fix - Setup Wizard now works correctly in Docker/Dokploy deployment.

**Root Cause:**
- `browser-mock.ts` creates a mock `window.electronAPI` for browser development
- `isWebMode()` was checking `!isElectron()` which relies on `window.electronAPI` absence
- In Docker, the mock was created, causing `isWebMode()` to return false

**Fix Applied:**
- Updated `lib/api/client.ts` to use `import.meta.env.IS_WEB` (set by vite.web.config.ts)
- `isWebMode()` now returns true only in production web builds (Docker/Dokploy)
- `isElectron()` explicitly returns false when `IS_WEB` is set

**Files Modified:**
- `apps/frontend/src/renderer/lib/api/client.ts` - Updated environment detection logic

**Test Results:**
| Test | Result |
|------|--------|
| Auth step shows "Web Mode Detected" card | ✅ |
| Continue button enabled | ✅ |
| Wizard navigation works | ✅ |

## Phase 4 Summary (COMPLETED)

E2E Testing via Playwriter MCP - all tests passed.

**Bug Found & Fixed:**
- Caddyfile had `try_files` before `handle /api/*` blocks
- API routes were falling through to SPA (returning HTML instead of JSON)
- Fixed by wrapping static file serving in catch-all `handle` block

**Test Results:**
| Test | Result |
|------|--------|
| UI Smoke Test | ✅ Page renders, no console errors |
| Health API | ✅ `{"status":"ok","version":"0.1.0"}` |
| Projects API | ✅ Create, list working |
| Tasks API | ✅ Create, list working |
| WebSocket Terminal | ✅ Connects, receives PTY output |

**Playwriter Commands Used:**
```js
// Accessibility snapshot
await accessibilitySnapshot({ page })

// API test via evaluate
await page.evaluate(async () => { 
  const res = await fetch('/api/health'); 
  return await res.json(); 
})

// WebSocket terminal test
const ws = new WebSocket('ws://localhost:3000/ws/terminal/session-id')

// Close dialogs
await page.keyboard.press('Escape')
```

## Phase 5 Quick Reference (NEXT)

Dokploy deployment guide and final documentation.

---

## Key Constraints

- **Private deployment**: No auth needed (Tailnet only)
- **Full terminal support**: WebSocket + ptyprocess from day 1
- **Must work in both modes**: Electron (existing) + Web (new)
- **Tests first**: Never implement without failing test
- **E2E testing**: Use Playwriter MCP for browser automation (user attaches Chrome extension)

---

## Start Command

```
Read /plans/DOKPLOY_PRIME_PROMPT.md and follow the instructions.
```
