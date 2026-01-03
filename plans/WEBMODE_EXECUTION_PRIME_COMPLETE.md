# Web Mode API Parity - Execution Prime

Copy everything below the line to start execution.

---

ultrawork

## Mission

Execute the Web Mode API Parity plan at `/plans/WEBMODE_AUDIT_RESULTS.md` on branch `feat/webmode-api-parity`.

## Context

Auto-Claude frontend has 482 `window.electronAPI` usages across 102 files. Only ~3% have web mode support. This work implements the remaining backend endpoints and migrates frontend code to use the unified API client.

## Execution Rules

1. **Continuous**: Work autonomously until human input is genuinely required
2. **TDD**: Write failing tests → implement → verify green → migrate
3. **Sequential**: Complete tasks in order (1.1 → 1.2 → 1.3 → etc.)
4. **Atomic commits**: One commit per completed task
5. **Update progress**: Mark checkboxes in plan as tasks complete

## Current Queue

Read `/plans/WEBMODE_AUDIT_RESULTS.md` for full details. Execute in order:

```
Sprint 1: Critical MVP
├── 1.1 Settings API
├── 1.2 Project Environment  
├── 1.3 Task Execution + WebSocket
└── 1.4 Terminal Enhancement

Sprint 2: Core Features
├── 2.1 Worktree Management
├── 2.2 Git Operations
├── 2.3 File System
└── 2.4 Task Logs

Sprint 3: Polish
├── 3.1 Claude Profile Management
└── 3.2 Web Mode Guards
```

## Per-Task Workflow

For each task (e.g., 1.1 Settings API):

1. **Read plan** - Get task details from Appendix A in `/plans/WEBMODE_AUDIT_RESULTS.md`
2. **Write tests** - Create test file with all specified test cases
3. **Run tests** - Verify RED (tests fail)
4. **Implement backend** - Create/extend routes and services
5. **Run tests** - Verify GREEN
6. **Extend frontend** - Add methods to WebAPIClient
7. **Migrate** - Replace `window.electronAPI` calls in specified files
8. **Verify** - Run typecheck, ensure no regressions
9. **Commit** - `feat(api): implement {task name} for web mode`
10. **Update plan** - Mark checkbox complete in `/plans/WEBMODE_AUDIT_RESULTS.md`
11. **Next task** - Continue to next item

## File Locations

| Component | Path |
|-----------|------|
| Plan | `/plans/WEBMODE_AUDIT_RESULTS.md` |
| Backend routes | `apps/backend/api/routes/` |
| Backend tests | `apps/backend/api/tests/routes/` |
| Backend services | `apps/backend/api/services/` |
| Frontend API client | `apps/frontend/src/renderer/lib/api/` |
| Frontend stores | `apps/frontend/src/renderer/stores/` |

## Commands

```bash
# Backend tests
cd apps/backend && .venv/bin/pytest api/tests/ -v

# Frontend typecheck
cd apps/frontend && npm run typecheck

# Specific test file
cd apps/backend && .venv/bin/pytest api/tests/routes/test_settings.py -v
```

## Stop Conditions

Stop and ask human ONLY if:
- Architectural decision with multiple valid approaches
- Existing code conflicts with plan (needs clarification)
- Test infrastructure missing or broken
- External dependency issue

Do NOT stop for:
- Implementation details (make reasonable choices)
- Minor deviations from plan (document and proceed)
- Warnings that don't block functionality

## Start

1. Verify on branch `feat/webmode-api-parity`
2. Read `/plans/WEBMODE_AUDIT_RESULTS.md`
3. Find first unchecked task
4. Begin execution

Go.
