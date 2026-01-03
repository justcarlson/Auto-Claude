# Web Mode Full Migration Plan

**Generated:** 2026-01-03
**Branch:** `feat/webmode-api-parity`
**Status:** Planning Complete, Ready for Execution

---

## Executive Summary

Based on thorough exploration of the codebase, here's the complete picture:

| Metric | Count |
|--------|-------|
| **Total Files with `window.electronAPI`** | 91 |
| **Total Direct Usages** | 378 |
| **Unique ElectronAPI Methods** | 265+ |
| **Already in WebAPIClient** | ~35 methods |
| **Backend Endpoints Implemented** | ~45 |
| **Gap (Methods Needing Migration)** | ~230 |

### Architecture Overview

The frontend uses a **Strategy Pattern** for API abstraction:
- `APIClient` interface in `lib/api/types.ts`
- `WebAPIClient` for REST/WebSocket (Docker/Web mode)
- `ElectronAPIClient` for IPC (Desktop mode)
- `isWebMode()` detects environment via `import.meta.env.IS_WEB`
- `createAPIClient()` factory returns correct implementation

---

## Phase 1: Foundation (COMPLETE ✅)

Already implemented in Sprint 1-3.2:

| Feature | Backend Routes | Frontend Client | Status |
|---------|---------------|-----------------|--------|
| Settings API | GET/PUT `/api/settings` | ✅ WebAPIClient | Complete |
| Project Environment | GET/PUT `/api/projects/{id}/env` | ✅ WebAPIClient | Complete |
| Task Execution | POST `/api/tasks/{id}/start\|stop\|review` | ✅ WebAPIClient | Complete |
| Task Events WebSocket | WS `/ws/tasks/{id}/events` | ✅ WebAPIClient | Complete |
| Terminal PTY | POST/DELETE `/api/terminals`, WS `/ws/terminal/{id}` | ✅ TerminalWebSocket | Complete |
| Worktree Management | GET/POST `/api/worktrees/*` | ✅ WebAPIClient | Complete |
| Git Operations | GET/POST `/api/projects/{id}/git/*` | ✅ WebAPIClient | Complete |
| Filesystem | GET `/api/fs/list\|read` | ✅ WebAPIClient | Complete |
| Task Logs | GET `/api/tasks/{id}/logs` | ✅ WebAPIClient | Complete |
| Web Mode Guards | - | ✅ `isWebMode()` guards | Complete |

**Backend Tests:** 144 passing

---

## Phase 2: Store Migration

Migrate Zustand stores from direct `window.electronAPI` to `getAPIClient()`.

### Priority 1: Critical Stores (7 files, ~50 usages)

| Store | Usages | Methods to Migrate | Effort | Backend Needed |
|-------|--------|-------------------|--------|----------------|
| `task-store.ts` | 8 | `createTask`, `updateTask`, `archiveTasks`, `deleteTask` | 2 hrs | No |
| `project-store.ts` | 5 | `saveTabState`, `getTabState`, `initializeProject`, `updateProjectSettings` | 1.5 hrs | Partial |
| `settings-store.ts` | 3 | Already migrated via `getAPIClient()` | ✅ Done | No |
| `terminal-store.ts` | 4 | `getTerminalSessions`, `checkTerminalPtyAlive` | 1 hr | No |
| `context-store.ts` | 5 | `getProjectContext`, `searchMemories`, `refreshContextIndex` | 2 hrs | Yes |

**Subtotal: ~6.5 hours**

### Priority 2: Feature Stores (4 files, ~52 usages)

| Store | Usages | Requires Backend | Effort |
|-------|--------|------------------|--------|
| `ideation-store.ts` | 17 | Yes - New routes + WebSocket | 6 hrs |
| `insights-store.ts` | 13 | Yes - New routes + SSE/WebSocket | 8 hrs |
| `changelog-store.ts` | 10 | Yes - New routes | 4 hrs |
| `roadmap-store.ts` | 7 | Yes - New routes | 3 hrs |

