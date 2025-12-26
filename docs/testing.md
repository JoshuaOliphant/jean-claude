# ABOUTME: Testing patterns and infrastructure for Jean Claude
# ABOUTME: Documents pytest configuration, fixtures, and TDD practices

# Testing Guide

## Quick Start

```bash
# Run all tests (parallel by default with -n 4)
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_work_command.py -v

# Run without parallel (for debugging)
uv run pytest tests/ -n 0

# Run with coverage
uv run pytest tests/ --cov=jean_claude
```

## Test Infrastructure

Tests use pytest with parallel execution (`pytest-xdist`) configured in `pyproject.toml:79-83`.

## Fixture-Based Testing (Required)

All new tests MUST use fixtures from `tests/conftest.py` instead of nested `with patch()` blocks.

### Good Pattern

```python
def test_work_emits_event(cli_runner, tmp_path, work_command_mocks):
    work_command_mocks["fetch_beads_task"].return_value = mock_task
    with cli_runner.isolated_filesystem(temp_dir=tmp_path):
        result = cli_runner.invoke(work, ["task.1"])
    work_command_mocks["event_logger"]["instance"].emit.assert_called()
```

### Anti-Pattern (Don't Do This)

```python
def test_work_emits_event(self):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch('...fetch_beads_task'):
            with patch('...generate_spec'):
                with patch('...update_status'):
                    # 6 levels of nesting - hard to read/maintain
                    result = runner.invoke(...)
```

## Available Fixtures

| Fixture | Purpose | Location |
|---------|---------|----------|
| `cli_runner` | Reusable CliRunner instance | `conftest.py:15` |
| `mock_beads_task` | Standard BeadsTask for testing | `conftest.py:25` |
| `mock_beads_task_factory` | Factory for custom BeadsTask | `conftest.py:35` |
| `work_command_mocks` | All mocks for work command tests | `conftest.py:50` |
| `mock_event_logger` | EventLogger class and instance mocks | `conftest.py:70` |
| `completed_workflow_state` | Mock state that reports complete | `conftest.py:85` |
| `failed_workflow_state` | Mock state that reports failed | `conftest.py:95` |

## Async Testing

For async functions, use `AsyncMock` instead of `Mock`:

```python
from unittest.mock import AsyncMock

# Correct - AsyncMock for async functions
mock_run = AsyncMock(return_value=result)

# Wrong - causes RuntimeWarning about unawaited coroutine
mock_run = Mock(return_value=result)
```

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures (import from here)
├── test_*.py             # Top-level test files
├── core/                 # Core module tests
│   ├── __init__.py
│   └── test_*.py
├── orchestration/        # Orchestration tests
│   └── test_*.py
└── templates/            # Template tests
    └── test_*.py
```

## TDD Workflow

1. Write a failing test that defines desired behavior
2. Run the test to confirm it fails as expected
3. Write minimal code to make the test pass
4. Run the test to confirm success
5. Refactor while keeping tests green
6. Repeat for each new feature

## Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple similar cases:

```python
@pytest.mark.parametrize("status,expected", [
    ("open", True),
    ("in_progress", True),
    ("closed", False),
])
def test_task_is_active(status, expected):
    task = BeadsTask(status=status)
    assert task.is_active == expected
```
