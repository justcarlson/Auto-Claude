# Auto-Claude Web Mode Full Audit Results

**Generated:** 2026-01-02 (Updated)  
**Scope:** 482 usages across 102 files (refined count)  
**Current WebAPIClient Coverage:** ~15 methods (~3% of total API surface)  
**ElectronAPI Interface:** ~200+ methods across 15 domains

---

## Execution Context

| Field | Value |
|-------|-------|
| **Branch** | `feat/webmode-api-parity` |
| **Base** | `develop` |
| **Execution Mode** | Continuous autonomous (stop only when human input required) |
| **Approach** | TDD (tests → implement → migrate) |

### Current Progress
- [ ] **Sprint 1: Critical MVP**
  - [x] 1.1 Settings API
  - [x] 1.2 Project Environment
  - [ ] 1.3 Task Execution + WebSocket
  - [ ] 1.4 Terminal Enhancement
- [ ] **Sprint 2: Core Features**
  - [ ] 2.1 Worktree Management
  - [ ] 2.2 Git Operations
  - [ ] 2.3 File System
  - [ ] 2.4 Task Logs
- [ ] **Sprint 3: Polish**
  - [ ] 3.1 Claude Profile Management
  - [ ] 3.2 Web Mode Guards
- [ ] **Sprint 4: Enhanced** (Deferred)
- [ ] **Sprint 5: Integrations** (Deferred)

---

## Executive Summary

The Auto-Claude frontend has **massive Electron dependency**. The existing `WebAPIClient` abstraction only covers basic CRUD operations for projects, tasks, and settings. The remaining ~97% of API calls go directly to `window.electronAPI` without web mode guards.

### Statistics by Category

| Category | Methods | Priority | Web Feasibility |
|----------|---------|----------|-----------------|
| **Core (Projects/Tasks)** | ~55 | Critical | Full |
| **Terminal** | ~15 | Critical | Full (WebSocket PTY) |
| **Settings** | ~10 | Critical | Full |
| **GitHub Integration** | ~65 | Important | Partial (needs backend proxy) |
| **GitLab Integration** | ~55 | Important | Partial (needs backend proxy) |
| **Insights (AI Chat)** | ~15 | Important | Full (streaming WS) |
| **Ideation** | ~15 | Nice-to-have | Full |
| **Roadmap** | ~10 | Nice-to-have | Full |
| **Changelog** | ~15 | Nice-to-have | Full |
| **App Update** | ~10 | Defer | Electron-only |
| **Claude Code CLI** | ~5 | Defer | Electron-only |
| **Ollama Local** | ~10 | Defer | Electron-only |
| **Debug/Logs** | ~5 | Defer | Partial |
| **File Dialogs** | ~5 | Defer | Browser alternatives |

---

## Phase 1: Critical Features

### Feature: Projects & Tasks Core
**Category:** Already has partial backend endpoint  
**Priority:** Critical  
**Files Affected:**
- `stores/task-store.ts` (9 usages)
- `stores/project-store.ts` (5 usages)
- `components/AddProjectModal.tsx` (8 usages)
- `components/TaskCreationWizard.tsx` (3 usages)
- `components/Worktrees.tsx` (3 usages)

#### Current electronAPI calls:
```typescript
// Task operations (task-store.ts)
window.electronAPI.createTask(projectId, title, description, metadata)
window.electronAPI.startTask(taskId, options)
window.electronAPI.submitReview(taskId, approved, feedback)
window.electronAPI.updateTaskStatus(taskId, status)
window.electronAPI.updateTask(taskId, updates)
window.electronAPI.checkTaskRunning(taskId)
window.electronAPI.recoverStuckTask(taskId, options)
window.electronAPI.archiveTasks(projectId, taskIds, version)

// Project operations (project-store.ts)
window.electronAPI.saveTabState(tabState)
window.electronAPI.getTabState()
window.electronAPI.updateProjectSettings(projectId, settings)
window.electronAPI.checkProjectVersion(projectId)
window.electronAPI.initializeProject(projectId)

// Worktree operations
window.electronAPI.listWorktrees(projectId)
window.electronAPI.mergeWorktree(taskId)
window.electronAPI.discardWorktree(taskId)
window.electronAPI.getWorktreeStatus(taskId)
window.electronAPI.getWorktreeDiff(taskId)
window.electronAPI.mergeWorktreePreview(taskId)
window.electronAPI.worktreeOpenInIDE(path, ide, customPath)
window.electronAPI.worktreeOpenInTerminal(path, terminal, customPath)
```

#### TDD Plan:
1. **Test**: `apps/backend/api/tests/routes/test_tasks.py`
   ```python
   # Existing tests to extend:
   - test_create_task_with_metadata
   - test_start_task
   - test_submit_review
   - test_update_task_status
   - test_archive_tasks
   - test_list_worktrees
   - test_merge_worktree
   - test_discard_worktree
   ```

2. **Backend**: `apps/backend/api/routes/tasks.py`
   ```python
   # Add endpoints:
   POST /api/projects/{id}/tasks  # with metadata
   POST /api/tasks/{id}/start
   POST /api/tasks/{id}/review
   PATCH /api/tasks/{id}/status
   POST /api/tasks/{id}/archive
   GET /api/projects/{id}/worktrees
   POST /api/tasks/{id}/worktree/merge
   DELETE /api/tasks/{id}/worktree
   GET /api/tasks/{id}/worktree/status
   GET /api/tasks/{id}/worktree/diff
   ```

