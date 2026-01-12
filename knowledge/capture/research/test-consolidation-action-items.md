# Test Suite Consolidation - Specific Action Items

**Investigation Date**: January 6, 2026
**Prepared For**: La Boeuf
**Status**: Ready for Implementation

---

## Item 1: Remove Duplicate Subprocess Fixtures from Core Conftest

**Priority**: HIGHEST (simplest, safest)
**Effort**: 30 minutes
**Risk**: VERY LOW

### What to Do

Delete lines 99-120 from `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/core/conftest.py`

### Current Code (REMOVE THIS)
```python
# Lines 99-119 in tests/core/conftest.py

@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return successful JSON response."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"id": "test.1", "title": "Test", "description": "Desc", "acceptance_criteria": [], "status": "open"}'
    mock_result.stderr = ""

    with patch('jean_claude.core.beads.subprocess.run', return_value=mock_result) as mock:
        yield mock


@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return a failure."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Command failed"

    with patch('jean_claude.core.beads.subprocess.run', return_value=mock_result) as mock:
        yield mock
```

### Why It's Safe
1. Identical functionality exists in root conftest.py (lines 352-372)
2. Pytest conftest.py inheritance chain means tests still access these fixtures
3. No test code changes needed
4. CI/CD will still pass

### Verification
```bash
# Before deletion
grep -n "def mock_subprocess" tests/core/conftest.py
# Should show lines 99 and 111

# After deletion, run tests
uv run pytest tests/core/ -v -k subprocess

# Tests should still pass using inherited fixtures from root conftest.py
```

---

## Item 2: Remove Duplicate Beads Task Factory from Core Conftest

**Priority**: HIGH
**Effort**: 1 hour
**Risk**: LOW

### What to Do

Delete lines 63-90 from `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/core/conftest.py`

### Current Code (REMOVE THIS)
```python
# Lines 63-90 in tests/core/conftest.py

@pytest.fixture
def beads_task_factory() -> Callable[..., BeadsTask]:
    """Factory fixture for creating BeadsTask with custom values.

    Usage:
        def test_something(beads_task_factory):
            task = beads_task_factory(id="custom-id", status="in_progress")
    """
    def _create_task(
        id: str = "factory-task.1",
        title: str = "Factory Task",
        description: str = "Created by factory fixture",
        acceptance_criteria: list[str] | None = None,
        status: str | BeadsTaskStatus = BeadsTaskStatus.OPEN,
        priority: str | BeadsTaskPriority | None = None,
        task_type: str | BeadsTaskType | None = None,
    ) -> BeadsTask:
        if isinstance(status, str):
            status = BeadsTaskStatus(status)
        return BeadsTask(
            id=id,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria or [],
            status=status,
            priority=priority,
            task_type=task_type,
        )
    return _create_task
```

### What Exists in Root

In `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py` (lines 66-101):
- Fixture name: `mock_beads_task_factory` (same functionality, different name)
- Same parameters, same behavior
- Available to all tests including core tests

### How Tests Will Still Work

```python
# Old code (using core conftest factory)
def test_something(beads_task_factory):
    task = beads_task_factory(id="custom-id")

# New code (using inherited root conftest factory)
# Just rename the fixture parameter:
def test_something(mock_beads_task_factory):
    task = mock_beads_task_factory(id="custom-id")

# OR update root conftest.py fixture name to "beads_task_factory"
# (see Item 3 below for naming standardization)
```

### Option A: Simple Removal + Test Updates
1. Delete lines 63-90 from core/conftest.py
2. Update core tests to use `mock_beads_task_factory` (from root)
3. Time: 1 hour

### Option B: Remove + Rename Root Fixture
1. Delete lines 63-90 from core/conftest.py
2. Rename `mock_beads_task_factory` → `beads_task_factory` in root
3. Update all tests that use `mock_beads_task_factory` → `beads_task_factory`
4. Time: 1.5 hours (more changes but cleaner naming)

