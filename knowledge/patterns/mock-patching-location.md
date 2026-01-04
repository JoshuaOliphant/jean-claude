# Mock Patching Location Pattern

## Problem

When using `@patch` in pytest, patches must target the namespace where the object is *used*, not where it's *defined*. Patching in the wrong location leads to tests that don't actually mock the intended code.

## Solution

**Always patch where the object is USED (imported), not where it's DEFINED.**

## Example

Given this code structure:

```python
# jean_claude/core/beads.py
def fetch_beads_task(task_id: str) -> BeadsTask:
    """Fetch task from Beads CLI."""
    # Implementation...
```

```python
# jean_claude/core/edit_and_revalidate.py
from jean_claude.core.beads import fetch_beads_task

def process_task(task_id: str):
    task = fetch_beads_task(task_id)  # Used here
    # Process task...
```

### ✅ CORRECT - Patch where used

```python
# tests/core/test_edit_and_revalidate.py
from unittest.mock import patch

@patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')
def test_process_task(mock_fetch):
    """Mock works because we patched where fetch_beads_task is USED."""
    mock_fetch.return_value = BeadsTask(...)

    result = process_task('beads-123')

    assert mock_fetch.called
    # Test passes - mock was actually used
```

### ❌ WRONG - Patch where defined

```python
# tests/core/test_edit_and_revalidate.py
from unittest.mock import patch

@patch('jean_claude.core.beads.fetch_beads_task')
def test_process_task(mock_fetch):
    """Mock DOESN'T WORK - we patched the source module, not the import."""
    mock_fetch.return_value = BeadsTask(...)

    result = process_task('beads-123')

    # Test fails - edit_and_revalidate.py has its own reference to the function
    # that wasn't patched
```

## When to Use

Use this pattern whenever you need to mock functions, classes, or objects that are imported by the code under test.

## Gotchas

### Import Style Matters

```python
# If the import is:
from jean_claude.core.beads import fetch_beads_task

# Then patch:
@patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')

# NOT:
@patch('jean_claude.core.beads.fetch_beads_task')
```

```python
# If the import is:
import jean_claude.core.beads

# Then the code calls:
beads.fetch_beads_task()

# So patch:
@patch('jean_claude.core.beads.fetch_beads_task')
```

### Multiple Patch Decorators

When stacking multiple patches, remember they're applied **bottom-up** but parameters are **top-down**:

```python
@patch('module.function_c')  # Third patch, third parameter
@patch('module.function_b')  # Second patch, second parameter
@patch('module.function_a')  # First patch, first parameter
def test_thing(mock_a, mock_b, mock_c):
    # Parameters match decorator order (top to bottom)
    pass
```

## Related Patterns

- [AsyncMock for Async Functions](asyncmock-pattern.md)
- [Subprocess Mocking](subprocess-mocking.md)
- [Fixture Organization](fixture-organization.md)

## References

- Python unittest.mock documentation
- Jean Claude testing philosophy (CLAUDE.md)
- Mock Patching Rule (CLAUDE.md:131-148)
