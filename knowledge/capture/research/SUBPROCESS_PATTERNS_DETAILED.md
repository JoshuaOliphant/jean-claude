# Subprocess Patterns - Detailed Reference Guide

**Purpose**: Complete reference for all subprocess mocking patterns found in Jean Claude test suite
**Date**: 2026-01-06
**Target**: Developers wanting to understand or extend subprocess mocking

---

## Table of Contents

1. [Overall Statistics](#overall-statistics)
2. [Beads (bd) Command Mocking](#beads-bd-command-mocking)
3. [Git Command Mocking](#git-command-mocking)
4. [Pytest Execution Mocking](#pytest-execution-mocking)
5. [Pattern Library](#pattern-library)
6. [Common Mistakes & How to Avoid Them](#common-mistakes--how-to-avoid-them)
7. [Testing Checklist](#testing-checklist)

---

## Overall Statistics

**Test Suite Overview**:
```
Total test files:           129
Files with subprocess mocks:   8
Total subprocess mocks:       54
Mock pattern coverage:    100% (all external tools mocked)

Distribution:
├── Beads operations       17 mocks (31%)
├── Edit workflows         11 mocks (20%)
├── Test runner             6 mocks (11%)
├── Feature commits         5 mocks (9%)
├── Git operations          5 mocks (9%)
├── Commit generation       5 mocks (9%)
└── Verification            1 mock  (2%)

Recursive pytest patterns:    0 (NONE FOUND - tests are isolated)
```

---

## Beads (bd) Command Mocking

### Files Involved
- `/tests/core/test_beads.py` (17 mocks)
- `/tests/test_edit_integration.py` (11 mocks)

### Commands Mocked

#### 1. fetch_beads_task (Show Task)
```python
# Command: bd --no-daemon show --json <task-id>

@patch('jean_claude.core.beads.subprocess.run')
def test_fetch_beads_task(mock_run):
    """Fetch a Beads task and return BeadsTask object."""
    mock_result = Mock()
    mock_result.stdout = json.dumps({
        "id": "gt-123",
        "title": "Test task",
        "description": "Test description",
        "status": "open",
        "acceptance_criteria": [],
        "priority": 2,
        "issue_type": "feature"
    })
    mock_run.return_value = mock_result

    task = fetch_beads_task("gt-123")

    # Verify subprocess called with correct command
    assert mock_run.called
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == 'bd'
    assert call_args[1] == '--no-daemon'
    assert 'show' in call_args
    assert '--json' in call_args
```

**Tests Implemented**:
- ✅ Valid ID proceeds to subprocess
- ✅ Invalid ID blocked BEFORE subprocess (security)
- ✅ Command injection blocked BEFORE subprocess (security)
- ✅ --no-daemon flag present
- ✅ Returns BeadsTask model correctly

#### 2. update_beads_status (Update Status)
```python
# Command: bd --no-daemon update --status <status> <task-id>

@patch('jean_claude.core.beads.subprocess.run')
def test_update_beads_status(mock_run):
    """Update Beads task status."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    update_beads_status("gt-123", "in_progress")

    # Verify subprocess called correctly
    call_args = mock_run.call_args[0][0]
    assert ['bd', '--no-daemon', 'update', '--status', 'in_progress', 'gt-123'] == call_args
```

**Tests Implemented**:
- ✅ Valid status update proceeds
- ✅ Invalid ID blocked BEFORE subprocess (security)
- ✅ Status validation
- ✅ --no-daemon flag present

#### 3. close_beads_task (Close Task)
```python
# Command: bd --no-daemon close <task-id>

@patch('jean_claude.core.beads.subprocess.run')
def test_close_beads_task(mock_run):
    """Close a Beads task."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    close_beads_task("gt-123")

    # Verify --no-daemon flag
    call_args = mock_run.call_args[0][0]
    assert call_args[0:2] == ['bd', '--no-daemon']
```

**Tests Implemented**:
- ✅ Valid task closed
- ✅ Invalid ID blocked BEFORE subprocess
- ✅ --no-daemon flag present

#### 4. EditTaskHandler.edit_task (Edit in Editor)
```python
# Command: bd --no-daemon edit <task-id>

@patch('subprocess.run')
def test_edit_task_calls_bd_edit(mock_run):
    """Edit task opens it in editor via bd edit command."""
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

    handler = EditTaskHandler()
    handler.edit_task("test-task-1")

    # Verify subprocess.run called with correct arguments
    call_args = mock_run.call_args[0][0]
    assert call_args == ['bd', '--no-daemon', 'edit', 'test-task-1']
```

**Tests Implemented**:
- ✅ Calls bd edit command
- ✅ Empty task ID raises error
- ✅ Handles subprocess errors
- ✅ check=True passed (waits for completion)

### Security Pattern: Validate Before Subprocess

**Critical Finding**: All Beads tests verify that input validation happens BEFORE subprocess execution.

```python
def test_invalid_id_blocked_before_subprocess(self):
    """SECURITY: Invalid ID should be blocked before any subprocess call."""
    with patch('jean_claude.core.beads.subprocess.run') as mock_run:
        # This should raise before subprocess.run is ever called
        with pytest.raises(ValueError, match="Invalid beads task ID format"):
            fetch_beads_task("../../etc/passwd")  # Path traversal attempt

        # CRITICAL ASSERTION: subprocess was NEVER called
        mock_run.assert_not_called()
```

**Why This Matters**:
- No shell injection possible
- All command-building happens in safe Python code
- Security gate is tested to actually work

### Beads ID Validation Test Cases

```python
def test_command_injection_attempts_blocked(self):
    """SECURITY: Block command injection attempts."""
    malicious_ids = [
        "beads-123; rm -rf /",           # Command chaining
        "beads-123 && echo pwned",       # Command chaining
        "beads-123|cat /etc/shadow",     # Pipe operator
        "beads-123`whoami`",             # Command substitution
        "beads-123$(whoami)",            # Command substitution
        "../etc/passwd",                 # Path traversal
        "../../secrets",                 # Path traversal
        "beads-123\nrm -rf",            # Newline injection
    ]

    for malicious_id in malicious_ids:
        with pytest.raises(ValueError, match="Invalid beads task ID format"):
            fetch_beads_task(malicious_id)
        # Each would verify mock_run.assert_not_called()
```

---

## Git Command Mocking

### File Involved
- `/tests/test_git_file_stager.py` (5 mocks)
- `/tests/test_commit_body_generator.py` (5 mocks)

### Commands Mocked

#### 1. Get Modified Files
```python
# Command: git status --porcelain

@patch('subprocess.run')
def test_get_modified_files_success_and_status_types(mock_run):
    """Get modified files from git status with various status indicators."""
    mock_run.return_value = Mock(
        returncode=0,
        stdout="M  file1.py\nA  file2.py\nD  file3.py\nR  file4.py\nMM file5.py\n",
        stderr=""
    )

    stager = GitFileStager()
    files = stager.get_modified_files()

    # Should parse all status indicators
    assert len(files) >= 4
    assert "file1.py" in files  # Modified
    assert "file2.py" in files  # Added
    assert "file3.py" in files  # Deleted
    assert "file4.py" in files  # Renamed
```

**Status Indicators Tested**:
- M = Modified
- A = Added
- D = Deleted
- R = Renamed
- MM = Merge conflict

#### 2. Get File Diff
```python
# Command: git diff <file> or git diff --cached <file>

@patch('subprocess.run')
def test_get_file_diff_success_empty_and_error(mock_run):
    """Get diff for a file, handle empty diff and errors."""
    stager = GitFileStager()

    # Success case
    expected_diff = "+++ b/src/main.py\n@@ -1,3 +1,4 @@\n+new line"
    mock_run.return_value = Mock(returncode=0, stdout=expected_diff, stderr="")
    assert stager.get_file_diff("src/main.py") == expected_diff

    # Empty diff
    mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
    assert stager.get_file_diff("unchanged.py") == ""

    # Error case
    mock_run.return_value = Mock(returncode=128, stdout="", stderr="fatal: bad revision")
    with pytest.raises(RuntimeError, match="Git diff failed"):
        stager.get_file_diff("nonexistent.py")
```

**Test Coverage**:
- ✅ Successful diff retrieval
- ✅ Empty diff (file unchanged)
- ✅ Git errors (bad revision, not a git repo)
- ✅ Staged-only diffs (--cached flag)

---

## Pytest Execution Mocking

### File Involved
- `/tests/test_test_runner_validator.py` (6 mocks)
- `/tests/test_verification.py` (1 mock)

### Commands Mocked

#### 1. Run Pytest Tests
```python
# Command: pytest (with various return codes)

@pytest.mark.parametrize("returncode,stdout,stderr,expected_passed", [
    (0, "===== 10 passed in 2.34s =====", "", True),
    (1, "===== 2 failed, 8 passed in 3.45s =====", "", False),
    (2, "", "ERROR: Test collection failed", False),
    (1, "===== 1 failed =====", "DeprecationWarning: old API", False),
])
@patch('subprocess.run')
def test_run_tests_returns_correct_result(mock_run, returncode, stdout, stderr, expected_passed):
    """Test that run_tests returns correct result for various pytest scenarios."""
    mock_run.return_value = Mock(returncode=returncode, stdout=stdout, stderr=stderr)

    validator = TestRunnerValidator()
    result = validator.run_tests()

    assert result["passed"] is expected_passed
    assert result["exit_code"] == returncode
```

**Return Codes Tested**:
- 0 = All tests passed
- 1 = Some tests failed
- 2 = Test collection error

#### 2. Handle Pytest Errors
```python
@pytest.mark.parametrize("error_type,error_msg", [
    (subprocess.SubprocessError, "Command not found"),
    (subprocess.TimeoutExpired, "timeout"),
    (PermissionError, "Permission denied"),
    (FileNotFoundError, "pytest not found"),
])
@patch('subprocess.run')
def test_run_tests_handles_errors(mock_run, error_type, error_msg):
    """Handle various subprocess errors gracefully."""
    if error_type == subprocess.TimeoutExpired:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pytest", timeout=30)
    else:
        mock_run.side_effect = error_type(error_msg)

    validator = TestRunnerValidator(timeout=30)
    result = validator.run_tests()

    assert result["passed"] is False
    assert result["error"] is not None
```

**Error Scenarios**:
- ✅ Subprocess not found
- ✅ Timeout (when timeout parameter set)
- ✅ Permission denied
- ✅ File not found

---

## Pattern Library

### Pattern 1: Simple Mock with Return Value

```python
@patch('jean_claude.core.beads.subprocess.run')
def test_something(mock_run):
    # Setup mock to return specific values
    mock_run.return_value = Mock(
        returncode=0,
        stdout='{"id": "test"}',
        stderr=""
    )

    # Call function that uses subprocess
    result = fetch_beads_task("test-id")

    # Assert the function was called
    assert mock_run.called
    assert result.id == "test"
```

**Use When**: Testing simple operations with predictable output

### Pattern 2: Fixture-Based Reuse

```python
# conftest.py
@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run to return success."""
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        mock.return_value = Mock(
            returncode=0,
            stdout='{"id": "test"}',
            stderr=""
        )
        yield mock

# test_file.py
def test_feature_one(mock_subprocess_success):
    # mock_subprocess_success is already configured
    result = fetch_beads_task("test-id")
    assert result.id == "test"

def test_feature_two(mock_subprocess_success):
    # Same mock, different test
    assert mock_subprocess_success.called
```

**Use When**: Multiple tests need the same mock configuration

### Pattern 3: Factory Fixture for Custom Responses

```python
# conftest.py
@pytest.fixture
def mock_subprocess_factory():
    """Create custom subprocess mocks."""
    def _create_mock(returncode=0, stdout="", stderr=""):
        mock_result = Mock()
        mock_result.returncode = returncode
        mock_result.stdout = stdout
        mock_result.stderr = stderr
        return patch('jean_claude.core.beads.subprocess.run', return_value=mock_result)
    return _create_mock

# test_file.py
def test_with_custom_response(mock_subprocess_factory):
    with mock_subprocess_factory(returncode=1, stderr="Task not found") as mock:
        with pytest.raises(RuntimeError):
            fetch_beads_task("invalid-id")
```

**Use When**: Tests need varied subprocess responses

### Pattern 4: Parameterized Tests with Mocks

```python
@pytest.mark.parametrize("returncode,expected_passed", [
    (0, True),
    (1, False),
    (2, False),
])
@patch('subprocess.run')
def test_various_exit_codes(mock_run, returncode, expected_passed):
    """Test handling of various pytest exit codes."""
    mock_run.return_value = Mock(returncode=returncode, stdout="")

    result = run_tests()
    assert result["passed"] is expected_passed
```

**Use When**: Multiple similar scenarios need testing

### Pattern 5: Side Effects for Complex Workflows

```python
@patch('subprocess.run')
def test_multi_step_workflow(mock_run):
    """Test workflow with multiple subprocess calls."""
    # Setup side effects for sequential calls
    mock_run.side_effect = [
        Mock(returncode=0, stdout='{"id": "test"}'),  # First call
        Mock(returncode=0),                           # Second call
        Mock(returncode=0),                           # Third call
    ]

    # Execute workflow
    task = fetch_beads_task("test-id")
    update_beads_status("test-id", "in_progress")
    close_beads_task("test-id")

    # Verify all three calls were made
    assert mock_run.call_count == 3
```

**Use When**: Testing workflows with multiple subprocess calls

### Pattern 6: Security Pattern - Validate Before Subprocess

```python
def test_invalid_input_blocked_before_subprocess(self):
    """SECURITY: Verify invalid input is rejected before subprocess call."""
    with patch('jean_claude.core.module.subprocess.run') as mock_run:
        # This should raise ValueError during validation
        with pytest.raises(ValueError, match="Invalid"):
            some_function("malicious; input")

        # CRITICAL: subprocess.run should never be called
        mock_run.assert_not_called()
```

**Use When**: Testing security-critical functions that accept user input

**Key Principle**: Validation happens in Python, not relying on shell safety

---

## Common Mistakes & How to Avoid Them

### Mistake 1: Patching in Wrong Location

```python
# ❌ WRONG - Patching where subprocess is defined
@patch('subprocess.run')
def test_fetch_beads_task(mock_run):
    # This won't work if beads.py does: from subprocess import run
    pass

# ✅ CORRECT - Patch where subprocess is USED
@patch('jean_claude.core.beads.subprocess.run')
def test_fetch_beads_task(mock_run):
    # This works regardless of how beads.py imports subprocess
    pass
```

**Rule**: Patch in the module that imports and uses subprocess, not the subprocess module itself.

### Mistake 2: Forgetting to Verify Critical Assertions

```python
# ❌ INCOMPLETE - Doesn't verify subprocess wasn't called
def test_invalid_input(mock_run):
    with pytest.raises(ValueError):
        fetch_beads_task("invalid")
    # Missing: mock_run.assert_not_called()

# ✅ COMPLETE - Verifies security gate
def test_invalid_input(mock_run):
    with pytest.raises(ValueError):
        fetch_beads_task("invalid")
    # CRITICAL: Verify subprocess wasn't called
    mock_run.assert_not_called()
```

**Rule**: For security-critical tests, always verify subprocess wasn't called for invalid input.

### Mistake 3: Mock Return Value Doesn't Match Reality

```python
# ❌ WRONG - Incomplete Mock object
mock_run.return_value = Mock(stdout='{"id": "test"}')
# Missing: returncode and stderr

# ✅ CORRECT - Complete Mock object
mock_run.return_value = Mock(
    returncode=0,          # CompletedProcess attribute
    stdout='{"id": "test"}',  # CompletedProcess attribute
    stderr=""              # CompletedProcess attribute
)
```

**Rule**: Mock's return value should mimic subprocess.CompletedProcess attributes: returncode, stdout, stderr.

### Mistake 4: Not Cleaning Up Mock State Between Tests

```python
# ❌ WRONG - Mock persists between tests
mock_run = Mock()

def test_one(mock_run):
    mock_run.return_value = Mock(returncode=0)
    # ... test code ...

def test_two(mock_run):
    # mock_run might still have state from test_one!
    pass

# ✅ CORRECT - Use fixtures for clean state
@pytest.fixture
def mock_subprocess_success():
    with patch('jean_claude.core.beads.subprocess.run') as mock:
        yield mock  # Fresh mock for each test
```

**Rule**: Use fixtures with yield for automatic cleanup.

### Mistake 5: Assuming Mock Was Called Without Verification

```python
# ❌ WRONG - Doesn't verify subprocess was called
def test_fetch_beads_task(mock_run):
    result = fetch_beads_task("test-id")
    assert result.id == "test-id"
    # No verification that subprocess.run was called!

# ✅ CORRECT - Verify subprocess was called
def test_fetch_beads_task(mock_run):
    result = fetch_beads_task("test-id")

    # Verify subprocess was called
    assert mock_run.called or mock_run.call_count > 0

    # Even better: verify specific call
    mock_run.assert_called_once()
```

**Rule**: Explicitly verify mocked functions were called as expected.

### Mistake 6: Not Testing Error Paths

```python
# ❌ INCOMPLETE - Only tests success case
@patch('subprocess.run')
def test_fetch_beads_task(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout='{"id": "test"}')
    result = fetch_beads_task("test-id")
    assert result.id == "test-id"

# ✅ COMPLETE - Tests both success and failure
@patch('subprocess.run')
def test_fetch_beads_task_success(mock_run):
    mock_run.return_value = Mock(returncode=0, stdout='{"id": "test"}')
    result = fetch_beads_task("test-id")
    assert result.id == "test-id"

@patch('subprocess.run')
def test_fetch_beads_task_error(mock_run):
    mock_run.return_value = Mock(returncode=1, stderr="Task not found")
    with pytest.raises(RuntimeError):
        fetch_beads_task("test-id")
```

**Rule**: Test both success and failure paths for subprocess operations.

---

## Testing Checklist

When writing tests for subprocess operations, verify:

### Input Validation Tests
- [ ] Valid inputs proceed to subprocess call
- [ ] Invalid inputs are rejected BEFORE subprocess
- [ ] Command injection attempts are blocked BEFORE subprocess
- [ ] Error messages are clear and helpful

### Success Path Tests
- [ ] Subprocess is called with correct arguments
- [ ] Return value is properly parsed/converted
- [ ] No errors are raised
- [ ] Output is as expected

### Error Path Tests
- [ ] Non-zero return codes are handled
- [ ] stderr is captured and reported
- [ ] TimeoutExpired exceptions are caught
- [ ] FileNotFoundError is handled (tool not installed)
- [ ] PermissionError is handled (no execute permission)

### Mock Verification Tests
- [ ] Mock was called (assert_called or call_count)
- [ ] Mock was called with correct arguments (assert_called_with)
- [ ] Mock was called correct number of times
- [ ] Mock was NOT called for invalid input (security)

### Integration Tests
- [ ] Multiple subprocess calls in correct sequence
- [ ] Side effects work correctly (for sequential calls)
- [ ] Cleanup happens properly (fixture yield)
- [ ] No state leakage between tests

### Security Tests (if applicable)
- [ ] Input validation happens BEFORE subprocess
- [ ] Command injection attempts are blocked
- [ ] Path traversal attempts are blocked
- [ ] Privilege escalation is not possible
- [ ] Shell metacharacters are escaped/rejected

---

## Quick Reference: Patch Locations by Module

```python
# Beads operations
@patch('jean_claude.core.beads.subprocess.run')

# Edit tasks
@patch('jean_claude.core.edit_task_handler.subprocess.run')

# Git operations
@patch('jean_claude.core.git_file_stager.subprocess.run')
@patch('jean_claude.core.commit_body_generator.subprocess.run')

# Test verification
@patch('jean_claude.core.verification.subprocess.run')

# Test running
@patch('jean_claude.core.test_runner_validator.subprocess.run')

# Feature commits
@patch('jean_claude.core.feature_commit_orchestrator.subprocess.run')
```

---

## Summary

This pattern library demonstrates that the Jean Claude test suite has:

1. **Comprehensive subprocess mocking** - All external tools covered
2. **Security-first approach** - Validation before subprocess
3. **Fixture-based reuse** - DRY principle applied
4. **Clear error handling** - Both success and failure paths tested
5. **Proper isolation** - No mock leakage or test pollution

Follow these patterns when adding new subprocess-using code to maintain consistency and quality.
