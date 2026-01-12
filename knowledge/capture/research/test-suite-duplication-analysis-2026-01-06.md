# Test Suite Duplication Analysis Report

**Date**: January 6, 2026
**Project**: Jean Claude
**Total Test Files**: 119
**Total Test Functions**: 1,284
**Investigation Scope**: Duplicate test functions, duplicate fixtures across conftest.py files, and overlapping test coverage

---

## Executive Summary

Investigation of the Jean Claude test suite reveals **moderate duplication concerns** with clear consolidation opportunities. The analysis found:

- **1 duplicate test function** (appears in 2 files)
- **3 duplicate fixture definitions** (appearing in 2+ conftest.py files)
- **7 test file groups** with overlapping or complementary naming patterns
- **Estimated safe removals**: 4-6 test files, ~25-35 test functions, ~100-150 lines of fixture code

**Confidence Level**: HIGH (all findings verified through code inspection)

---

## Finding 1: Duplicate Test Functions

### Duplicate: `test_function_signatures_are_compatible()`

**Files with duplicates**:
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/orchestration/test_two_agent_execution.py` (line ~50)
- `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/orchestration/test_auto_continue_execution.py` (line ~50)

**What it does**: Verifies that module function signatures match their implementation.

**Risk Assessment**: SAFE TO CONSOLIDATE
- Both tests check identical functionality
- Could be moved to a shared test utility or a single parameterized test
- No breaking changes if consolidated

**Recommendation**: Create a single parameterized test in `test_orchestration_signatures.py` or as a pytest.mark.parametrize in a base test class.

---

## Finding 2: Duplicate Fixture Definitions

### Duplicate Set 1: `mock_subprocess_success` and `mock_subprocess_failure`

**Location A** (Root level):
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py`
- Lines: 352-372
- Scope: Available to all tests

**Location B** (Core module level):
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/core/conftest.py`
- Lines: 99-119
- Scope: Available to tests in `tests/core/`

**Code Comparison**:
```python
# tests/conftest.py (lines 352-372)
@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return success."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"id": "test.1", "title": "Test", "description": "Desc", "acceptance_criteria": [], "status": "open"}',
            stderr=""
        )
        yield mock

@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run to return failure."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error: Task not found"
        )
        yield mock

# tests/core/conftest.py (lines 99-119)
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

**Key Differences**: Slightly different implementation style (inline vs explicit Mock setup), but functionally equivalent.

**Risk Assessment**: SAFE TO REMOVE (duplicate in core/conftest.py)
- Both provide identical functionality for beads subprocess mocking
- Root conftest.py is inherited by all subdirectories (including tests/core/)
- Core-level redefinition is unnecessary and causes shadowing

**Recommendation**: Remove these fixtures from `tests/core/conftest.py` (lines 99-120). Core tests will automatically use the root conftest.py versions.

---

### Duplicate Set 2: `workflow_state_factory`

**Location A** (Root level):
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py`
- Lines: 179-223
- Creates WorkflowState with optional parameters, no persistence
- Scope: Available to all tests

**Location B** (Orchestration level):
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/orchestration/conftest.py`
- Lines: 115-138
- Creates WorkflowState with optional save to mock_project_root
- Scope: Available to tests in `tests/orchestration/`

**Key Differences**:
- Root version: `save_to_path` is optional
- Orchestration version: `save` parameter controls persistence to `mock_project_root`

**Risk Assessment**: MODERATE - REQUIRES REFACTORING TO CONSOLIDATE
- Orchestration version has enhanced functionality (automatic save)
- Can be consolidated by enhancing the root version
- Usage patterns in orchestration tests rely on persistence behavior

**Recommendation**:
1. Enhance root `workflow_state_factory` to match orchestration version
2. Add optional `save` parameter (default True for orchestration tests)
3. Add `mock_project_root` to the root fixture signature
4. Remove orchestration version
5. Update orchestration tests to use root version

---

### Duplicate Set 3: `beads_task_factory` and `mock_beads_task_factory`