3. **Frontend**: Extend `lib/api/types.ts` and `lib/api/web-client.ts`
   ```typescript
   // Add to APIClient interface:
   createTaskWithMetadata(projectId, title, desc, metadata): Promise<Task>
   startTask(taskId, options): void
   submitReview(taskId, approved, feedback): Promise<void>
   // ... etc
   ```

4. **Component Update**: Replace direct calls with `getAPIClient()`

---

### Feature: Terminal Management
**Category:** Needs new backend endpoint  
**Priority:** Critical  
**Files Affected:**
- `components/Terminal.tsx` (4 usages)
- `components/terminal/useXterm.ts` (1 usage)
- `components/terminal/useTerminalEvents.ts` (4 usages)
- `components/terminal/usePtyProcess.ts` (2 usages)
- `components/terminal/useAutoNaming.ts` (1 usage)
- `components/TerminalGrid.tsx` (10 usages)
- `stores/terminal-store.ts` (2 usages)
- `lib/buffer-persistence.ts` (2 usages)

#### Current electronAPI calls:
```typescript
// PTY operations
window.electronAPI.createTerminal({ cwd, cols, rows, claudeProfile })
window.electronAPI.sendTerminalInput(id, data)
window.electronAPI.resizeTerminal(id, cols, rows)
window.electronAPI.destroyTerminal(id)
window.electronAPI.invokeClaudeInTerminal(id, cwd)
window.electronAPI.restoreTerminalSession(terminalId, cwd, claudeProfile)

// Event listeners
window.electronAPI.onTerminalOutput((id, data) => {})
window.electronAPI.onTerminalExit((id, exitCode) => {})
window.electronAPI.onTerminalTitleChange((id, title) => {})
window.electronAPI.onTerminalClaudeSession((id, sessionId) => {})

// Session management
window.electronAPI.getTerminalSessions(projectPath)
window.electronAPI.getTerminalSessionDates(projectPath)
window.electronAPI.getTerminalSessionsForDate(date, projectPath)
window.electronAPI.restoreTerminalSessionsFromDate(date, terminalIds, cwd)
window.electronAPI.checkTerminalPtyAlive(terminalId)
window.electronAPI.generateTerminalName(command, cwd)
window.electronAPI.saveTerminalBuffer(terminalId, buffer)
```

#### TDD Plan:
1. **Test**: `apps/backend/api/tests/websocket/test_terminal.py`
   ```python
   - test_terminal_create_connect
   - test_terminal_input_output
   - test_terminal_resize
   - test_terminal_disconnect
   - test_terminal_session_restore
   ```

2. **Backend**: Existing `apps/backend/api/websocket/terminal.py` + new routes
   ```python
   # WebSocket already exists: /ws/terminal/{session_id}
   # Add REST endpoints:
   POST /api/terminals  # create
   DELETE /api/terminals/{id}
   GET /api/terminals/sessions
   POST /api/terminals/{id}/invoke-claude
   ```

3. **Frontend**: `lib/api/terminal-client.ts` already exists, extend it

---

### Feature: Settings
**Category:** Already has backend endpoint  
**Priority:** Critical  
**Files Affected:**
- `stores/settings-store.ts` (3 usages)
- `hooks/useIpc.ts` (3 usages)
- `components/onboarding/*.tsx` (5 usages)

#### Current electronAPI calls:
```typescript
window.electronAPI.getSettings()
window.electronAPI.saveSettings(settings)
window.electronAPI.getAppVersion()
```

#### TDD Plan:
1. **Test**: `apps/backend/api/tests/routes/test_settings.py`
   ```python
   - test_get_settings
   - test_save_settings
   - test_get_version
   ```

2. **Backend**: `apps/backend/api/routes/settings.py`
   ```python
   GET /api/settings
   PUT /api/settings
   GET /api/version
   ```

3. **Frontend**: Already in `WebAPIClient`, just verify it works

---

## Phase 2: Important Features

### Feature: GitHub Integration
**Category:** Needs new backend endpoint (proxy to gh CLI or API)  
**Priority:** Important  
**Files Affected:**
- `stores/github/issues-store.ts` (2 usages)
- `stores/github/pr-review-store.ts` (4 usages)
- `stores/github/sync-status-store.ts` (1 usage)
- `stores/github/investigation-store.ts` (1 usage)
- `components/github-issues/hooks/*.ts` (25+ usages)
- `components/github-prs/hooks/*.ts` (20+ usages)
- `components/GitHubSetupModal.tsx` (15 usages)
- `components/settings/integrations/GitHubIntegration.tsx` (5 usages)

#### Current electronAPI calls (subset):
```typescript
// Issues
window.electronAPI.getGitHubIssues(projectId, state)
window.electronAPI.importGitHubIssues(projectId, issueNumbers)
window.electronAPI.investigateGitHubIssue(projectId, issueNumber, commentIds)
window.electronAPI.getIssueComments(projectId, issueNumber)

// PRs
window.electronAPI.github.listPRs(projectId)
window.electronAPI.github.runPRReview(projectId, prNumber)
window.electronAPI.github.postPRReview(projectId, prNumber, findingIds)
window.electronAPI.github.mergePR(projectId, prNumber, mergeMethod)
window.electronAPI.github.getPRLogs(projectId, prNumber)

// AutoFix (complex)
window.electronAPI.github.startAutoFix(projectId, issueNumber)
window.electronAPI.github.batchAutoFix(projectId, issueNumbers)
window.electronAPI.github.analyzeIssuesPreview(projectId, issueNumbers, max)

// OAuth
window.electronAPI.checkGitHubCli()
window.electronAPI.checkGitHubAuth()
window.electronAPI.startGitHubAuth()
window.electronAPI.getGitHubToken()
window.electronAPI.getGitHubUser()

// Event listeners (many)
window.electronAPI.github.onPRReviewProgress(callback)
window.electronAPI.github.onPRReviewComplete(callback)
window.electronAPI.github.onAutoFixProgress(callback)
// ... 10+ more
```

