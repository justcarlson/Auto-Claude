# BACKEND AGENTS.md

Python multi-agent orchestration system using Claude Agent SDK.

## STRUCTURE

```
backend/
├── agents/           # Build agents (coder, planner, qa_*)
├── spec/             # Spec creation pipeline (phases/, pipeline/)
├── core/             # SDK client, security, auth, workspace
├── prompts/          # Agent behavior as Markdown files
├── merge/            # AI-powered conflict resolution (see AGENTS.md)
├── runners/github/   # PR automation (see AGENTS.md)
├── integrations/     # Graphiti memory, Linear sync
├── security/         # Dynamic command allowlisting
├── context/          # Project stack detection
├── cli/              # CLI command modules
├── analysis/         # Code analyzers (port, framework, CI detection)
└── *.py (root)       # Facade modules for flat imports
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Modify agent behavior | `prompts/*.md` (not Python code) |
| Add new build agent | `agents/` + register in `core/client.py` |
| Add spec phase | `spec/phases/` + register in `spec/pipeline/orchestrator.py` |
| Extend security allowlist | `security/` + `context/project_analyzer.py` |
| Add MCP server | `core/client.py` (dynamic based on project caps) |

## CONVENTIONS

| Pattern | Implementation |
|---------|----------------|
| Facade imports | `from agents import CoderAgent` via `__init__.py` exports |
| SDK client | Always `create_client()`, never `Anthropic()` |
| Agent types | `planner`, `coder`, `qa_reviewer`, `qa_fixer` |
| Spec storage | `.auto-claude/specs/XXX-name/` (spec.md, plan.json, etc.) |

## AGENT PIPELINE

```
Spec Creation (spec_runner.py):
  SIMPLE:   Discovery → Quick Spec → Validate
  STANDARD: Discovery → Requirements → Context → Spec → Plan → Validate
  COMPLEX:  + Research + Self-Critique phases

Implementation (run.py):
  1. Planner creates subtask-based plan
  2. Coder implements subtasks (can spawn subagents)
  3. QA Reviewer validates acceptance criteria
  4. QA Fixer resolves issues in loop
```

## ANTI-PATTERNS

- **Never** use `anthropic.Anthropic()` directly
- **Never** commit spec files to git from agent
- **Never** push to remote from agent session
- **Never** delete existing plan phases (append only)
- **Never** use absolute paths (always `./`)

## NOTES

- Facade modules at root (`debug.py`, `security.py`) shim `core/` utilities
- Recovery after 3 failures marks subtask `STUCK` for human intervention
- Post-session processing (`session.py`) ensures filesystem consistency
- Graphiti memory persists insights across sessions via LadybugDB
