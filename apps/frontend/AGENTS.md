# FRONTEND AGENTS.md

Electron + React + TypeScript desktop application.

## STRUCTURE

```
frontend/src/
├── main/              # Electron main process
│   ├── ipc-handlers/  # Domain-split IPC (task/, github/, gitlab/)
│   ├── agent/         # Python process spawning + progress parsing
│   ├── terminal/      # PTY management (node-pty + xterm.js)
│   └── index.ts       # Entry point
├── preload/           # contextBridge API exposure
├── renderer/          # React application
│   ├── components/    # Feature-based (kanban/, terminal/, settings/)
│   ├── stores/        # Zustand global state
│   └── main.tsx       # React entry
└── shared/            # Types, constants, i18n (cross-process)
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add IPC handler | `src/main/ipc-handlers/{domain}/` |
| Add UI component | `src/renderer/components/{feature}/` |
| Add global state | `src/renderer/stores/` (Zustand) |
| Add translation | `src/shared/i18n/locales/{en,fr}/*.json` |
| Modify preload API | `src/preload/api/modules/` |

## CONVENTIONS

| Area | Rule |
|------|------|
| i18n | **MANDATORY**: `t('namespace:key')`, never hardcoded strings |
| Path aliases | `@/*` (renderer), `@shared/*`, `@components/*`, `@hooks/*` |
| Components | PascalCase files, feature-based folders |
| Stores | kebab-case: `task-store.ts` |
| IPC | `ipcMain.handle` for async, `ipcMain.on` for events |

## STATE MANAGEMENT

- **Zustand**: Global app state (tasks, projects, settings)
- **React Context**: UI-specific view state (non-persistent)

## AGENT COORDINATION

The frontend spawns Python agents and parses their stdout for progress:
```
AgentProcessManager → spawns python run.py
  ↓ parses __EXEC_PHASE__ markers
  ↓ emits TASK_PROGRESS events
  ↓ Renderer displays real-time status
```

## ANTI-PATTERNS

- **Never** hardcode UI text (use i18n)
- **Never** put business logic in components (extract to hooks/stores)
- **Never** use deep imports (use path aliases)

## COMPLEXITY HOTSPOTS

| File | Lines | Issue |
|------|-------|-------|
| `ipc-handlers/task/worktree-handlers.ts` | 2,276 | Hardcoded IDE/terminal paths |
| `components/AgentTools.tsx` | 1,408 | Config objects mixed with UI |
| `components/TaskCreationWizard.tsx` | 1,166 | Complex multi-step form |

## NOTES

- E2E testing via Electron MCP (QA agents interact with running app)
- HMR ignores `.worktrees/`, `.auto-claude/`, `.git/`
- Python env auto-detected/created by `python-env-manager.ts`