#### TDD Plan:
1. **Test**: `apps/backend/api/tests/routes/test_github.py`
   ```python
   - test_list_issues
   - test_import_issues
   - test_list_prs
   - test_run_pr_review
   - test_github_oauth_flow
   ```

2. **Backend**: `apps/backend/api/routes/github.py`
   ```python
   # GitHub proxy endpoints
   GET /api/projects/{id}/github/issues
   POST /api/projects/{id}/github/issues/import
   GET /api/projects/{id}/github/prs
   POST /api/projects/{id}/github/prs/{num}/review
   
   # OAuth (may need to proxy to backend token storage)
   POST /api/github/auth/start
   GET /api/github/auth/status
   
   # WebSocket for real-time events
   /ws/github/events
   ```

3. **Frontend**: Add `GitHubAPIClient` methods to `WebAPIClient`

---

### Feature: GitLab Integration
**Category:** Needs new backend endpoint  
**Priority:** Important  
**Files Affected:**
- `stores/gitlab-store.ts` (4 usages)
- `stores/gitlab/mr-review-store.ts` (6 usages)
- `components/gitlab-issues/*.tsx` (5+ usages)
- `components/gitlab-merge-requests/*.tsx` (30+ usages)
- `components/settings/integrations/GitLabIntegration.tsx` (15 usages)

#### Current electronAPI calls (similar structure to GitHub):
```typescript
window.electronAPI.getGitLabIssues(projectId, state)
window.electronAPI.checkGitLabConnection(projectId)
window.electronAPI.investigateGitLabIssue(projectId, issueIid, noteIds)
window.electronAPI.importGitLabIssues(projectId, issueIids)
window.electronAPI.getGitLabMergeRequests(projectId, state)
window.electronAPI.runGitLabMRReview(projectId, mrIid)
// ... 50+ more methods
```

#### TDD Plan:
Same pattern as GitHub - create backend proxy routes

---

### Feature: Insights (AI Chat)
**Category:** Needs new backend endpoint  
**Priority:** Important  
**Files Affected:**
- `stores/insights-store.ts` (15 usages)

#### Current electronAPI calls:
```typescript
window.electronAPI.listInsightsSessions(projectId)
window.electronAPI.getInsightsSession(projectId)
window.electronAPI.sendInsightsMessage(projectId, message, config)
window.electronAPI.clearInsightsSession(projectId)
window.electronAPI.newInsightsSession(projectId)
window.electronAPI.switchInsightsSession(projectId, sessionId)
window.electronAPI.deleteInsightsSession(projectId, sessionId)
window.electronAPI.renameInsightsSession(projectId, sessionId, newTitle)
window.electronAPI.updateInsightsModelConfig(projectId, sessionId, config)
window.electronAPI.createTaskFromInsights(projectId, title, description)

// Streaming events
window.electronAPI.onInsightsStreamChunk(callback)
window.electronAPI.onInsightsStatus(callback)
window.electronAPI.onInsightsError(callback)
```

#### TDD Plan:
1. **Backend**: `apps/backend/api/routes/insights.py`
   ```python
   GET /api/projects/{id}/insights/sessions
   POST /api/projects/{id}/insights/sessions
   DELETE /api/projects/{id}/insights/sessions/{sid}
   POST /api/projects/{id}/insights/message  # starts streaming
   
    # WebSocket for streaming
    /ws/insights/{project_id}
    ```

---

## Phase 3: Nice-to-Have Features

### Feature: Ideation
**Category:** Needs new backend endpoint  
**Priority:** Nice-to-have  
**Files Affected:** `stores/ideation-store.ts` (17 usages)

#### Current electronAPI calls:
```typescript
window.electronAPI.getIdeation(projectId)
window.electronAPI.generateIdeation(projectId, config)
window.electronAPI.stopIdeation(projectId)
window.electronAPI.refreshIdeation(projectId, config)
window.electronAPI.dismissAllIdeas(projectId)
window.electronAPI.archiveIdea(projectId, ideaId)
window.electronAPI.deleteIdea(projectId, ideaId)
window.electronAPI.deleteMultipleIdeas(projectId, ideaIds)
window.electronAPI.convertIdeaToTask(projectId, ideaId)
window.electronAPI.dismissIdea(projectId, ideaId)

// Events
window.electronAPI.onIdeationProgress(callback)
window.electronAPI.onIdeationLog(callback)
window.electronAPI.onIdeationTypeComplete(callback)
window.electronAPI.onIdeationTypeFailed(callback)
window.electronAPI.onIdeationComplete(callback)
window.electronAPI.onIdeationError(callback)
window.electronAPI.onIdeationStopped(callback)
```

---

### Feature: Roadmap
**Category:** Needs new backend endpoint  
**Priority:** Nice-to-have  
**Files Affected:**
- `stores/roadmap-store.ts` (7 usages)
- `hooks/useIpc.ts` (4 usages)
- `components/roadmap/hooks.ts` (3 usages)
- `components/AddFeatureDialog.tsx` (1 usage)