### Recommended: Option B (better naming)
The "mock_" prefix is redundant - @pytest.fixture already indicates it's a test fixture.

---

## Item 3: Standardize Fixture Naming

**Priority**: MEDIUM
**Effort**: 2-3 hours
**Risk**: MEDIUM (requires test updates)

### What to Do

Rename conftest.py fixtures for consistency.

### Changes in `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py`

**Line 54-62** - Rename fixture:
```python
# BEFORE
@pytest.fixture
def mock_beads_task() -> BeadsTask:
    """Provide a standard mock BeadsTask for testing."""
    return BeadsTask(...)

# AFTER
@pytest.fixture
def sample_beads_task() -> BeadsTask:
    """Provide a standard sample BeadsTask for testing."""
    return BeadsTask(...)
```

**Line 66** - Rename fixture:
```python
# BEFORE
@pytest.fixture
def mock_beads_task_factory():
    """Factory fixture for creating BeadsTask with custom values."""
    ...

# AFTER
@pytest.fixture
def beads_task_factory():
    """Factory fixture for creating BeadsTask with custom values."""
    ...
```

### Rationale
- Drop "mock_" prefix (redundant, less discoverable)
- Use "sample_" for concrete instances
- Use "{domain}_factory" for factory fixtures
- Matches core conftest.py naming (minor adjustment)

### Tests to Update
```bash
# Find all references
grep -r "mock_beads_task\|mock_beads_task_factory" tests/ --include="*.py"

# Estimate: 20-40 test files affected
# Time to update: 1-2 hours with automated replacement
```

### Implementation
```bash
# Automated replacement (careful - may have false positives)
find tests/ -name "*.py" -exec sed -i 's/mock_beads_task_factory/beads_task_factory/g' {} +
find tests/ -name "*.py" -exec sed -i 's/mock_beads_task/sample_beads_task/g' {} +

# Then run full test suite to verify
uv run pytest -v
```

---

## Item 4: Consolidate Duplicate Signature Tests

**Priority**: MEDIUM
**Effort**: 1-2 hours
**Risk**: LOW

### What to Do

Create single parameterized test instead of duplicate tests in two files.

### Files Involved
- `tests/orchestration/test_two_agent_execution.py` (DELETE after consolidation)
- `tests/orchestration/test_auto_continue_execution.py` (DELETE after consolidation)

### Step 1: Create New Test File

Create `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/orchestration/test_orchestration_function_signatures.py`:

```python
# ABOUTME: Verify orchestration modules call correct public functions
# ABOUTME: Consolidated signature tests for two-agent and auto-continue

"""Verify orchestration modules use correct function imports."""

import ast
from pathlib import Path
import pytest


ORCHESTRATION_MODULES = [
    ("two_agent", "jean_claude.orchestration.two_agent"),
    ("auto_continue", "jean_claude.orchestration.auto_continue"),
]


@pytest.mark.parametrize("module_name,module_path", ORCHESTRATION_MODULES)
def test_orchestration_modules_call_execute_prompt_async(module_name, module_path):
    """Verify orchestration modules call execute_prompt_async correctly."""
    # Convert module path to file path
    module_file = module_path.replace(".", "/") + ".py"
    module_path_full = Path(__file__).parent.parent.parent / "src" / module_file

    with open(module_path_full, "r") as f:
        source = f.read()

    tree = ast.parse(source)
    found_call = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "execute_prompt_async":
                    found_call = True
                    break
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr == "execute_prompt_async":
                    found_call = True
                    break

    # Check for await statements
    if not found_call:
        for node in ast.walk(tree):
            if isinstance(node, ast.Await):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "execute_prompt_async":
                            found_call = True
                            break

    assert found_call, f"{module_name}.py should call execute_prompt_async"
```

### Step 2: Delete Old Test Files

