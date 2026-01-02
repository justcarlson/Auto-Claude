# SECURITY SYSTEM AGENTS.md

Dynamic context-aware command sandbox for autonomous agents.

## OVERVIEW

Three-layer defense: Base commands (always safe) → Stack commands (project-detected) → Custom commands (user scripts). Deep validation inspects arguments, not just command names.

## STRUCTURE

```
security/
├── hooks.py              # bash_security_hook - SDK enforcement entry point
├── validator_registry.py # Maps sensitive commands to validators
├── parser.py             # Shell command parsing (pipes, chains, subshells)
├── filesystem_validators.py  # rm, chmod, mv safety checks
├── database_validators.py    # SQL injection prevention
├── process_validators.py     # kill/pkill restrictions
├── git_validators.py         # Pre-commit secret scanning
└── scan_secrets.py           # Regex-based credential detection
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add command validator | `validator_registry.py` + new `*_validators.py` |
| Extend base allowlist | `../project/command_registry/base.py` |
| Add stack detection | `../context/project_analyzer.py` |
| Modify secret patterns | `scan_secrets.py` |

## SECURITY LAYERS

```
1. Base Commands (~126): ls, cat, grep, git, curl...
   → Always allowed for any project

2. Stack Commands (dynamic): npm, pytest, flask, docker...
   → Detected via package.json, requirements.txt, etc.
   → Cached in .auto-claude/project_index.json

3. Custom Commands: make build, npm run test...
   → Extracted from Makefile, package.json scripts
```

## DEEP VALIDATORS

| Command | Validation | Blocks |
|---------|------------|--------|
| `rm` | Path inspection | `/`, `..`, `~`, escaping project dir |
| `chmod` | Mode check | Anything except `+x`, `755`, `644` |
| `psql/mysql` | SQL parsing | `DROP`, `TRUNCATE`, `DELETE` without `WHERE` |
| `kill/pkill` | Process allowlist | Non-dev processes, `kill -1`, `kill 0` |
| `git commit` | Secret scan | API keys, tokens, private keys in staged files |

## CONVENTIONS

- All bash execution flows through `bash_security_hook`
- Validators return `(allowed: bool, reason: str)`
- Unknown/unparseable commands → blocked by default
- Security profile invalidated on project structure change

## ANTI-PATTERNS

- **Never** bypass `bash_security_hook` for shell execution
- **Never** add production database credentials to allowlist
- **Never** allow `rm -rf` without explicit path validation
- **Never** trust command strings from agent output directly
