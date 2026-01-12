# Test Markers for CI Pipeline

Jean Claude uses pytest markers to categorize tests for efficient CI execution.

## Available Markers

### `@pytest.mark.fast` (Default)
- **Purpose**: Unit tests that complete in < 1 second
- **What to test**: Pure functions, data models, simple logic
- **CI Usage**: Runs on every push/PR in parallel with lint and type-check
- **Example**:
```python
import pytest

@pytest.mark.fast
def test_workflow_state_initialization():
    """Fast unit test for WorkflowState model"""
    state = WorkflowState(workflow_id="test-123")
    assert state.workflow_id == "test-123"
```

### `@pytest.mark.slow`
- **Purpose**: Tests that take > 1 second
- **What to test**: Complex computations, heavy data processing
- **CI Usage**: Not run by default (manual trigger)
- **Example**:
```python
@pytest.mark.slow
def test_large_workflow_processing():
    """Process 1000 features - takes ~5s"""
    features = [Feature(name=f"feat-{i}") for i in range(1000)]
    # ... test logic
```

### `@pytest.mark.integration`
- **Purpose**: Tests requiring external dependencies
- **What to test**: Database operations, SDK integration, file system
- **CI Usage**: Runs conditionally when `src/jean_claude/core/**` or `src/jean_claude/orchestration/**` changes
- **Example**:
```python
@pytest.mark.integration
def test_event_logger_persistence():
    """Integration test for SQLite event store"""
    logger = EventLogger(project_root)
    logger.log_event("test_event", {"key": "value"})
    # Verify database state
```

### `@pytest.mark.e2e`
- **Purpose**: End-to-end system tests
- **What to test**: Full workflows, dashboard UI, CLI commands
- **CI Usage**: Manual trigger only
- **Example**:
```python
@pytest.mark.e2e
def test_full_workflow_execution():
    """E2E test: jc workflow 'Add auth' -> completion"""
    # Test entire workflow from CLI to completion
```

## Running Tests Locally

```bash
# Run only fast tests (default)
uv run pytest -m fast

# Run integration tests
uv run pytest -m integration

# Run all tests except e2e
uv run pytest -m "not e2e"

# Run slow and integration tests
uv run pytest -m "slow or integration"

# Run everything
uv run pytest
```

## CI Pipeline Behavior

### `ci.yml` - Main CI (Runs on all pushes/PRs)
- **test**: Fast tests only (`-m fast`)
- **lint**: Ruff check + format verification
- **type-check**: mypy type checking (non-blocking)
- **Timeout**: 10 minutes (test), 5 minutes (lint/type-check)
- **Parallelization**: All 3 jobs run in parallel

### `integration.yml` - Conditional Integration Tests
- **Trigger**: Only when core/ or orchestration/ code changes
- **Runs**: Integration tests (`-m integration`)
- **Timeout**: 15 minutes
- **Parallelization**: Runs alongside ci.yml jobs

## Marking Your Tests

**Default behavior**: Unmarked tests are treated as fast tests.

**Best practices**:
1. **Always mark slow tests** - Prevents CI slowdown
2. **Mark integration tests explicitly** - Isolates external dependencies
3. **Use e2e sparingly** - Reserve for critical user flows
4. **Combine markers when appropriate**:
```python
@pytest.mark.slow
@pytest.mark.integration
def test_full_database_migration():
    """Slow integration test"""
    # ...
```

## Concurrency Control

- **Concurrency cancellation**: New pushes cancel outdated workflow runs
- **Group**: `${{ github.workflow }}-${{ github.ref }}`
- **Benefit**: Saves CI minutes and provides faster feedback

## Coverage Reporting

Both workflows upload coverage to Codecov:
- **Token**: Stored in `CODECOV_TOKEN` secret
- **Fail behavior**: `fail_ci_if_error: false` (non-blocking)
- **Reports**: Visible on PR comments via Codecov integration

## Timeouts

| Job | Timeout | Rationale |
|-----|---------|-----------|
| test | 10 min | Fast tests should complete quickly |
| lint | 5 min | Linting is fast |
| type-check | 5 min | Type checking is fast |
| integration | 15 min | Integration tests may be slower |

## Future Enhancements

From `knowledge/doc/plans/gastown-patterns-roadmap.md`:
- **Security linting** (Bandit) - Pattern 5.3
- **E2E dashboard tests** (Playwright) - Pattern 5.5
- **Build validation** - Pattern 5.8

## Troubleshooting

### Tests fail with "no tests ran matching filter"
- Make sure you've marked tests with `@pytest.mark.fast`
- Or run without marker filter: `uv run pytest`

### CI timeout
- Check if tests are properly marked (slow tests in fast job)
- Review test execution time: `uv run pytest --durations=10`

### Type-check failures don't fail CI
- This is intentional during migration period
- Remove `continue-on-error: true` in `.github/workflows/ci.yml` when ready

## References

- **Gastown Pattern 5.1**: GitHub Actions CI
- **Gastown Pattern 5.2**: Test Categorization
- **CLAUDE.md**: Testing Philosophy section
- **pytest markers docs**: https://docs.pytest.org/en/stable/how-to/mark.html