**Subtotal: ~21 hours**

### Priority 3: Integration Stores (4 files, ~15 usages)

| Store | Usages | Requires Backend | Effort |
|-------|--------|------------------|--------|
| `github/issues-store.ts` | 2 | Yes - Proxy routes | 4 hrs |
| `github/pr-review-store.ts` | 4 | Yes - Proxy routes + WS | 8 hrs |
| `gitlab-store.ts` | 4 | Yes - Proxy routes | 4 hrs |
| `gitlab/mr-review-store.ts` | 6 | Yes - Proxy routes + WS | 8 hrs |

**Subtotal: ~24 hours**

---

## Phase 3: Hook Migration

### Central Hook: `useIpc.ts` (15 usages) - CRITICAL PATH

This hook aggregates 11+ event listeners used across the app:
- `onTaskProgress`, `onTaskError`, `onTaskLog`, `onTaskStatusChange`
- `onTaskExecutionProgress`
- `onRoadmapProgress`, `onRoadmapComplete`, `onRoadmapError`, `onRoadmapStopped`
- `onSDKRateLimit`, `onTerminalRateLimit`

**Migration Strategy:**
1. Create `useApiEvents.ts` hook that abstracts event sources
2. In Electron: Use IPC listeners
3. In Web: Use WebSocket subscriptions from `getAPIClient()`

**Effort: 4 hours**

### Feature Hooks (20+ files, ~80 usages)

| Hook Category | Files | Key Hooks | Effort |
|--------------|-------|-----------|--------|
| GitHub Hooks | 6 | `useAutoFix`, `useGitHubPRs`, `useGitHubIssues` | 12 hrs |
| GitLab Hooks | 5 | `useGitLabMRs`, `useGitLabIssues`, `useGitLabInvestigation` | 10 hrs |
| Terminal Hooks | 4 | `usePtyProcess`, `useTerminalEvents`, `useAutoNaming` | 4 hrs |
| Task Hooks | 2 | `useTaskDetail`, `useTaskLogs` | 3 hrs |
| Settings Hooks | 2 | `useProjectSettings`, `useClaudeProfiles` | 2 hrs |

**Subtotal: ~31 hours**

---

## Phase 4: Component Migration

### High-Usage Components (Top 20)

| Rank | File | Usages | Category | Effort |
|------|------|--------|----------|--------|
| 1 | `IntegrationSettings.tsx` | 11 | Settings | 2 hrs |
| 2 | `GitLabIntegration.tsx` | 10 | Settings | 2 hrs |
| 3 | `GitHubSetupModal.tsx` | 9 | Onboarding | 2 hrs |
| 4 | `OAuthStep.tsx` | 9 | Onboarding | 2 hrs |
| 5 | `AdvancedSettings.tsx` | 9 | Settings | 1.5 hrs |
| 6 | `AddProjectModal.tsx` | 8 | Projects | ✅ Done |
| 7 | `TerminalGrid.tsx` | 8 | Terminal | 2 hrs |
| 8 | `AgentTools.tsx` | 7 | MCP | 2 hrs |
| 9 | `EnvConfigModal.tsx` | 7 | Config | 1.5 hrs |
| 10 | `useTaskDetail.ts` | 7 | Tasks | 2 hrs |
| 11-20 | Various | 40 | Mixed | 8 hrs |

**Subtotal: ~25 hours**

### Remaining Components (~50 files, ~150 usages)

Lower-priority components with 1-5 usages each.

**Effort: ~20 hours** (batched migration)

---

## Phase 5: Backend API Expansion

### 5.1 AI Features (~42 methods)

