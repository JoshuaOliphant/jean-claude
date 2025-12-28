# Commit Error Handling

## Overview

The commit error handling feature provides comprehensive error detection, reporting, and recovery guidance for the commit workflow. When any step of the commit process fails, the system provides clear error messages and actionable recovery suggestions to help agents understand and fix the problem.

## Error Types Handled

### 1. Test Failures

**When it occurs**: Tests fail before commit can be created

**Error message format**:
```
Cannot commit: 3 of 10 tests failed
Failed tests: test_auth_login, test_auth_logout, test_user_validation

Recovery suggestions:
  1. Fix the failing tests before attempting to commit
  2. Run tests locally to identify the root cause
  3. Check test output for assertion errors or exceptions
```

**Recovery actions**:
- Fix the failing tests
- Review test output for specific errors
- Ensure all test dependencies are met

### 2. No Files to Stage

**When it occurs**: No modified files found to include in commit

**Error message format**:
```
Cannot commit: No files to stage

Recovery suggestions:
  1. Verify that changes were made to the codebase
  2. Check if files are already committed (run 'git status')
  3. Ensure file modifications are saved
  4. Review the feature implementation to confirm files were actually modified
```

**Recovery actions**:
- Verify files were modified
- Check git status
- Ensure changes are saved

### 3. Git Conflicts

**When it occurs**: Repository has unresolved merge conflicts

**Error message format**:
```
Cannot commit: Git repository has conflicts
Conflicting files: src/auth.py, tests/test_auth.py

Recovery suggestions:
  1. Resolve merge conflicts before committing
  2. Run 'git status' to see which files have conflicts
  3. Edit conflicting files to resolve markers (<<<<<<, ======, >>>>>>)
  4. After resolving, stage the files with 'git add'
  5. Alternatively, abort the merge with 'git merge --abort'
```

**Recovery actions**:
- Resolve conflict markers in files
- Stage resolved files
- Or abort the merge if needed

### 4. Permission Errors

**When it occurs**: Insufficient permissions to write to repository

**Error message format**:
```
Cannot commit: Insufficient permissions

Recovery suggestions:
  1. Check file and directory permissions in the repository
  2. Ensure you have write access to the .git directory
  3. Verify ownership of repository files (may need 'sudo chown')
  4. Check if .git directory is read-only
  5. Ensure no other process has locked the repository
```

**Recovery actions**:
- Fix file/directory permissions
- Check repository ownership
- Verify .git directory is writable

### 5. Git Hook Failures

**When it occurs**: Pre-commit, commit-msg, or other git hooks fail

**Error message format**:
```
Cannot commit: pre-commit hook failed

Recovery suggestions:
  1. Fix the issues reported by the pre-commit hook
  2. Review hook output for specific validation errors
  3. Common issues: code formatting, linting errors, test requirements
  4. Check for linting errors (pylint, flake8, black, etc.)
  5. Ensure code formatting meets standards
  6. If needed, bypass hook temporarily with 'git commit --no-verify' (not recommended)
```

**Recovery actions**:
- Fix linting/formatting issues
- Address hook validation errors
- Review hook requirements

### 6. Invalid Beads ID

**When it occurs**: Beads task ID is empty, None, or invalid format

**Error message format**:
```
Cannot commit: Invalid Beads task ID: ''

Recovery suggestions:
  1. Ensure Beads task ID is provided and not empty
  2. Verify the task ID format matches expected pattern
  3. Check task metadata to ensure ID was properly set
  4. Valid format example: 'task-name-abc.123'
```

**Recovery actions**:
- Provide valid Beads task ID
- Check task metadata
- Verify ID format

## Implementation Details

### CommitErrorHandler Class

The `CommitErrorHandler` class provides methods for handling different error types:

```python
from jean_claude.core.commit_error_handler import CommitErrorHandler

# Handle test failure
error_info = CommitErrorHandler.handle_test_failure(test_result)

# Handle no files to stage
error_info = CommitErrorHandler.handle_no_files_to_stage()

# Handle git errors (auto-categorizes)
error_info = CommitErrorHandler.handle_git_error(git_error, "commit")

# Handle invalid Beads ID
error_info = CommitErrorHandler.handle_invalid_beads_id(beads_id)
```

### Error Result Structure

All error results follow a consistent structure:

```python
{
    "success": False,
    "commit_sha": None,
    "error": "Enhanced error message with recovery suggestions",
    "step": "test_validation",  # or "file_staging", "message_generation", "commit_execution", "validation"
    "recovery_suggestions": [
        "Suggestion 1",
        "Suggestion 2",
        ...
    ],
    "error_type": "test_failure",  # Classification of error
    "details": {...}  # Optional additional details
}
```

### Integration with FeatureCommitOrchestrator

The `FeatureCommitOrchestrator` uses `CommitErrorHandler` at each step:

1. **Validation step**: Checks for invalid Beads ID
2. **Test validation step**: Handles test failures
3. **File staging step**: Handles no files, permission errors
4. **Message generation step**: Handles parsing/generation failures
5. **Commit execution step**: Handles git conflicts, hooks, other git errors

## Usage in Agent Workflows

When a commit fails, the agent receives:

1. **Clear error identification**: What went wrong
2. **Context**: Which step failed and why
3. **Recovery guidance**: Specific actions to take
4. **Error categorization**: Type of error for programmatic handling

Example agent response:

```
Commit failed during test_validation phase.

Error: Cannot commit: 2 of 5 tests failed
Failed tests: test_login, test_logout

Recovery suggestions:
  1. Fix the failing tests before attempting to commit
  2. Run tests locally to identify the root cause
  3. Check test output for assertion errors or exceptions

I'll investigate the failing tests and fix them before attempting to commit again.
```

## Testing

Comprehensive tests in `tests/test_commit_error_handling.py` cover:

- Test failure scenarios
- No files to stage
- Git conflicts
- Permission errors
- Invalid Beads ID
- Git hook failures
- Test timeouts
- Exception handling
- Error result structure consistency
- Rollback behavior

## Best Practices

1. **Always check error_type**: Use it to programmatically handle different error categories
2. **Show recovery_suggestions to user**: These provide actionable guidance
3. **Log error details**: Include `step` and `details` for debugging
4. **Handle rollback**: The orchestrator automatically rolls back staged files on errors
5. **Validate early**: Beads ID validation happens before any git operations

## Future Enhancements

Potential improvements:

- Add support for more git error types
- Provide automated recovery for some error types
- Integrate with external validation tools
- Add error metrics and reporting
- Provide error-specific documentation links
