# GITHUB RUNNER AGENTS

**Path:** `apps/backend/runners/github/`

## OVERVIEW
High-performance automation for GitHub Pull Requests and Issues. Orchestrates parallel AI reviewers, automated triage, and issue-to-spec "Auto-Fix" pipelines.

## STRUCTURE
- `orchestrator.py`: Main coordinator delegating to specialized services.
- `gh_client.py`: Robust async `gh` CLI wrapper with retries and rate limiting.
- `bot_detection.py`: Prevents infinite AI-to-AI interaction loops.
- `services/`: Specialized logic engines for core workflows:
  - `pr_review_engine.py`: Multi-pass/parallel PR review pipeline.
  - `triage_engine.py`: AI-powered classification and duplicate detection.
  - `autofix_processor.py`: Lifecycle from issue label to implementation spec.
  - `batch_processor.py`: Clusters similar issues into unified specs.

## PIPELINE: MULTI-PASS REVIEW
1. **Context Gathering**: Collects PR metadata, diffs, and repository context.
2. **Specialist Analysis**: Spawns parallel subagents via Claude Agent SDK.
   - *Specialists*: `security-reviewer`, `quality-reviewer`, `logic-reviewer`, etc.
3. **Synthesis**: Deduplicates findings and generates a `MergeVerdict`.
4. **Verification**: Explicitly blocks on critical findings or failing CI checks.

## WHERE TO LOOK
- **Modify Review Logic**: `services/parallel_orchestrator_reviewer.py`
- **Adjust Issue Triage**: `services/triage_engine.py`
- **CLI Commands**: `runner.py` (CLI entry point for automation tasks)
- **Rate Limits/Retries**: `gh_client.py` and `rate_limiter.py`

## CONVENTIONS
- **GHClient Patterns**: Always use `GHClient` for `gh` commands; handles `-R` flag and timeouts.
- **Service Layer**: Engines are thin and stateless; report progress via `ProgressCallback`.
- **Isolation**: All PR analysis MUST happen in detached worktrees (`.auto-claude/pr-review-worktrees/`).
- **Subagents**: Specialized reviewers use read-only tools and inherit the parent agent's model.

## ANTI-PATTERNS
- **Direct CLI Calls**: Never use `subprocess` for `gh` directly; use `GHClient`.
- **Infinite Loops**: Always check `BotDetector` before responding to AI comments.
- **Ambiguous Context**: Never omit the repository `-R` flag in worktree operations.