| Feature | Routes Needed | WebSocket | Effort |
|---------|--------------|-----------|--------|
| **Insights** | `/api/projects/{id}/insights/*` (8 routes) | SSE for streaming | 10 hrs |
| **Ideation** | `/api/projects/{id}/ideation/*` (7 routes) | WS for parallel logs | 8 hrs |
| **Roadmap** | `/api/projects/{id}/roadmap/*` (5 routes) | Progress events | 5 hrs |
| **Changelog** | `/api/projects/{id}/changelog/*` (8 routes) | Progress events | 6 hrs |

**Subtotal: ~29 hours**

### 5.2 Integration Proxies (~120 methods)

| Integration | Methods | Auth Complexity | Effort |
|-------------|---------|-----------------|--------|
| **GitHub** | 52 | OAuth via `gh` CLI or PAT | 25 hrs |
| **GitLab** | 64 | PAT + Multi-instance | 30 hrs |
| **Linear** | 5 | API Key | 3 hrs |

**Subtotal: ~58 hours**

### 5.3 Supporting APIs (~20 methods)

| API | Routes | Effort |
|-----|--------|--------|
| Claude Profiles | CRUD + auto-switch | 4 hrs |
| MCP Management | Health check, test | 2 hrs |
| Debug Info | System info, logs | 2 hrs |

**Subtotal: ~8 hours**

---

## Phase 6: Event System Unification

### Event Patterns (29+ listener types)

| Domain | Events | WebSocket Topic |
|--------|--------|-----------------|
| Tasks | `onTaskProgress`, `onTaskLog`, `onTaskError`, `onTaskStatusChange` | `/ws/tasks/{id}/events` ✅ |
| Terminal | `onTerminalOutput`, `onTerminalExit`, `onTerminalTitleChange` | `/ws/terminal/{id}` ✅ |
| Ideation | `onIdeationProgress`, `onIdeationLog`, `onIdeationComplete` | `/ws/ideation/{id}` |
| Insights | `onInsightsStreamChunk`, `onInsightsStatus` | `/ws/insights/{id}` |
| GitHub | `onPRReviewProgress`, `onAutoFixProgress` (8 types) | `/ws/github/{project}/events` |
| GitLab | `onMRReviewProgress`, `onTriageProgress` (9 types) | `/ws/gitlab/{project}/events` |
| Roadmap | `onRoadmapProgress`, `onRoadmapComplete` | `/ws/roadmap/{id}` |
| Changelog | `onChangelogProgress` | `/ws/changelog/{id}` |
| App | `onAppUpdateAvailable`, `onUsageUpdated` | N/A (Electron only) |

### Migration Strategy

1. **Create `WebEventBus`** - Unified WebSocket multiplexer
2. **Topic-based routing** - Single WS connection, multiple subscriptions
3. **Fallback to IPC** - When in Electron mode

**Effort: 12 hours**

---

## Total Effort Estimate

| Phase | Hours | Dependencies |
|-------|-------|--------------|
| Phase 1: Foundation | ✅ Complete | - |
| Phase 2: Store Migration | 51.5 hrs | Backend APIs for features |
| Phase 3: Hook Migration | 35 hrs | Stores migrated |
| Phase 4: Component Migration | 45 hrs | Hooks migrated |
| Phase 5: Backend Expansion | 95 hrs | Python services |
| Phase 6: Event Unification | 12 hrs | WebSocket infrastructure |

**Grand Total: ~238.5 hours (~30 working days)**

---

## Recommended Execution Order

### Sprint A: Core Store Migration (1 week)
**Goal:** Migrate critical stores that don't need new backend APIs

1. [ ] Migrate `task-store.ts` to use `getAPIClient()`
2. [ ] Migrate `project-store.ts` to use `getAPIClient()`
3. [ ] Migrate `terminal-store.ts` to use `getAPIClient()`
4. [ ] Create `useApiEvents.ts` to replace `useIpc.ts`
5. [ ] Update components that only use core stores

### Sprint B: Task Detail Flow (1 week)
**Goal:** Complete the task viewing/editing flow