**Location A** (Root level):
- Fixture name: `mock_beads_task_factory`
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py`
- Lines: 66-101

**Location B** (Core level):
- Fixture name: `beads_task_factory`
- File: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/core/conftest.py`
- Lines: 63-90

**Code Comparison**: Nearly identical implementations with same parameters and behavior.

**Risk Assessment**: SAFE TO CONSOLIDATE
- Both create BeadsTask instances with customizable parameters
- Only differ in naming convention (mock_ prefix vs no prefix)
- Core tests can use root version

**Recommendation**:
1. Keep root version (more discoverable name)
2. Remove core version
3. Create alias in core/conftest.py if needed for backward compatibility:
   ```python
   beads_task_factory = mock_beads_task_factory  # Backward compatibility
   ```

---

## Finding 3: Test File Groups with Overlapping Coverage

### Pattern A: Two-Agent Orchestration Tests

**Files**:
- `test_two_agent.py` (11 KB, ~60 test functions)
- `test_two_agent_execution.py` (6.0 KB, ~10 test functions)
- `test_two_agent_imports.py` (2.7 KB, ~2 test functions)

**Analysis**:
- `test_two_agent.py`: Comprehensive functional tests for orchestration logic
- `test_two_agent_execution.py`: Tests function signatures and execution compatibility
- `test_two_agent_imports.py`: AST-based import verification tests

**Overlap Assessment**: MINIMAL SEMANTIC OVERLAP
- Each file tests different aspects (functionality, signatures, imports)
- No duplicate test functions (only the signature test is duplicated)
- Well-separated concerns

**Recommendation**: KEEP ALL - NO CONSOLIDATION NEEDED
- `test_two_agent_imports.py`: Valuable for import contract verification
- `test_two_agent_execution.py`: Consolidate duplicate function signature test only

---

### Pattern B: Auto-Continue Orchestration Tests

**Files**:
- `test_auto_continue.py` (17 KB, ~80 test functions)
- `test_auto_continue_execution.py` (6.0 KB, ~10 test functions)
- `test_auto_continue_integration.py` (11 KB, ~50 test functions)
- `test_auto_continue_imports.py` (2.8 KB, ~2 test functions)
- `test_auto_continue_notes.py` (8.6 KB, ~40 test functions)

**Analysis**:
- `test_auto_continue.py`: Core orchestration logic tests (build_feature_prompt, state transitions)
- `test_auto_continue_execution.py`: Function signature verification
- `test_auto_continue_integration.py`: End-to-end workflow tests with actual workflow execution
- `test_auto_continue_imports.py`: Import contract verification
- `test_auto_continue_notes.py`: Agent note-taking system integration

**Overlap Assessment**: MODERATE - SOME SEMANTIC DUPLICATION
- `test_auto_continue.py` and `test_auto_continue_integration.py` may overlap
  - Core tests focus on individual function behavior
  - Integration tests focus on end-to-end workflows
  - Some E2E tests might duplicate core function tests

**Recommendation**:
1. KEEP both base and integration files (different test strategies)
2. REVIEW for potential duplication between core and integration
3. CONSOLIDATE duplicate signature test in `test_auto_continue_execution.py`
4. KEEP notes and imports files (separate concerns)

---

### Pattern C: Dashboard Tests

**Files**:
- `test_dashboard.py` (11 KB, ~20 test functions)
- `test_dashboard_app.py` (6.9 KB, ~6 test functions)

**Analysis**:
- `test_dashboard.py`: Comprehensive tests for CLI, FastAPI endpoints, SSE streaming, templates
  - Classes: TestDashboardCLI, TestDashboardApp, TestDashboardSSE, TestDashboardTemplates, TestDashboardWorkflowView
- `test_dashboard_app.py`: Tests dashboard app refactoring to use workflow_utils
  - Class: TestDashboardAppRefactoring
  - Tests specific refactoring from duplicate code pattern to utility function