#### Current electronAPI calls:
```typescript
window.electronAPI.getRoadmapStatus(projectId)
window.electronAPI.getRoadmap(projectId)
window.electronAPI.saveRoadmap(projectId, roadmap)
window.electronAPI.generateRoadmap(projectId, enableCompetitor, refresh)
window.electronAPI.refreshRoadmap(projectId, enableCompetitor, refresh)
window.electronAPI.stopRoadmap(projectId)
window.electronAPI.convertFeatureToSpec(projectId, featureId)

// Events
window.electronAPI.onRoadmapProgress(callback)
window.electronAPI.onRoadmapComplete(callback)
window.electronAPI.onRoadmapError(callback)
window.electronAPI.onRoadmapStopped(callback)
```

---

### Feature: Changelog
**Category:** Needs new backend endpoint  
**Priority:** Nice-to-have  
**Files Affected:**
- `stores/changelog-store.ts` (12 usages)
- `components/changelog/*.tsx` (8 usages)

#### Current electronAPI calls:
```typescript
window.electronAPI.getChangelogDoneTasks(projectId, tasks)
window.electronAPI.readExistingChangelog(projectId)
window.electronAPI.loadTaskSpecs(projectId, taskIds)
window.electronAPI.getChangelogBranches(projectId)
window.electronAPI.getChangelogTags(projectId)
window.electronAPI.getChangelogCommitsPreview(projectId, options, mode)
window.electronAPI.generateChangelog({...})
window.electronAPI.saveChangelog({...})
window.electronAPI.suggestChangelogVersion(projectId, taskIds, existingVersion)
window.electronAPI.suggestChangelogVersionFromCommits(projectId, options)
window.electronAPI.saveChangelogImage(projectId, name, buffer)
window.electronAPI.readLocalImage(projectPath, relativePath)
window.electronAPI.createGitHubRelease(projectId, version, notes, options)

// Events
window.electronAPI.onChangelogGenerationProgress(callback)
window.electronAPI.onChangelogGenerationComplete(callback)
window.electronAPI.onChangelogGenerationError(callback)
```

---

## Phase 4: Defer (Electron-Only)

These features rely heavily on desktop-specific functionality and should be hidden/disabled in web mode rather than reimplemented.

### Feature: App Updates
**Category:** Electron-only  
**Priority:** Defer  
**Files Affected:**
- `components/AppUpdateNotification.tsx` (5 usages)
- `components/settings/AdvancedSettings.tsx` (10 usages)

#### Action:
```typescript
// Wrap in isWebMode() guard to hide
if (!isWebMode()) {
  // Show update UI
}
```

---

### Feature: Claude Code CLI Installation
**Category:** Electron-only  
**Priority:** Defer  
**Files Affected:**
- `components/ClaudeCodeStatusBadge.tsx` (4 usages)
- `components/onboarding/ClaudeCodeStep.tsx` (4 usages)

#### Action: Hide in web mode, show "Not available in web mode" message

---

### Feature: Ollama Local Installation
**Category:** Electron-only  
**Priority:** Defer  
**Files Affected:**
- `components/onboarding/OllamaModelSelector.tsx` (6 usages)
- `components/project-settings/MemoryBackendSection.tsx` (2 usages)

#### Action: In web mode, show remote Ollama configuration only (URL input)

---

### Feature: File/Directory Dialogs
**Category:** Electron-only (partial web support)  
**Priority:** Defer  
**Files Affected:**
- `components/AddProjectModal.tsx` (2 usages)
- `components/settings/DevToolsSettings.tsx` (2 usages)
- `App.tsx` (1 usage)

#### Current electronAPI calls:
```typescript
window.electronAPI.selectDirectory()
window.electronAPI.getDefaultProjectLocation()
window.electronAPI.createProjectFolder(location, name, initGit)
```

#### Action: 
- Web mode: Use `<input type="file" webkitdirectory>` for directory selection
- Show text input for manual path entry
- Document that project must exist on server filesystem

---

### Feature: Open External Links
**Category:** Electron-only  
**Priority:** Defer  
**Files Affected:**
- `components/onboarding/OllamaModelSelector.tsx` (1 usage)
- `components/ClaudeCodeStatusBadge.tsx` (1 usage)
- `components/settings/AdvancedSettings.tsx` (1 usage)
- `components/CustomMcpDialog.tsx` (1 usage)

#### Current electronAPI calls:
```typescript
window.electronAPI.openExternal(url)
window.electronAPI?.openExternal?.(url)
```

#### Action: Replace with `window.open(url, '_blank')` in web mode

---

### Feature: Debug Info & Logs
**Category:** Partial web support  
**Priority:** Defer  
**Files Affected:**
- `components/settings/DebugSettings.tsx` (3 usages)

#### Current electronAPI calls:
```typescript
window.electronAPI.getDebugInfo()
window.electronAPI.openLogsFolder()
window.electronAPI.copyDebugInfo()
```

#### Action: 
- `getDebugInfo()` - Can implement via backend API
- `openLogsFolder()` - Hide in web mode
- `copyDebugInfo()` - Use clipboard API

---

## Implementation Priority Matrix

### Sprint 1: Critical MVP

| # | Task | Backend | Frontend | Migrate |
|---|------|---------|----------|---------|
| 1.1 | Settings API | `GET/PUT /api/settings`, `GET /api/version` | Extend WebAPIClient | `settings-store.ts`, `useIpc.ts` |
| 1.2 | Project Environment | `GET/PUT /api/projects/{id}/env` | Extend WebAPIClient | `Sidebar.tsx`, `AgentTools.tsx`, `TaskCreationWizard.tsx` |
| 1.3 | Task Execution | `POST /api/tasks/{id}/start\|stop\|review`, `PUT status`, `WS /ws/tasks/{id}/events` | Extend WebAPIClient + WS subscriptions | `task-store.ts`, `useIpc.ts` |
| 1.4 | Terminal Enhancement | `POST/DELETE /api/terminals`, enhance existing WS | Verify `terminal-client.ts` | `Terminal.tsx`, `TerminalGrid.tsx`, `usePtyProcess.ts` |

