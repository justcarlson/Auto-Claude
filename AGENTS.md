# AUTO-CLAUDE KNOWLEDGE BASE

**Generated:** 2026-01-02 | **Commit:** 614ae80 | **Branch:** develop

## OVERVIEW

Multi-agent autonomous coding framework. Python backend orchestrates Claude Agent SDK sessions; Electron frontend provides desktop UI. Agents plan, implement, and validate code in isolated git worktrees.

## STRUCTURE

```
Auto-Claude/
├── apps/
│   ├── backend/          # Python agents, specs, QA pipeline (see AGENTS.md)
│   │   ├── merge/        # AI-powered semantic merge (see AGENTS.md)
│   │   ├── runners/github/ # PR automation (see AGENTS.md)
│   │   └── security/     # Dynamic command sandbox (see AGENTS.md)
│   └── frontend/         # Electron desktop app (see AGENTS.md)
├── tests/                # Pytest suite with advanced isolation (see AGENTS.md)
├── scripts/              # Build utilities (bump-version, install-backend)
├── docker/               # Caddyfile + start.sh only (Dockerfile at root)
├── guides/               # CLI documentation
├── plans/                # Deployment/audit plans (DOKPLOY, WEBMODE)
├── shared_docs/          # Cross-cutting design docs
└── run.py/               # ANOMALY: Empty directory, ignore
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new agent | `apps/backend/agents/` | Extend coder.py, register in `AGENT_CONFIGS` |
| Modify agent prompts | `apps/backend/prompts/*.md` | Markdown files define agent behavior |
| Add CLI command | `apps/backend/cli/` | Subcommands in dedicated modules |
| Add spec phase | `apps/backend/spec/phases/` | Register in `pipeline/orchestrator.py` |
| Frontend component | `apps/frontend/src/renderer/components/` | Feature-based folders |
| IPC handler | `apps/frontend/src/main/ipc-handlers/` | Domain-split modules |
| Add preload API | `apps/frontend/src/preload/api/modules/` | Factory pattern |
| Security allowlist | `apps/backend/security/` | Dynamic per-project stack (see AGENTS.md) |
| Memory system | `apps/backend/integrations/graphiti/` | LadybugDB embedded graph |
| GitHub automation | `apps/backend/runners/github/` | PR review, issue triage (see AGENTS.md) |
| Merge conflicts | `apps/backend/merge/` | AI-powered semantic merge (see AGENTS.md) |

## ANTI-PATTERNS (THIS PROJECT)

| Pattern | Why Forbidden |
|---------|---------------|
| `anthropic.Anthropic()` | Use `create_client()` from `core.client` - enforces security hooks |
| Absolute paths | Always use `./` relative paths |
| `as any`, `@ts-ignore` | No type suppression |
| Hardcoded UI strings | Use i18n keys (`t('namespace:key')`) |
| Push from agent | Agents never push to remote |
| PRs to `main` | Contributions target `develop` branch |
| Deep imports | Use facade modules: `from agents import CoderAgent` |
| Direct `gh` subprocess | Use `GHClient` wrapper in runners |

## CONVENTIONS

| Area | Rule |
|------|------|
| Python imports | Facade modules via `__init__.py` exports |
| Ruff ignores | `E501` (formatter), `E402` (facade), `B008` |
| TypeScript paths | `@/*`, `@shared/*`, `@features/*`, `@components/*` |
| ESLint | `no-explicit-any: warn`, `react-in-jsx-scope: off` |
| Commit messages | Conventional: `type(scope): description` |
| Package manager | npm only (no pnpm/yarn) |
| IPC responses | `{ success: boolean; data?: T; error?: string }` |

## COMMANDS

```bash
# Setup
npm run install:all                    # Install backend + frontend deps
cd apps/backend && uv venv && uv pip install -r requirements.txt

# Development
npm run dev                            # Electron with hot reload + E2E debug
cd apps/backend && python run.py --spec 001  # Run autonomous build

# Testing
apps/backend/.venv/bin/pytest tests/ -v      # Backend tests
npm test                                      # Frontend tests

# Release
node scripts/bump-version.js patch    # Bump → push → PR to main
```

## CRITICAL CONSTRAINTS

1. **Claude SDK Only**: All AI via `create_client()`, never raw Anthropic API
2. **Worktree Isolation**: Agent work in `.worktrees/{spec}/`, never main branch
3. **Three-Layer Security**: OS sandbox → filesystem perms → command allowlist (see `security/AGENTS.md`)
4. **OAuth Authentication**: Uses Claude Code OAuth, ignores `ANTHROPIC_API_KEY`
5. **i18n Required**: All frontend text via `react-i18next` translation keys
6. **Phase Protocol**: Backend→Frontend sync via `__EXEC_PHASE__:` stdout markers

## HIERARCHY

```
./AGENTS.md (this file)
├── apps/backend/AGENTS.md
│   ├── apps/backend/merge/AGENTS.md
│   ├── apps/backend/runners/github/AGENTS.md
│   └── apps/backend/security/AGENTS.md
├── apps/frontend/AGENTS.md
└── tests/AGENTS.md
```

## NOTES

- `CLAUDE.md` has comprehensive docs (500 lines) - this file adds hierarchy
- Root `run.py/` directory is an anomaly - actual entry is `apps/backend/run.py`
- CI auto-scans releases with VirusTotal before publishing
- Electron MCP enables QA agents to E2E test the running app
- Pre-commit hook syncs versions across package.json, __init__.py, README