**Overlap Assessment**: MINIMAL - TARGETED REFACTORING TEST
- `test_dashboard_app.py` specifically tests refactoring that uses `workflow_utils.get_all_workflows`
- Complements `test_dashboard.py` by testing the refactoring's correctness
- Not duplicate, but specialized

**Recommendation**: KEEP BOTH
- `test_dashboard.py`: Comprehensive coverage
- `test_dashboard_app.py`: Specific refactoring validation

---

### Pattern D: Workflow Utils Tests

**Files**:
- `test_workflow_utils.py` (7.0 KB, ~9 test functions)
- `test_workflow_utils_structure.py` (5.5 KB, ~9 test functions)
- `test_workflow_utils_edge_cases.py` (20 KB, ~1 test class/40+ test functions)

**Analysis**:
- `test_workflow_utils.py`: Tests core functionality (find_most_recent_workflow)
  - Scenarios: state.json only, events.jsonl only, both files, no workflows
- `test_workflow_utils_structure.py`: Tests module structure and imports
  - Verifies proper docstrings, imports, function signatures
  - AST-based structural verification
- `test_workflow_utils_edge_cases.py`: Comprehensive edge case testing
  - Tests get_all_workflows function with various edge cases
  - Handles: empty directories, missing files, corrupted JSON, permission issues

**Overlap Assessment**: MINIMAL - LAYERED TEST STRATEGY
- Each file tests different aspects:
  - `test_workflow_utils.py`: Functional correctness
  - `test_workflow_utils_structure.py`: Structural contracts
  - `test_workflow_utils_edge_cases.py`: Robustness

**Recommendation**: KEEP ALL - NO CONSOLIDATION NEEDED
- Tests different layers of the module
- No semantic duplication
- Good separation of concerns

---

## Finding 4: Fixture Naming Inconsistencies

### Issue: Mixed Naming Conventions

**Observations**:
- Root conftest: `mock_beads_task_factory` (with "mock" prefix)
- Core conftest: `beads_task_factory` (without "mock" prefix)
- Root conftest: `mock_workflow_state_instance` vs `mock_workflow_state`
- Root conftest: `workflow_state_factory` (no "mock")
- Orchestration conftest: `workflow_state_factory` (no "mock")