### Sprint 2: Core Features

| # | Task | Backend | Frontend | Migrate |
|---|------|---------|----------|---------|
| 2.1 | Worktree Management | `GET /api/projects/{id}/worktrees`, `GET/POST /api/worktrees/{task_id}/*` | Extend WebAPIClient | `Worktrees.tsx`, `TaskDetailModal.tsx`, `useTaskDetail.ts` |
| 2.2 | Git Operations | `GET /api/projects/{id}/git/branches\|main-branch\|status`, `POST init` | Extend WebAPIClient | `AddProjectModal.tsx`, `Sidebar.tsx`, `TaskCreationWizard.tsx` |
| 2.3 | File System | `GET /api/fs/list`, `GET /api/fs/read` (sandboxed) | Extend WebAPIClient | `file-explorer-store.ts`, `TaskFiles.tsx` |
| 2.4 | Task Logs | `GET /api/tasks/{id}/logs`, `WS /ws/tasks/{id}/logs` | Extend WebAPIClient | `useTaskDetail.ts` |

### Sprint 3: Polish

| # | Task | Backend | Frontend | Migrate |
|---|------|---------|----------|---------|
| 3.1 | Claude Profile Management | CRUD `/api/claude/profiles`, `/api/claude/auto-switch` | Extend WebAPIClient | `OAuthStep.tsx`, `EnvConfigModal.tsx`, `IntegrationSettings.tsx` |
| 3.2 | Web Mode Guards | - | Add `isWebMode()` checks, replace `openExternal` | 10+ components |

### Sprint 4: Enhanced (Deferred)

| # | Task | Backend | Frontend |
|---|------|---------|----------|
| 4.1 | Insights Chat | `/api/projects/{id}/insights/*`, `WS /ws/insights/{id}` | Streaming UI |
| 4.2 | Ideation | `/api/projects/{id}/ideation/*`, `WS /ws/ideation/{id}` | Update store |
| 4.3 | Roadmap | `/api/projects/{id}/roadmap/*`, `WS /ws/roadmap/{id}` | Update store |
| 4.4 | Changelog | `/api/projects/{id}/changelog/*` | Update store |

### Sprint 5: Integrations (Deferred)

| # | Task | Backend | Frontend |
|---|------|---------|----------|
| 5.1 | GitHub Integration | Proxy endpoints for issues, PRs, OAuth, AutoFix | Update hooks |
| 5.2 | GitLab Integration | Proxy endpoints for issues, MRs, OAuth | Update hooks |
| 5.3 | Linear Integration | Proxy endpoints for teams, issues | Update hooks |

---

## Files Requiring Web Mode Guards

These files use `window.electronAPI` for features that cannot work in web mode and should show alternative UI:

| File | Guard Action |
|------|--------------|
| `OllamaModelSelector.tsx` | Show "Remote Ollama only" config |
| `ClaudeCodeStep.tsx` | Show "Not available in web mode" |
| `AppUpdateNotification.tsx` | Hide entirely |
| `AdvancedSettings.tsx` | Hide update section |
| `DebugSettings.tsx` | Hide "Open Logs Folder" |
| `AddProjectModal.tsx` | Use text input instead of dialog |
| `DevToolsSettings.tsx` | Use text input for paths |

---

## Test Commands

```bash
# Backend API tests
cd apps/backend && .venv/bin/pytest api/tests/ -v

# Frontend tests  
cd apps/frontend && npm test -- --run

# TypeScript check
cd apps/frontend && npm run typecheck

# Build web bundle
cd apps/frontend && npm run build:web
```

---

## Summary

**Total API Methods to Implement:** ~250+  
**Current Coverage:** ~45 methods  
**Gap:** ~205 methods  

**Sprint 1 Progress: 4/4 COMPLETE ✅**
- [x] 1.1 Settings API ✅
- [x] 1.2 Project Environment ✅
- [x] 1.3 Task Execution ✅
- [x] 1.4 Terminal Enhancement ✅

**Execution Order:**
1. Sprint 1: Critical MVP (Settings, Project Env, Task Execution, Terminal) ✅ COMPLETE
2. Sprint 2: Core Features (Worktrees, Git, Filesystem, Task Logs) ← NEXT
3. Sprint 3: Polish (Claude Profiles, Web Mode Guards)
4. Sprint 4: Enhanced - Deferred (Insights, Ideation, Roadmap, Changelog)
5. Sprint 5: Integrations - Deferred (GitHub, GitLab, Linear)

**Principles:**
- TDD: Write tests first, then implement
- Use `isWebMode()` guards to hide Electron-only features
- Use WebSocket for all streaming/event-based features
- Test each feature independently before moving to next

---

## Appendix A: Complete TDD Implementation Checklist

### Sprint 1: Critical MVP

#### 1.1 Settings API ✅ COMPLETED
```
[x] TEST: apps/backend/api/tests/routes/test_settings.py
    [x] test_get_settings_returns_defaults
    [x] test_get_settings_persists_changes
    [x] test_save_settings_partial_update
    [x] test_save_settings_invalid_theme_rejected
    [x] test_get_version_returns_string

[x] BACKEND: apps/backend/api/routes/settings.py
    [x] GET /api/settings → AppSettings
    [x] PUT /api/settings → void
    [x] GET /api/version → string

[x] FRONTEND: apps/frontend/src/renderer/lib/api/web-client.ts
    [x] Implement getSettings(): Promise<APIResult<AppSettings>>
    [x] Implement saveSettings(settings: Partial<AppSettings>): Promise<APIResult<void>>

[x] MIGRATE: Replace window.electronAPI calls
    [x] stores/settings-store.ts (already using getAPIClient for web mode)
    [x] hooks/useIpc.ts (lines 191, 199)
```