1. [ ] Migrate `useTaskDetail.ts` hook
2. [ ] Migrate `TaskDetailModal.tsx` and related components
3. [ ] Migrate `Worktrees.tsx` component
4. [ ] Add any missing backend endpoints

### Sprint C: AI Features Backend (2 weeks)
**Goal:** Implement backend APIs for AI features

1. [ ] Implement `/api/projects/{id}/insights/*` routes + WebSocket
2. [ ] Implement `/api/projects/{id}/ideation/*` routes + WebSocket
3. [ ] Implement `/api/projects/{id}/roadmap/*` routes
4. [ ] Implement `/api/projects/{id}/changelog/*` routes
5. [ ] Migrate corresponding stores: `insights-store.ts`, `ideation-store.ts`, `roadmap-store.ts`, `changelog-store.ts`

### Sprint D: GitHub Integration (1.5 weeks)
**Goal:** Full GitHub support in web mode

1. [ ] Implement `/api/projects/{id}/github/*` proxy routes (52 methods)
2. [ ] Implement `/ws/github/{project}/events` WebSocket
3. [ ] Migrate `github/` stores
4. [ ] Migrate `useAutoFix.ts`, `useGitHubPRs.ts`, `useGitHubIssues.ts`
5. [ ] Migrate GitHub components

### Sprint E: GitLab Integration (1.5 weeks)
**Goal:** Full GitLab support in web mode

1. [ ] Implement `/api/projects/{id}/gitlab/*` proxy routes (64 methods)
2. [ ] Implement `/ws/gitlab/{project}/events` WebSocket
3. [ ] Migrate `gitlab/` stores
4. [ ] Migrate `useGitLabMRs.ts`, `useGitLabIssues.ts`
5. [ ] Migrate GitLab components

### Sprint F: Cleanup & Polish (1 week)
**Goal:** Zero `window.electronAPI` calls remaining

1. [ ] Migrate remaining low-usage components (~50 files)
2. [ ] Audit for any remaining direct `window.electronAPI` calls
3. [ ] Comprehensive testing in both modes
4. [ ] Update documentation

---

## File-by-File Migration Checklist

### Stores (18 files)

#### Critical (Phase 2, Priority 1)
- [ ] `stores/task-store.ts` (8 usages)
- [ ] `stores/project-store.ts` (5 usages)
- [x] `stores/settings-store.ts` (3 usages) ✅
- [ ] `stores/terminal-store.ts` (4 usages)
- [ ] `stores/context-store.ts` (5 usages)

#### Feature (Phase 2, Priority 2) - Needs Backend
- [ ] `stores/ideation-store.ts` (17 usages)
- [ ] `stores/insights-store.ts` (13 usages)
- [ ] `stores/changelog-store.ts` (10 usages)
- [ ] `stores/roadmap-store.ts` (7 usages)

#### Integration (Phase 2, Priority 3) - Needs Backend
- [ ] `stores/github/issues-store.ts` (2 usages)
- [ ] `stores/github/pr-review-store.ts` (4 usages)
- [ ] `stores/github/investigation-store.ts` (1 usage)
- [ ] `stores/github/sync-status-store.ts` (1 usage)
- [ ] `stores/gitlab-store.ts` (4 usages)
- [ ] `stores/gitlab/mr-review-store.ts` (6 usages)

#### Other
- [ ] `stores/file-explorer-store.ts` (3 usages)
- [ ] `stores/download-store.ts` (2 usages)
- [ ] `stores/usage-store.ts` (2 usages)

### Hooks (11 files)