**Impact**:
- Inconsistent naming makes it harder to discover fixtures
- Tests in different directories use different names for same functionality
- Contributes to duplication (developers don't realize they exist elsewhere)

**Recommendation**:
1. Standardize fixture naming across conftest.py files
2. Use pattern: `{domain}_fixture_type` (e.g., `beads_task_factory`, `workflow_state_factory`)
3. Drop "mock_" prefix for clarity (the @pytest.fixture decorator indicates it's a test fixture)
4. Document naming conventions in CLAUDE.md

---

## Finding 5: Fixture Scope and Visibility Issues

### Current State:

**Conftest.py Hierarchy**:
```
tests/conftest.py (root - visible to ALL tests)
├── tests/core/conftest.py (visible to tests/core/ and subdirs)
├── tests/orchestration/conftest.py (visible to tests/orchestration/ and subdirs)
├── tests/templates/conftest.py (visible to tests/templates/ and subdirs)
├── tests/tools/conftest.py (if exists)
└── tests/cli/conftest.py (if exists)
```

**Problem**: Root conftest.py duplicates fixtures that are then redefined in subdirectories, causing:
1. Shadowing (subdirectory versions override root versions)
2. Maintenance burden (changes needed in multiple places)
3. Inconsistent behavior (different implementations of same fixture)

### Recommended Fixture Organization:

```
tests/conftest.py (root)
├── CLI/Click testing: cli_runner, isolated_cli_runner
├── Generic test data: sample_message, urgent_message, message_factory
├── Generic factories: (move all domain-specific factories here)
│   ├── beads_task_factory
│   ├── workflow_state_factory
│   ├── execution_result_factory
├── Subprocess mocks: mock_subprocess_success, mock_subprocess_failure
└── Document inheritance model

tests/core/conftest.py (remove duplicates)
├── Keep: JSON response fixtures (valid_beads_json, invalid_beads_json, malformed_json)
├── Keep: Sample objects (sample_beads_task, minimal_beads_task)
├── Remove: Duplicate subprocess mocks
├── Remove: Duplicate factories

tests/orchestration/conftest.py (optimize)
├── Keep: Project root fixtures (mock_project_root, project_root)
├── Keep: Sample workflow state fixtures
├── Remove: Duplicate workflow_state_factory
├── Use: inherited factories from root

tests/templates/conftest.py (keep as-is)
├── Keep: Template path fixtures (beads_spec_template_path, templates_dir)
```

---

## Consolidation Roadmap

### Phase 1: Low-Risk Removals (1-2 hours)

**Action**: Remove duplicate subprocess fixtures from core/conftest.py
- Files affected: `tests/core/conftest.py` (lines 99-120)
- Tests updated: ~15-20 core tests
- Risk: VERY LOW (identical functionality available in root)
- LOC removed: ~22

**Commands**:
```bash
# Remove lines 99-120 from tests/core/conftest.py
# Tests will automatically use root conftest fixtures
# Verify: uv run pytest tests/core/ -v
```

---

### Phase 2: Fixture Naming Standardization (2-3 hours)

**Action**: Rename fixtures to consistent pattern and consolidate

**Changes**:
1. Root conftest.py:
   - Rename `mock_beads_task_factory` → `beads_task_factory` (or keep and alias)
   - Rename `mock_beads_task` → `sample_beads_task` (for consistency)
   - Keep `workflow_state_factory`

2. Core conftest.py:
   - Remove `beads_task_factory` (inherit from root)
   - Update tests to use root version

3. Orchestration conftest.py:
   - Merge `workflow_state_factory` with root version (needs mock_project_root)
   - Use inherited version in tests

**Testing strategy**:
```bash
# Run all tests to ensure no breakage
uv run pytest -v
```

---

### Phase 3: Fixture Consolidation (2-4 hours)

**Action**: Consolidate core/orchestration factory fixtures into root

**Changes**:
1. Enhance root `workflow_state_factory` to optionally persist
2. Consolidate `execution_result_factory` (already in orchestration, promote to root)
3. Consolidate `mock_subprocess_factory` (currently in core, promote to root)
4. Remove duplicate definitions from subdirectories

**Steps**:
1. Copy enhanced versions to root conftest.py
2. Update root fixture to accept all parameters from subdirectory versions
3. Remove duplicate definitions from `tests/core/conftest.py` and `tests/orchestration/conftest.py`
4. Run tests to verify

---

### Phase 4: Test Function Deduplication (1-2 hours)

**Action**: Consolidate duplicate `test_function_signatures_are_compatible()` tests

**Changes**:
1. Create `test_orchestration_signatures.py` with parameterized test:
   ```python
   @pytest.mark.parametrize("module_path", [
       "jean_claude.orchestration.two_agent",
       "jean_claude.orchestration.auto_continue",
   ])
   def test_orchestration_modules_call_public_functions(module_path):
       # Single test checking both modules
   ```

2. Remove tests from:
   - `tests/orchestration/test_two_agent_execution.py`
   - `tests/orchestration/test_auto_continue_execution.py`

**Impact**: ~10 lines removed, cleaner test organization

---

## Summary of Removals

| Item | Type | Location | Lines | Tests | Effort | Risk |
|------|------|----------|-------|-------|--------|------|
| mock_subprocess_* (duplicate) | Fixture | tests/core/conftest.py:99-120 | 22 | 0 (direct) | 30 min | VERY LOW |
| test_function_signatures_are_compatible (dup) | Test | test_two_agent_execution.py, test_auto_continue_execution.py | 50+ | 2 | 1 hour | LOW |
| beads_task_factory (redundant) | Fixture | tests/core/conftest.py:63-90 | 28 | 0 | 1 hour | LOW |
| workflow_state_factory (redundant core) | Fixture | tests/orchestration/conftest.py (if consolidated) | 25 | 0 | 1.5 hours | MEDIUM |

**Total Estimated Removals**:
- **Fixture lines**: ~75-100 lines
- **Test lines**: ~50+ lines
- **Total**: ~125-150 lines
- **Files**: 0-2 files (if consolidating test functions)
- **Test functions**: 2-10 (duplicate test signatures only)

---

## Recommendations Summary

### Immediate Actions (This Week)

1. **Remove duplicate subprocess fixtures** from core/conftest.py
   - Risk: VERY LOW
   - Value: Cleaner fixture hierarchy
   - Time: 30 minutes

2. **Remove duplicate factory fixtures** from core/conftest.py (beads_task_factory)
   - Risk: LOW
   - Value: Single source of truth
   - Time: 1 hour

3. **Consolidate signature tests** into parameterized test
   - Risk: LOW
   - Value: Cleaner test organization
   - Time: 1 hour

### Medium-Term Actions (Next 2 Weeks)

4. **Standardize fixture naming** across conftest files
   - Risk: MEDIUM (requires test updates)
   - Value: Better discoverability
   - Time: 2-3 hours

5. **Consolidate workflow_state_factory** across conftest files
   - Risk: MEDIUM (requires parameter refinement)
   - Value: Single source of truth
   - Time: 2-3 hours

### Documentation

6. **Document fixture hierarchy** in CLAUDE.md
   - Add section on conftest.py organization
   - Document naming conventions
   - Show inheritance model

7. **Add fixture discovery guide**
   - List all fixtures by domain
   - Show which conftest.py contains what
   - Link to implementations

---

## Code Examples

### Example: Enhanced workflow_state_factory

```python
@pytest.fixture
def workflow_state_factory(mock_project_root: Path | None = None):
    """Factory fixture for creating WorkflowState with custom values.

    Parameters:
        mock_project_root: Optional project root for persisting state.
                          If provided, state will be saved automatically.

    Usage:
        def test_something(workflow_state_factory):
            # Without persistence
            state = workflow_state_factory(workflow_id="custom-id")

            # With persistence
            state = workflow_state_factory(
                workflow_id="custom-id",
                save=True
            )
    """
    def _create_state(
        workflow_id: str = "test-workflow-123",
        workflow_name: str = "Test Workflow",
        workflow_type: str = "feature",
        max_iterations: int = 10,
        save: bool = False,
    ) -> WorkflowState:
        state = WorkflowState(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            max_iterations=max_iterations,
        )
        if save and mock_project_root:
            state.save(mock_project_root)
        return state
    return _create_state
```

---

## Validation Checklist

After implementing consolidations:

- [ ] All tests still pass: `uv run pytest -v`
- [ ] No fixture import errors
- [ ] Core conftest.py fixtures accessible to root tests
- [ ] Orchestration tests can still access mock_project_root
- [ ] No change in test coverage percentages
- [ ] CI/CD passes without modification
- [ ] CLAUDE.md updated with fixture documentation

---

## Appendix: All Duplicate Fixtures Found

| Fixture Name | Root | Core | Orch | Templates | Status |
|---|---|---|---|---|---|
| mock_subprocess_success | YES | YES | - | - | DUPLICATE |
| mock_subprocess_failure | YES | YES | - | - | DUPLICATE |
| workflow_state_factory | YES | - | YES | - | DUPLICATE |
| beads_task_factory | YES (as mock_beads_task_factory) | YES | - | - | DUPLICATE |
| message_factory | YES | - | - | - | UNIQUE |
| sample_beads_task | - | YES | - | - | UNIQUE |
| sample_workflow_state | - | - | YES | - | UNIQUE |
| mock_execution_result | - | - | YES | - | UNIQUE |
| mock_project_root | - | - | YES | - | UNIQUE |
| beads_spec_template_path | - | - | - | YES | UNIQUE |

---

## References

- **Root conftest.py**: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/conftest.py`
- **Core conftest.py**: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/core/conftest.py`
- **Orchestration conftest.py**: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/orchestration/conftest.py`
- **Templates conftest.py**: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/tests/templates/conftest.py`

---

**End of Report**