#### 1.2 Project Environment ✅ COMPLETED
```
[x] TEST: apps/backend/api/tests/routes/test_project_env.py
    [x] test_get_env_project_not_found_404
    [x] test_get_env_returns_defaults
    [x] test_update_env_project_not_found_404
    [x] test_update_env_partial_merge
    [x] test_update_env_persists_changes
    [x] test_update_env_creates_if_missing
    [x] test_update_env_with_mcp_servers

[x] BACKEND: apps/backend/api/routes/projects.py (extend)
    [x] GET /api/projects/{id}/env → ProjectEnvConfig
    [x] PUT /api/projects/{id}/env → ProjectEnvConfig

[x] FRONTEND: Extend WebAPIClient
    [x] getProjectEnv(projectId): Promise<APIResult<ProjectEnvConfig>>
    [x] updateProjectEnv(projectId, config): Promise<APIResult<ProjectEnvConfig>>

[x] MIGRATE: 
    [x] components/Sidebar.tsx
    [x] components/AgentTools.tsx
    [x] components/TaskCreationWizard.tsx
    [x] components/project-settings/hooks/useProjectSettings.ts
```

#### 1.3 Task Execution ✅ COMPLETED
```
[x] TEST: apps/backend/api/tests/routes/test_task_execution.py
    [x] test_start_task_not_found_404
    [x] test_start_task_creates_process
    [x] test_stop_task_kills_process
    [x] test_submit_review_approved
    [x] test_submit_review_rejected_with_feedback
    [x] test_update_status_valid_transition
    [x] test_update_status_invalid_transition_400
    [x] test_check_task_running_true
    [x] test_check_task_running_false
    [x] test_recover_stuck_task

[x] TEST: apps/backend/api/tests/websocket/test_task_events.py (renamed from test_task_progress.py)
    [x] test_websocket_connects
    [x] test_progress_events_streamed
    [x] test_status_change_events
    [x] test_error_events
    [x] test_multiple_clients_receive_events
    [x] test_log_events (added)
    [x] test_websocket_supports_multiple_clients (added)

[x] BACKEND: apps/backend/api/routes/task_execution.py
    [x] POST /api/tasks/{id}/start
    [x] POST /api/tasks/{id}/stop
    [x] POST /api/tasks/{id}/review
    [x] PUT /api/tasks/{id}/status
    [x] GET /api/tasks/{id}/running
    [x] POST /api/tasks/{id}/recover

[x] BACKEND: apps/backend/api/websocket/task_events.py
    [x] WS /ws/tasks/{task_id}/events
    [x] Event types: progress, status, error, log

[x] FRONTEND: Extend WebAPIClient
    [x] startTask(taskId, options?)
    [x] stopTask(taskId)
    [x] submitReview(taskId, approved, feedback?)
    [x] updateTaskStatus(taskId, status)
    [x] checkTaskRunning(taskId)
    [x] recoverStuckTask(taskId, options?)
    [x] subscribeToTaskEvents(taskId, callbacks): () => void (via onTaskProgress/onTaskError/onTaskStatusChange)

[x] MIGRATE:
    [x] stores/task-store.ts (startTask, submitReview, persistTaskStatus, checkTaskRunning, recoverStuckTask)
    [ ] hooks/useIpc.ts (lines 19, 25, 32, 38, 44) - deferred, store functions sufficient
```

#### 1.4 Terminal Enhancement ✅
```
[x] TEST: apps/backend/api/tests/routes/test_terminals.py
    [x] test_create_terminal_returns_session_id
    [x] test_destroy_terminal_cleans_up
    [x] test_list_sessions
    [x] test_check_alive_returns_status

[x] TEST: apps/backend/api/tests/websocket/test_terminal_pty.py
    [x] test_input_echoed_back (existing test_terminal_ws.py covers this)
    [x] test_command_execution (existing test_terminal_ws.py covers this)
    [x] test_resize_changes_dimensions (existing test_terminal_ws.py covers this)
    [x] test_disconnect_kills_pty (existing test_terminal_ws.py covers this)

[x] BACKEND: apps/backend/api/routes/terminals.py
    [x] POST /api/terminals → { session_id }
    [x] DELETE /api/terminals/{id}
    [x] GET /api/terminals/sessions
    [x] GET /api/terminals/{id}/alive

[x] BACKEND: Enhance apps/backend/api/websocket/terminal.py
    [x] Add resize message handling (already existed)
    [x] Add title change events
    [x] Add Claude session ID tracking

[x] FRONTEND: Verify lib/api/terminal-client.ts works
    [x] Test connection flow
    [x] Test input/output
    [x] Test resize

[x] MIGRATE:
    [ ] components/Terminal.tsx (lines 64, 122, 148) - deferred, higher-level component
    [ ] components/TerminalGrid.tsx (lines 78, 102, 115, 123, 146, 175, 212, 253) - deferred, higher-level component
    [x] components/terminal/usePtyProcess.ts (lines 40, 71)
    [ ] components/terminal/useXterm.ts (line 115) - deferred, uses hooks
    [x] components/terminal/useTerminalEvents.ts (lines 47, 59, 71, 83)
    [ ] stores/terminal-store.ts (lines 246, 276) - deferred, uses electronAPI for session persistence
```