Delete these files completely:
1. `tests/orchestration/test_two_agent_execution.py`
2. `tests/orchestration/test_auto_continue_execution.py`

### Step 3: Verify

```bash
# Confirm tests still pass
uv run pytest tests/orchestration/test_orchestration_function_signatures.py -v

# Should see 2 test results (one for each module)
```

### Result
- Single parameterized test covers both modules
- Easier to maintain
- ~50 lines of code removed
- Same test coverage

---

## Item 5: Consolidate Workflow State Factory

**Priority**: LOW (more complex)
**Effort**: 2-3 hours
**Risk**: MEDIUM

### What to Do

Merge orchestration-specific workflow_state_factory logic into root version.

### Current State

**Root version** (tests/conftest.py, lines 179-223):
```python
@pytest.fixture
def workflow_state_factory():
    """Factory fixture for creating WorkflowState with custom values."""
    def _create_state(
        workflow_id: str = "test-workflow-123",
        workflow_name: str = "Test Workflow",
        workflow_type: str = "feature",
        beads_task_id: str = None,
        beads_task_title: str = None,
        phase: str = None,
        max_iterations: int = 10,
        updated_at=None,
        total_cost_usd: float = None,
        total_duration_ms: int = None,
        save_to_path=None,  # <-- SAVE PARAMETER EXISTS!
    ) -> WorkflowState:
        # ... creates state ...
        if save_to_path is not None:
            state.save(save_to_path)
        return state
    return _create_state
```

**Orchestration version** (tests/orchestration/conftest.py, lines 115-138):
```python
@pytest.fixture
def workflow_state_factory(mock_project_root: Path) -> Callable[..., WorkflowState]:
    """Factory fixture for creating WorkflowState with custom values."""
    def _create_state(
        workflow_id: str = "factory-workflow-1",
        workflow_name: str = "Factory Workflow",
        workflow_type: str = "feature",
        max_iterations: int = 10,
        save: bool = True,  # <-- DIFFERENT APPROACH
    ) -> WorkflowState:
        state = WorkflowState(...)
        if save:
            state.save(mock_project_root)  # <-- SAVES TO MOCK_PROJECT_ROOT
        return state
    return _create_state
```

### Problem

The two versions have different approaches:
- Root: explicit `save_to_path` parameter
- Orchestration: boolean `save` parameter that uses `mock_project_root`

### Solution

Enhanced root version that supports both patterns:

```python
@pytest.fixture
def workflow_state_factory(mock_project_root: Path = None):
    """Factory fixture for creating WorkflowState with custom values.

    Args:
        mock_project_root: Optional project root for persistence.
                          Auto-injected when used in orchestration tests.

    Usage:
        # Without persistence (root tests)
        def test_root(workflow_state_factory):
            state = workflow_state_factory(workflow_id="test")

        # With explicit path (root tests)
        def test_root_explicit(workflow_state_factory):
            state = workflow_state_factory(
                workflow_id="test",
                save_to_path=Path("/tmp/agents")
            )

        # With auto-persistence (orchestration tests)
        def test_orch(workflow_state_factory):
            state = workflow_state_factory(
                workflow_id="test",
                save=True  # Uses injected mock_project_root
            )
    """
    def _create_state(
        workflow_id: str = "test-workflow-123",
        workflow_name: str = "Test Workflow",
        workflow_type: str = "feature",
        beads_task_id: str = None,
        beads_task_title: str = None,
        phase: str = None,
        max_iterations: int = 10,
        updated_at=None,
        total_cost_usd: float = None,
        total_duration_ms: int = None,
        save_to_path: Path = None,
        save: bool = False,  # NEW: Boolean flag for auto-save
    ) -> WorkflowState:
        kwargs = {
            "workflow_id": workflow_id,
            "workflow_name": workflow_name,
            "workflow_type": workflow_type,
        }

        if beads_task_id is not None:
            kwargs["beads_task_id"] = beads_task_id
        if beads_task_title is not None:
            kwargs["beads_task_title"] = beads_task_title
        if phase is not None:
            kwargs["phase"] = phase
        if max_iterations != 10:
            kwargs["max_iterations"] = max_iterations
        if updated_at is not None:
            kwargs["updated_at"] = updated_at
        if total_cost_usd is not None:
            kwargs["total_cost_usd"] = total_cost_usd
        if total_duration_ms is not None:
            kwargs["total_duration_ms"] = total_duration_ms

        state = WorkflowState(**kwargs)

        # Support both patterns
        if save and mock_project_root:
            state.save(mock_project_root)
        elif save_to_path is not None:
            state.save(save_to_path)

        return state
    return _create_state
```