- [ ] `hooks/useIpc.ts` (15 usages) - **Priority 1**
- [ ] `components/task-detail/hooks/useTaskDetail.ts` (7 usages)
- [ ] `components/project-settings/hooks/useProjectSettings.ts` (10 usages)
- [ ] `components/gitlab-merge-requests/hooks/useGitLabMRs.ts` (20 usages)
- [ ] `components/github-issues/hooks/useAutoFix.ts` (14 usages)
- [ ] `components/github-prs/hooks/useGitHubPRs.ts` (12 usages)
- [ ] `components/terminal/useTerminalEvents.ts` (6 usages)
- [ ] `components/terminal/usePtyProcess.ts` (4 usages)
- [ ] `components/terminal/useAutoNaming.ts` (2 usages)
- [ ] `hooks/useClaudeProfile.ts` (3 usages)
- [ ] `components/github-issues/hooks/useAnalyzePreview.ts` (4 usages)

### Components (58 files - Top 20)

- [ ] `components/settings/IntegrationSettings.tsx` (11 usages)
- [ ] `components/settings/integrations/GitLabIntegration.tsx` (10 usages)
- [ ] `components/GitHubSetupModal.tsx` (9 usages)
- [ ] `components/onboarding/OAuthStep.tsx` (9 usages)
- [ ] `components/settings/AdvancedSettings.tsx` (9 usages)
- [x] `components/AddProjectModal.tsx` (8 usages) ✅
- [ ] `components/TerminalGrid.tsx` (8 usages)
- [ ] `components/AgentTools.tsx` (7 usages)
- [ ] `components/EnvConfigModal.tsx` (7 usages)
- [ ] `components/SDKRateLimitModal.tsx` (6 usages)
- [x] `components/ClaudeCodeStatusBadge.tsx` (4 usages) ✅
- [x] `components/onboarding/ClaudeCodeStep.tsx` (4 usages) ✅
- [x] `components/onboarding/OllamaModelSelector.tsx` (6 usages) ✅
- [x] `components/CustomMcpDialog.tsx` (4 usages) ✅
- [x] `components/AppUpdateNotification.tsx` (5 usages) ✅
- [x] `components/settings/DebugSettings.tsx` (3 usages) ✅
- [x] `components/task-detail/TaskFiles.tsx` (3 usages) ✅
- [x] `components/task-detail/task-review/WorkspaceStatus.tsx` (4 usages) ✅
- [ ] `components/Sidebar.tsx` (3 usages)
- [ ] `App.tsx` (4 usages)

### Remaining Components (~38 files)
Low-priority files with 1-5 usages each - batch migrate in Sprint F.

---

## Backend Routes to Implement

### Already Implemented ✅
```
GET    /health
GET    /api/version
GET    /api/settings
PUT    /api/settings
GET    /api/projects
POST   /api/projects
GET    /api/projects/{id}
DELETE /api/projects/{id}
GET    /api/projects/{id}/env
PUT    /api/projects/{id}/env
GET    /api/projects/{id}/tasks
POST   /api/projects/{id}/tasks
GET    /api/projects/{id}/tasks/{task_id}
PUT    /api/projects/{id}/tasks/{task_id}
DELETE /api/projects/{id}/tasks/{task_id}
POST   /api/tasks/{id}/start
POST   /api/tasks/{id}/stop
POST   /api/tasks/{id}/review
PUT    /api/tasks/{id}/status
GET    /api/tasks/{id}/running
POST   /api/tasks/{id}/recover
GET    /api/tasks/{id}/logs
GET    /api/projects/{id}/worktrees
GET    /api/worktrees/{id}/status
GET    /api/worktrees/{id}/diff
GET    /api/worktrees/{id}/merge/preview
POST   /api/worktrees/{id}/merge
POST   /api/worktrees/{id}/discard
GET    /api/projects/{id}/git/branches
GET    /api/projects/{id}/git/status
GET    /api/projects/{id}/git/main-branch
POST   /api/projects/{id}/git/init
GET    /api/fs/list
GET    /api/fs/read
POST   /api/terminals
DELETE /api/terminals/{id}
GET    /api/terminals/sessions
GET    /api/terminals/{id}/alive
WS     /ws/terminal/{id}
WS     /ws/tasks/{id}/events
```

### To Implement