### Sprint 2: Core Features

#### 2.1 Worktree Management
```
[x] TEST: apps/backend/api/tests/routes/test_worktrees.py
    [x] test_list_worktrees_empty
    [x] test_list_worktrees_with_tasks
    [x] test_get_status_returns_diff_info
    [x] test_get_diff_returns_file_changes
    [x] test_merge_preview_shows_conflicts
    [x] test_merge_applies_changes
    [x] test_merge_with_no_commit
    [x] test_discard_removes_worktree

[x] BACKEND: apps/backend/api/routes/worktrees.py
    [x] GET /api/projects/{id}/worktrees
    [x] GET /api/worktrees/{task_id}/status
    [x] GET /api/worktrees/{task_id}/diff
    [x] GET /api/worktrees/{task_id}/merge/preview
    [x] POST /api/worktrees/{task_id}/merge
    [x] POST /api/worktrees/{task_id}/discard

[x] FRONTEND: Extend WebAPIClient
    [x] listWorktrees(projectId)
    [x] getWorktreeStatus(taskId)
    [x] getWorktreeDiff(taskId)
    [x] mergeWorktreePreview(taskId)
    [x] mergeWorktree(taskId, options?)
    [x] discardWorktree(taskId)

[ ] MIGRATE:
    [ ] components/Worktrees.tsx (lines 75, 110, 145)
    [ ] components/task-detail/TaskDetailModal.tsx (lines 131, 154)
    [ ] components/task-detail/hooks/useTaskDetail.ts (lines 111, 112, 213)
    [ ] components/task-detail/task-review/WorkspaceMessages.tsx (line 107)
    [ ] components/task-detail/task-review/WorkspaceStatus.tsx (lines 104, 117)
```

#### 2.2 Git Operations
```
[x] TEST: apps/backend/api/tests/routes/test_git.py
    [x] test_get_branches_lists_all
    [x] test_detect_main_branch_main
    [x] test_detect_main_branch_master
    [x] test_check_status_clean
    [x] test_check_status_dirty
    [x] test_initialize_git_new_repo
    [x] test_initialize_git_already_initialized

[x] BACKEND: apps/backend/api/routes/git.py
    [x] GET /api/projects/{id}/git/branches
    [x] GET /api/projects/{id}/git/main-branch
    [x] GET /api/projects/{id}/git/status
    [x] POST /api/projects/{id}/git/init

[x] FRONTEND: Extend WebAPIClient
    [x] getGitBranches(projectId)
    [x] getGitMainBranch(projectId)
    [x] getGitStatus(projectId)
    [x] initGitRepo(projectId)

[ ] MIGRATE:
    [ ] components/TaskCreationWizard.tsx (lines 191, 212)
    [ ] components/Sidebar.tsx (lines 193, 249)
    [ ] components/AddProjectModal.tsx (lines 70, 132)
    [ ] components/GitSetupModal.tsx (line 49)
    [ ] components/project-settings/IntegrationSettings.tsx (lines 93, 98)
```

#### 2.3 File System
```
[ ] TEST: apps/backend/api/tests/routes/test_filesystem.py
    [ ] test_list_directory_returns_nodes
    [ ] test_list_directory_path_traversal_blocked
    [ ] test_read_file_returns_content
    [ ] test_read_file_outside_project_blocked
    [ ] test_binary_file_handled

[ ] BACKEND: apps/backend/api/routes/filesystem.py
    [ ] GET /api/fs/list?path=&project_id=
    [ ] GET /api/fs/read?path=&project_id=
    [ ] Security: Sandbox to project directory only

[ ] MIGRATE:
    [ ] stores/file-explorer-store.ts (line 95)
    [ ] components/task-detail/TaskFiles.tsx (lines 62, 95, 133)
```

#### 2.4 Task Logs
```
[ ] TEST: apps/backend/api/tests/routes/test_task_logs.py
    [ ] test_get_logs_returns_structured_data
    [ ] test_watch_logs_streams_updates
    [ ] test_logs_for_nonexistent_task

[ ] BACKEND: apps/backend/api/routes/task_logs.py
    [ ] GET /api/tasks/{id}/logs
    [ ] WS /ws/tasks/{id}/logs

[ ] MIGRATE:
    [ ] components/task-detail/hooks/useTaskDetail.ts (lines 138, 159, 162, 181)
```

### Sprint 3: Polish

#### 3.1 Claude Profile Management
```
[ ] TEST: apps/backend/api/tests/routes/test_claude_profiles.py
[ ] BACKEND: apps/backend/api/routes/claude.py
    [ ] GET /api/claude/profiles
    [ ] POST /api/claude/profiles
    [ ] PUT /api/claude/profiles/{id}
    [ ] DELETE /api/claude/profiles/{id}
    [ ] POST /api/claude/profiles/{id}/activate
    [ ] POST /api/claude/profiles/{id}/initialize
    [ ] GET /api/claude/auto-switch
    [ ] PUT /api/claude/auto-switch

[ ] MIGRATE: 15 files using Claude profile APIs
```

