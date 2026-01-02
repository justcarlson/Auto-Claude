# AUTO-CLAUDE TEST SUITE

## OVERVIEW
Advanced isolation test suite powered by pytest, designed for autonomous agent validation without external dependencies.

## STRUCTURE

| File | Purpose |
|------|---------|
| `conftest.py` | Global configuration, pre-emptive SDK mocking, and module cleanup. |
| `test_fixtures.py` | Shared code snippets (React/Python) and sample data constants. |
| `review_fixtures.py` | Spec directory generation and `ReviewState` factory fixtures. |
| `qa_report_helpers.py` | specialized mocks for testing the QA reporting pipeline. |

## WHERE TO LOOK

- **Adding Tests**: Place in `tests/` with `test_*.py` prefix.
- **Project Contexts**: Use `python_project`, `node_project`, or `docker_project` fixtures.
- **Git Operations**: Use `temp_git_repo` for isolated workspace testing.
- **Async Logic**: Mark with `@pytest.mark.asyncio`.

## CONVENTIONS

### Mock Patterns
- **SDK Mocking**: External SDKs (`claude_agent_sdk`, `claude_code_sdk`) are automatically mocked in `conftest.py` before any imports occur.
- **Agent Simulation**: Use `mock_run_agent_fn` to simulate agent execution without hitting the LLM.

### Fixture Usage
- **Factory Fixtures**: Use `make_commit` and `stage_files` for rapid git state manipulation.
- **Mock Cleanup**: Modules are purged from `sys.modules` between tests to prevent mock leakage.

## UNIQUE PATTERNS

- **Pre-emptive Mocking**: SDK mocks are injected into `sys.modules` at startup to allow importing backend modules that depend on missing SDKs.
- **Dynamic Isolation**: `conftest.py` explicitly purges and restores original modules between test runs.
- **Worktree Simulation**: Tests often leverage `temp_git_repo` to simulate the framework's core worktree isolation behavior.
- **Async Testing**: Uses `httpx.ASGITransport` for testing API endpoints asynchronously.
