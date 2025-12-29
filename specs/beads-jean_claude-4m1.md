# Add error handling to unprotected file I/O operations

## Description

## Problem
Multiple CLI commands perform file reads/writes with NO error handling for PermissionError, FileNotFoundError, or OSError.

## Files to Modify
1. src/jean_claude/cli/commands/work.py (line 216)
2. src/jean_claude/cli/commands/initialize.py (line 97)
3. src/jean_claude/cli/commands/workflow.py (line 148)

## Locations
### work.py:216
```python
spec_path.write_text(spec_content)  # NO ERROR HANDLING
```

### initialize.py:97
```python
spec_content = spec_file.read_text()  # NO ERROR HANDLING
```

### workflow.py:148
```python
spec_content = spec_file.read_text()  # NO ERROR HANDLING
```

## Fix Pattern (Use for All)
```python
try:
    spec_path.write_text(spec_content)
except PermissionError:
    console.print(f'[red]Permission denied writing to {spec_path}[/red]')
    raise click.Abort()
except OSError as e:
    console.print(f'[red]Failed to write {spec_path}: {e}[/red]')
    raise click.Abort()
```

For read operations:
```python
try:
    spec_content = spec_file.read_text()
except FileNotFoundError:
    console.print(f'[red]Spec file not found: {spec_file}[/red]')
    raise click.Abort()
except PermissionError:
    console.print(f'[red]Permission denied reading {spec_file}[/red]')
    raise click.Abort()
except OSError as e:
    console.print(f'[red]Failed to read {spec_file}: {e}[/red]')
    raise click.Abort()
```

## Acceptance Criteria
- [ ] All 3 file operations wrapped in try-except
- [ ] Specific error messages for each error type
- [ ] User-friendly error output with Rich console
- [ ] Tests pass: uv run pytest tests/ -k 'work or initialize or workflow' -v
- [ ] Add test cases for file I/O errors

## Test Requirements
For each command, add:
```python
def test_command_handles_permission_error(tmp_path, monkeypatch):
    # Mock file operation to raise PermissionError
    # Assert click.Abort raised
    # Assert error message shown
```

## Dependencies
None - can start immediately

## Agent Notes
🔴 CRITICAL - Production bug
📬 Message when all 3 files updated
🧪 Add tests for PermissionError, FileNotFoundError, OSError
⚡ Can work on files in parallel

## Time Estimate
Agent: ~1.5 hours (3 files + 6-9 tests)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-4m1
- **Status**: open
- **Created**: 2025-12-28 17:12:18
- **Updated**: 2025-12-28 17:12:18