#### AI Features
```
# Insights
GET    /api/projects/{id}/insights/sessions
POST   /api/projects/{id}/insights/sessions
GET    /api/projects/{id}/insights/sessions/{sid}
DELETE /api/projects/{id}/insights/sessions/{sid}
PUT    /api/projects/{id}/insights/sessions/{sid}
POST   /api/projects/{id}/insights/message
WS     /ws/insights/{project_id}

# Ideation  
GET    /api/projects/{id}/ideation
POST   /api/projects/{id}/ideation/generate
POST   /api/projects/{id}/ideation/stop
DELETE /api/projects/{id}/ideation/ideas/{idea_id}
POST   /api/projects/{id}/ideation/ideas/{idea_id}/archive
POST   /api/projects/{id}/ideation/ideas/{idea_id}/to-task
WS     /ws/ideation/{project_id}

# Roadmap
GET    /api/projects/{id}/roadmap
POST   /api/projects/{id}/roadmap/generate
POST   /api/projects/{id}/roadmap/stop
PUT    /api/projects/{id}/roadmap
POST   /api/projects/{id}/roadmap/features/{fid}/to-spec
WS     /ws/roadmap/{project_id}

# Changelog
GET    /api/projects/{id}/changelog
POST   /api/projects/{id}/changelog/generate
PUT    /api/projects/{id}/changelog
GET    /api/projects/{id}/changelog/branches
GET    /api/projects/{id}/changelog/tags
GET    /api/projects/{id}/changelog/commits-preview
POST   /api/projects/{id}/changelog/suggest-version
```

#### GitHub Integration
```
# Auth
GET    /api/github/auth/status
POST   /api/github/auth/start
GET    /api/github/token
GET    /api/github/user

# Issues
GET    /api/projects/{id}/github/issues
GET    /api/projects/{id}/github/issues/{num}
GET    /api/projects/{id}/github/issues/{num}/comments
POST   /api/projects/{id}/github/issues/import
POST   /api/projects/{id}/github/issues/{num}/investigate

# PRs
GET    /api/projects/{id}/github/prs
GET    /api/projects/{id}/github/prs/{num}
POST   /api/projects/{id}/github/prs/{num}/review
POST   /api/projects/{id}/github/prs/{num}/review/cancel
POST   /api/projects/{id}/github/prs/{num}/review/post
POST   /api/projects/{id}/github/prs/{num}/merge

# AutoFix
GET    /api/projects/{id}/github/autofix/config
PUT    /api/projects/{id}/github/autofix/config
GET    /api/projects/{id}/github/autofix/queue
POST   /api/projects/{id}/github/autofix/start
POST   /api/projects/{id}/github/autofix/batch

# WebSocket
WS     /ws/github/{project_id}/events
```

#### GitLab Integration
```
# Similar structure to GitHub with 64 methods
# Including multi-instance support via instanceUrl parameter
```

---

## Success Criteria

1. **Zero `window.electronAPI` calls** in renderer code
2. **All features work** in both Electron and Web modes
3. **144+ backend tests** continue passing
4. **TypeScript compiles** with no errors
5. **Web build** (`npm run build:web`) succeeds
6. **No regressions** in Electron mode

---

## Testing Commands

```bash
# Backend API tests
cd apps/backend && .venv/bin/pytest api/tests/ -v

# Frontend type check
cd apps/frontend && npm run typecheck

# Count remaining electronAPI usages
grep -r "window\.electronAPI" apps/frontend/src/renderer --include="*.ts" --include="*.tsx" | wc -l

# Build web bundle
cd apps/frontend && npm run build:web
```

---

## Related Documents

- `plans/WEBMODE_AUDIT_RESULTS_COMPLETE.md` - Original audit (Phase 1 implementation details)
- `plans/WEBMODE_EXECUTION_PRIME_COMPLETE.md` - Sprint 1-2 execution guide
- `plans/DOKPLOY_DOCKER_DEPLOYMENT.md` - Docker deployment configuration