### Steps

1. Replace root conftest.py workflow_state_factory with enhanced version above
2. Delete orchestration/conftest.py workflow_state_factory (lines 115-138)
3. Update orchestration tests to use `save=True` instead of custom factory
4. Run tests to verify

### Verification

```bash
# Tests in root that use workflow_state_factory
grep -r "workflow_state_factory" tests/*.py | grep -v orchestration

# Tests in orchestration that use workflow_state_factory
grep -r "workflow_state_factory" tests/orchestration/*.py

# Run both to verify
uv run pytest tests/ -v -k workflow_state_factory
```

---

## Implementation Order

### Week 1 (Priority Phase)
1. **Item 1** (30 min): Remove subprocess fixtures duplicate
   - Verify: `uv run pytest tests/core/ -v`

2. **Item 2** (1 hour): Remove beads_task_factory duplicate
   - Update test parameters if needed
   - Verify: `uv run pytest tests/core/ -v`

3. **Item 4** (1-2 hours): Consolidate signature tests
   - Create new test file
   - Delete old test files
   - Verify: `uv run pytest tests/orchestration/ -v`

### Week 2 (Naming & Consolidation)
4. **Item 3** (2-3 hours): Standardize fixture naming
   - Run automated replacements
   - Manual verification
   - Verify: `uv run pytest -v`

5. **Item 5** (2-3 hours): Consolidate workflow_state_factory
   - Update root version
   - Delete orchestration version
   - Update orchestration tests
   - Verify: `uv run pytest tests/orchestration/ -v`

### Week 3 (Documentation)
6. **Documentation**: Update CLAUDE.md with fixture organization guide

---

## Testing Strategy

### After Each Item
```bash
# Run specific test suite
uv run pytest tests/{affected_area}/ -v

# Look for:
# - Fixture not found errors
# - Import errors
# - Test failures
```

### Final Validation
```bash
# Full test suite
uv run pytest -v

# Check no regression
uv run pytest --cov=jean_claude
```

---

## Rollback Plan

Each item is relatively safe, but if needed:

```bash
# Restore from git
git checkout tests/conftest.py tests/core/conftest.py tests/orchestration/conftest.py

# Or restore individual lines using git show
git show HEAD:tests/core/conftest.py | head -120 > temp.py
```

---

## Questions for La Boeuf

1. Should we rename `mock_*` fixtures to remove "mock_" prefix? (RECOMMENDED: YES)
2. Can we delete entire test files (test_two_agent_execution.py, test_auto_continue_execution.py)? (RECOMMENDED: YES, consolidate to one)
3. Should fixture consolidation happen before or after naming standardization? (RECOMMENDED: After naming to avoid confusion)

---

## Success Criteria

- All tests pass: `uv run pytest -v`
- No fixture errors or warnings
- Fewer conftest.py files with duplicates (4 → 2-3)
- Test coverage percentages unchanged
- CI/CD passes without modification
- CLAUDE.md updated with fixture documentation

---

**Total Estimated Time**: 8-10 hours spread over 3 weeks
**Confidence Level**: HIGH
**Impact**: Cleaner codebase, easier maintenance, no coverage loss