#### 3.2 Web Mode Guards
```
[ ] Create isWebMode() guards for:
    [ ] components/ClaudeCodeStatusBadge.tsx - Show "Not available" message
    [ ] components/onboarding/ClaudeCodeStep.tsx - Skip or show instructions
    [ ] components/onboarding/OllamaModelSelector.tsx - Remote config only
    [ ] components/AppUpdateNotification.tsx - Hide entirely
    [ ] components/settings/AdvancedSettings.tsx - Hide update section
    [ ] components/settings/DebugSettings.tsx - Hide "Open Logs"
    [ ] components/AddProjectModal.tsx - Text input instead of dialog
    [ ] components/settings/DevToolsSettings.tsx - Text input for paths
    [ ] components/task-detail/TaskFiles.tsx - worktreeOpenInIDE → show path
    [ ] components/task-detail/task-review/WorkspaceStatus.tsx - show path

[ ] Replace window.electronAPI.openExternal with window.open
    [ ] ClaudeCodeStatusBadge.tsx (line 296)
    [ ] onboarding/ClaudeCodeStep.tsx (line 285)
    [ ] onboarding/OllamaModelSelector.tsx (line 469)
    [ ] settings/AdvancedSettings.tsx (line 356)
    [ ] CustomMcpDialog.tsx (line 369)
```

---

## Appendix B: API Domain Breakdown

| Domain | Interface | Methods | Priority |
|--------|-----------|---------|----------|
| ProjectAPI | `createProjectAPI()` | 15 | Critical |
| TaskAPI | `createTaskAPI()` | 20 | Critical |
| TerminalAPI | `createTerminalAPI()` | 18 | Critical |
| SettingsAPI | `createSettingsAPI()` | 10 | Critical |
| FileAPI | `createFileAPI()` | 5 | Important |
| AgentAPI | `createAgentAPI()` | 25 | Important |
| IdeationAPI | `createIdeationAPI()` | 15 | Nice-to-have |
| InsightsAPI | `createInsightsAPI()` | 15 | Nice-to-have |
| AppUpdateAPI | `createAppUpdateAPI()` | 10 | Defer |
| GitHubAPI | `createGitHubAPI()` | 50+ | Defer |
| GitLabAPI | `createGitLabAPI()` | 45+ | Defer |
| DebugAPI | `createDebugAPI()` | 5 | Defer |
| ClaudeCodeAPI | `createClaudeCodeAPI()` | 3 | Defer |
| McpAPI | `createMcpAPI()` | 3 | Defer |

---

## Appendix C: Backend Route Structure

```
apps/backend/api/
├── main.py                          # FastAPI app entry
├── models/
│   ├── __init__.py
│   ├── project.py                   # Project, ProjectSettings, ProjectEnvConfig
│   ├── task.py                      # Task, TaskStatus, TaskMetadata
│   ├── settings.py                  # AppSettings
│   ├── worktree.py                  # WorktreeStatus, WorktreeDiff
│   └── terminal.py                  # TerminalSession
├── routes/
│   ├── __init__.py
│   ├── health.py                    # ✅ Exists
│   ├── projects.py                  # ✅ Exists - extend with /env
│   ├── tasks.py                     # ✅ Exists - extend with execution
│   ├── settings.py                  # 🆕 NEW
│   ├── terminals.py                 # 🆕 NEW
│   ├── worktrees.py                 # 🆕 NEW
│   ├── git.py                       # 🆕 NEW
│   ├── filesystem.py                # 🆕 NEW
│   ├── task_logs.py                 # 🆕 NEW
│   ├── claude.py                    # 🆕 NEW
│   ├── insights.py                  # 🆕 Phase 4
│   ├── ideation.py                  # 🆕 Phase 4
│   ├── roadmap.py                   # 🆕 Phase 4
│   ├── changelog.py                 # 🆕 Phase 4
│   ├── github.py                    # 🆕 Phase 5
│   └── gitlab.py                    # 🆕 Phase 5
├── services/
│   ├── project_service.py           # ✅ Exists
│   ├── task_service.py              # ✅ Exists
│   ├── terminal_service.py          # ✅ Exists
│   ├── settings_service.py          # 🆕 NEW
│   ├── worktree_service.py          # 🆕 NEW
│   └── git_service.py               # 🆕 NEW
├── websocket/
│   ├── terminal.py                  # ✅ Exists - enhance
│   ├── task_events.py               # 🆕 NEW
│   └── insights.py                  # 🆕 Phase 4
└── tests/
    ├── conftest.py
    ├── routes/
    │   ├── test_health.py           # ✅ Exists
    │   ├── test_projects.py         # ✅ Exists
    │   ├── test_tasks.py            # ✅ Exists
    │   ├── test_settings.py         # 🆕 NEW
    │   ├── test_project_env.py      # 🆕 NEW
    │   ├── test_task_execution.py   # 🆕 NEW
    │   ├── test_terminals.py        # 🆕 NEW
    │   ├── test_worktrees.py        # 🆕 NEW
    │   ├── test_git.py              # 🆕 NEW
    │   ├── test_filesystem.py       # 🆕 NEW
    │   └── test_task_logs.py        # 🆕 NEW
    └── websocket/
        ├── test_terminal_pty.py     # 🆕 NEW
        └── test_task_progress.py    # 🆕 NEW
```

---

## Appendix D: Frontend API Client Structure

```
apps/frontend/src/renderer/lib/api/
├── index.ts                         # Re-exports
├── client.ts                        # ✅ Factory with isWebMode()
├── types.ts                         # ✅ APIClient interface - EXTEND
├── electron-client.ts               # ✅ Electron implementation
├── web-client.ts                    # ✅ Web implementation - EXTEND
├── terminal-client.ts               # ✅ Terminal WebSocket
└── __tests__/
    ├── client-factory.test.ts       # 🆕 NEW
    ├── web-client.test.ts           # 🆕 NEW
    └── terminal-client.test.ts      # 🆕 NEW
```
