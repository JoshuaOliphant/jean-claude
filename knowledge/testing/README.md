# Testing Strategies

Testing approaches and strategies that work well for Jean Claude.

## Jean Claude Testing Philosophy

**Test OUR code, not external dependencies.**

### What to Mock
✅ External tools (Beads CLI, Claude SDK)
✅ Subprocess calls
✅ File system operations (when appropriate)
✅ Network requests

### What NOT to Mock
❌ Pydantic validation
❌ Click command parsing
❌ Our business logic
❌ Framework behavior

## Fixture Organization

Jean Claude uses a hierarchical fixture structure:

```
tests/
├── conftest.py                    # Root fixtures
├── core/
│   └── conftest.py               # Core module fixtures
├── orchestration/
│   └── conftest.py               # Workflow fixtures
└── templates/
    └── conftest.py               # Template fixtures
```

**Search before creating** - Check existing fixtures first:
```bash
grep -r "def.*fixture" tests/conftest.py tests/core/conftest.py
```

## Key Testing Patterns

### 1. Mock Patching Location

**Always patch where used, not where defined:**

```python
# ✅ CORRECT
@patch('jean_claude.core.edit_and_revalidate.fetch_beads_task')
def test_something(mock_fetch):
    pass

# ❌ WRONG
@patch('jean_claude.core.beads.fetch_beads_task')
def test_something(mock_fetch):
    pass
```

### 2. AsyncMock for Async Functions

```python
# ✅ CORRECT
@patch('module.async_function', new_callable=AsyncMock)
def test_async(mock_async):
    pass

# ❌ WRONG
@patch('module.async_function')
def test_async(mock_async):
    pass
```

### 3. Decorator Order (Bottom-Up)

```python
@patch('module.function_c')
@patch('module.function_b')
@patch('module.function_a')
def test_thing(mock_a, mock_b, mock_c):
    # Parameters are in reverse order of decorators
    pass
```

### 4. Comprehensive Tests Over Many Small Tests

```python
# ✅ GOOD
@pytest.mark.parametrize("priority", [LOW, NORMAL, URGENT])
def test_all_priorities(priority):
    pass

# ❌ BAD
def test_low_priority(): pass
def test_normal_priority(): pass
def test_urgent_priority(): pass
```

## Test Categories

### Unit Tests
- Test individual functions and classes
- Mock all external dependencies
- Fast execution

### Integration Tests
- Test component interactions
- Mock external services only
- Test real business logic

### End-to-End Tests
- Test complete workflows
- Minimal mocking
- Verify real behavior

## Continuous Improvement

When you discover a testing approach that works well:
1. Document it here
2. Create example test
3. Add to fixture library if reusable
4. Update CLAUDE.md if it's a critical pattern
