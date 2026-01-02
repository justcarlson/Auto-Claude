# Prime Prompt: Auto-Claude Web Mode Full Audit

Copy everything below the line to start a new session.

---

## Context

Auto-Claude is an Electron desktop app being refactored for Docker/Dokploy deployment as a web app. Initial Docker infrastructure is complete, but many features still call Electron-only APIs (`window.electronAPI.*`) that don't work in web mode.

**Goal:** Full audit of codebase to identify and fix ALL `window.electronAPI` usages for web mode compatibility.

## Current State

### Completed Infrastructure
- **Backend API** (`apps/backend/api/`): FastAPI with REST + WebSocket
  - Health, Projects, Tasks CRUD endpoints
  - Terminal PTY service with WebSocket
- **Frontend API Layer** (`apps/frontend/src/renderer/lib/api/`):
  - `isWebMode()` detection using `import.meta.env.IS_WEB`
  - `WebAPIClient` for REST calls
  - `TerminalWebSocket` for terminal
- **Docker**: Dockerfile, docker-compose.yml, Caddyfile, start.sh
- **Web Build**: `vite.web.config.ts` with `IS_WEB=true`

### Partially Fixed (Setup Wizard Only)
| Component | Fix Applied |
|-----------|-------------|
| `OAuthStep.tsx` | Shows "Web Mode Detected" message, skips Electron auth |
| `OllamaModelSelector.tsx` | Shows manual model config instead of download UI |

### Known Scope (from previous analysis)
- **446 usages** of `window.electronAPI` across **98 files**
- Core stores updated: `project-store.ts`, `task-store.ts`, `settings-store.ts`
- Everything else still uses `window.electronAPI` directly

## Architecture

```
Frontend (React SPA)
    │
    ├── Electron Mode: window.electronAPI (IPC to main process)
    │
    └── Web Mode: WebAPIClient (REST/WebSocket to FastAPI)
            │
            └── FastAPI Backend (apps/backend/api/)
                    │
                    ├── /api/health
                    ├── /api/projects (CRUD)
                    ├── /api/projects/{id}/tasks (CRUD)
                    └── /ws/terminal/{session_id} (WebSocket PTY)
```

## Audit Requirements

### Phase 1: Discovery & Categorization
1. Find ALL `window.electronAPI` usages in frontend
2. Categorize each by:
   - **Already has backend endpoint** (just need to wire up WebAPIClient)
   - **Needs new backend endpoint** (implement in FastAPI)
   - **Electron-only feature** (hide in web mode or show alternative)
   - **Mock/stub acceptable** (non-critical, can no-op)

### Phase 2: TDD Implementation Plan
For each category, create detailed implementation tasks:
- **RED**: Write failing test first
- **GREEN**: Implement to pass
- **REFACTOR**: Clean up

### Phase 3: Priority Matrix
Rank by:
1. **Critical** - App unusable without it (auth, projects, tasks, terminal)
2. **Important** - Core features (settings, worktrees, git operations)
3. **Nice-to-have** - Enhanced features (GitHub, Linear, roadmap, changelog)
4. **Defer** - Can remain Electron-only for now

## Key Files to Audit

### API Layer
- `apps/frontend/src/renderer/lib/api/` - Current abstraction
- `apps/frontend/src/renderer/lib/browser-mock.ts` - Mock implementations
- `apps/frontend/src/renderer/stores/` - State management

### Features Using electronAPI
```
src/renderer/
├── components/
│   ├── onboarding/          # Setup wizard steps
│   ├── project-settings/    # Project configuration
│   ├── terminals/           # Terminal emulation
│   └── ...
├── features/
│   ├── tasks/              # Task management
│   ├── projects/           # Project management
│   ├── settings/           # App settings
│   ├── github/             # GitHub integration
│   ├── roadmap/            # Roadmap generation
│   ├── changelog/          # Release notes
│   ├── insights/           # Code analysis
│   ├── ideation/           # AI brainstorming
│   └── ...
└── stores/                 # Zustand stores
```

### Backend API (existing)
```
apps/backend/api/
├── main.py                 # FastAPI app
├── routes/
│   ├── health.py          # GET /api/health
│   ├── projects.py        # CRUD /api/projects
│   └── tasks.py           # CRUD /api/projects/{id}/tasks
├── services/
│   ├── project_service.py
│   ├── task_service.py
│   └── terminal_service.py
└── websocket/
    └── terminal.py        # WebSocket PTY handler
```

## Methodology

1. **TDD**: Write failing test FIRST, then implement
2. **No mocking in unit tests**: Design pure functions
3. **Incremental**: One feature at a time, all tests passing before next
4. **Web mode guards**: Use `isWebMode()` to conditionally render/execute

## APIClient Interface (Current)

```typescript
interface APIClient {
  // Projects
  getProjects(): Promise<Project[]>;
  addProject(project: Omit<Project, 'id'>): Promise<Project>;
  removeProject(id: string): Promise<void>;
  
  // Tasks
  getTasks(projectId: string): Promise<Task[]>;
  createTask(projectId: string, task: Partial<Task>): Promise<Task>;
  deleteTask(projectId: string, taskId: string): Promise<void>;
  startTask(projectId: string, taskId: string): Promise<void>;
  stopTask(projectId: string, taskId: string): Promise<void>;
  
  // Settings
  getSettings(): Promise<AppSettings>;
  saveSettings(settings: Partial<AppSettings>): Promise<void>;
}
```

**Needs expansion for:** Git operations, file system, Claude profiles, integrations, etc.

## Test Commands

```bash
# Backend API tests
cd apps/backend && .venv/bin/pytest api/tests/ -v

# Frontend tests
cd apps/frontend && npm test -- --run

# Docker tests
apps/backend/.venv/bin/pytest tests/docker/ -v

# TypeScript check
cd apps/frontend && npm run typecheck

# Build web bundle
cd apps/frontend && npm run build:web
```

## Instructions for Audit Agent

1. **Use ultrathink** for comprehensive analysis
2. **Grep for `window.electronAPI`** across all frontend files
3. **Categorize each usage** per the requirements above
4. **Create detailed TDD plan** with:
   - Test file locations
   - Expected test cases
   - Implementation approach
   - Priority level
5. **Output structured plan** that can be executed incrementally

## Output Format

The audit should produce a structured plan like:

```markdown
## Feature: [Feature Name]
### Category: [Already has endpoint | Needs endpoint | Electron-only | Mock OK]
### Priority: [Critical | Important | Nice-to-have | Defer]
### Files Affected:
- `path/to/file.tsx` (N usages)

### Current electronAPI calls:
- `window.electronAPI.someMethod()`
- `window.electronAPI.anotherMethod()`

### TDD Plan:
1. **Test**: `api/tests/routes/test_feature.py`
   - test_feature_get
   - test_feature_create
   - test_feature_error_handling
   
2. **Backend**: `api/routes/feature.py`
   - GET /api/feature
   - POST /api/feature
   
3. **Frontend**: `lib/api/types.ts`, `lib/api/web-client.ts`
   - Add to APIClient interface
   - Implement in WebAPIClient
   
4. **Component Update**: `components/Feature.tsx`
   - Replace window.electronAPI with getAPIClient()

### Estimated Effort: [S/M/L/XL]
```

---

## Start Command

```
Read /plans/WEBMODE_FULL_AUDIT_PRIME.md and perform a comprehensive audit of all window.electronAPI usages in the frontend codebase. Use ultrathink for thorough analysis. Categorize each usage and create a detailed TDD implementation plan.
```
