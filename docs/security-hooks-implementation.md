# Security Hooks Implementation

Implementation of pre-tool-use security hooks for Jean Claude CLI, following Anthropic's autonomous agent patterns.

## Overview

This implementation adds defense-in-depth security for autonomous agent execution using the Claude Code SDK's hook system. It validates bash commands against configurable allowlists before they execute, preventing unauthorized or dangerous operations.

## Architecture

### Three-Layer Security Model

1. **Environment Isolation** (deployment level)
   - Docker containers
   - Sandboxed environments
   - Network restrictions

2. **SDK Tool Permissions** (SDK level)
   - Allowed tools: `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`
   - Configured in `ClaudeCodeOptions`

3. **Command Allowlist** (hook level)
   - Pre-tool-use hook validates bash commands
   - Configurable per workflow type
   - Smart command parsing

## Implementation Details

### Files Created

1. **`src/jean_claude/core/security.py`** (260 lines)
   - Command validation logic
   - Allowlist management
   - Pre-tool-use hook implementation
   - Helper functions for custom allowlists

2. **`tests/test_security.py`** (289 lines)
   - 29 comprehensive tests
   - Command parsing tests
   - Validation logic tests
   - Hook integration tests
   - Real-world scenario tests

3. **`tests/test_security_integration.py`** (123 lines)
   - 10 integration tests
   - SDK integration validation
   - Workflow type configuration tests
   - Default behavior verification

### Files Modified

1. **`src/jean_claude/core/agent.py`**
   - Added `workflow_type` parameter to `PromptRequest`
   - Added `enable_security_hooks` parameter (default: True)

2. **`src/jean_claude/core/sdk_executor.py`**
   - Imported `HookMatcher` and `bash_security_hook`
   - Created hook wrapper to inject workflow context
   - Configured hooks in `ClaudeCodeOptions`

3. **`CLAUDE.md`**
   - Added "Security Configuration" section
   - Documented workflow types and allowlists
   - Added usage examples

4. **`docs/autonomous-agent-patterns.md`**
   - Updated Phase 2 status to show completion
   - Marked security hooks as implemented

## Workflow Types

### Readonly (Most Restrictive)
**Use case**: Code exploration, analysis, reporting

**Allowed commands**:
- File inspection: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`
- Version control: `git` (read-only operations)
- Process inspection: `ps`, `lsof`

**Blocked commands**: `mkdir`, `chmod`, `cp`, `rm`, `mv`

### Development (Default)
**Use case**: Normal development workflows

**Allowed commands**: All readonly commands plus:
- File operations: `cp`, `mkdir`, `touch`, `chmod`
- Development tools: `python`, `uv`, `pytest`, `ruff`
- Node.js: `npm`, `node`, `npx`
- Utilities: `echo`, `date`, `sleep`

**Blocked commands**: `rm`, `dd`, destructive operations

### Testing
**Use case**: Running test suites with coverage

**Allowed commands**: All development commands plus:
- Test runners: `coverage`, `tox`
- Additional test tools as configured

## Command Parsing

The security module intelligently parses bash commands to extract the base command:

```python
extract_base_command("FOO=bar /usr/bin/python -m pytest")
# Returns: "python"

extract_base_command("ls -la | grep test")
# Returns: "ls"

extract_base_command("echo test > file.txt")
# Returns: "echo"
```

**Handles**:
- Full paths (`/usr/bin/python` → `python`)
- Environment variables (`FOO=bar cmd` → `cmd`)
- Pipes (`cmd1 | cmd2` → `cmd1`)
- Redirects (`cmd > file` → `cmd`)
- Complex shell constructs

## Usage Examples

### Basic Usage (Default Security)

```python
from jean_claude.core.agent import PromptRequest
from jean_claude.core.sdk_executor import execute_prompt_async

# Security enabled by default, development workflow
request = PromptRequest(
    prompt="Add logging to the API",
    model="sonnet",
)

result = await execute_prompt_async(request)
```

### Readonly Workflow

```python
request = PromptRequest(
    prompt="Analyze the codebase structure",
    workflow_type="readonly",  # Blocks write operations
)

result = await execute_prompt_async(request)
```

### Custom Allowlist

```python
from jean_claude.core.security import create_custom_allowlist, bash_security_hook

# Create custom allowlist
allowlist = create_custom_allowlist("ls", "cat", "special-tool")

# Use in hook context
context = {"command_allowlist": allowlist}
result = await bash_security_hook(
    {"command": "special-tool --run"},
    context=context
)
# Returns: {"decision": "allow"}
```

### Disabling Security (Caution)

```python
# Only for trusted, controlled environments
request = PromptRequest(
    prompt="Emergency fix",
    enable_security_hooks=False,  # ⚠️ Disables all command validation
)
```

## Hook Integration

The security hook is registered with the Claude Code SDK:

```python
# In sdk_executor.py
async def security_hook_wrapper(
    tool_input: dict[str, Any],
    tool_use_id: str | None = None,
    hook_context: Any = None,
) -> dict[str, Any]:
    context = {"workflow_type": request.workflow_type}
    return await bash_security_hook(tool_input, tool_use_id, context)

hooks = {
    "PreToolUse": [
        HookMatcher(matcher="Bash", hooks=[security_hook_wrapper])
    ]
}

options = ClaudeCodeOptions(
    model=model,
    hooks=hooks,
    # ... other options
)
```

## Testing

### Test Coverage

- **29 unit tests** in `test_security.py`
  - Command parsing (7 tests)
  - Validation logic (7 tests)
  - Async hook (5 tests)
  - Workflow allowlists (3 tests)
  - Helper functions (3 tests)
  - Real-world scenarios (4 tests)

- **10 integration tests** in `test_security_integration.py`
  - SDK integration (4 tests)
  - Default behavior (4 tests)
  - Context passing (2 tests)

### Running Tests

```bash
# Run security tests only
uv run pytest tests/test_security.py -v

# Run integration tests
uv run pytest tests/test_security_integration.py -v

# Run all security tests
uv run pytest tests/test_security*.py -v

# All tests with coverage
uv run pytest tests/ --cov=src/jean_claude/core/security
```

## Security Best Practices

### For Autonomous Workflows

1. **Use readonly for exploration**: When agents explore codebases, use `workflow_type="readonly"`
2. **Default to development**: Most tasks work fine with the default security
3. **Never disable in production**: Only disable hooks for debugging in controlled environments
4. **Custom allowlists for specialized tools**: Create specific allowlists for domain-specific tools

### For Production Deployments

1. **Layer defenses**: Use Docker + SDK permissions + command allowlists
2. **Log blocked commands**: Monitor security hook blocks for suspicious activity
3. **Audit allowlists**: Regularly review and minimize command allowlists
4. **Environment isolation**: Run autonomous agents in sandboxed containers

### For Development

1. **Start with readonly**: Explore new codebases in readonly mode
2. **Test security**: Verify hooks block dangerous commands
3. **Custom workflows**: Create workflow-specific allowlists for specialized tasks

## Future Enhancements

Potential improvements for future phases:

1. **Argument validation**: Validate command arguments, not just base commands
2. **Path restrictions**: Restrict file operations to specific directories
3. **Rate limiting**: Limit command execution frequency
4. **Audit logging**: Persist all hook decisions for compliance
5. **Machine learning**: Detect anomalous command patterns
6. **Workflow templates**: Pre-defined security profiles for common tasks

## References

- **Anthropic Patterns**: `docs/autonomous-agent-patterns.md`
- **Claude Code SDK**: https://docs.anthropic.com/en/docs/claude-agent-sdk
- **Source Code**:
  - Security module: `src/jean_claude/core/security.py`
  - SDK executor: `src/jean_claude/core/sdk_executor.py`
  - Tests: `tests/test_security*.py`

## Migration Guide

### For Existing Code

The security hooks are **enabled by default** with **development workflow**. Existing code continues to work without changes:

```python
# Before (still works)
request = PromptRequest(prompt="Build feature")

# After (explicitly configured)
request = PromptRequest(
    prompt="Build feature",
    workflow_type="development",  # default
    enable_security_hooks=True    # default
)
```

### For New Workflows

Consider security requirements when designing workflows:

```python
# Exploration workflow
explore_request = PromptRequest(
    prompt="Analyze architecture",
    workflow_type="readonly",  # No modifications
)

# Development workflow
dev_request = PromptRequest(
    prompt="Add feature",
    workflow_type="development",  # Safe tools
)

# CI/CD workflow
ci_request = PromptRequest(
    prompt="Run tests",
    workflow_type="testing",  # Test runners
)
```

## Conclusion

The security hooks implementation provides robust, layered security for autonomous agent execution while maintaining ease of use. The default settings protect against common mistakes while allowing legitimate development tasks to proceed smoothly.

**Key achievements**:
- ✅ Defense-in-depth security model
- ✅ Three workflow types with graduated permissions
- ✅ Smart command parsing
- ✅ 39 comprehensive tests (100% pass rate)
- ✅ SDK integration with Claude Code
- ✅ Backward compatible defaults
- ✅ Configurable and extensible

This foundation enables safe autonomous workflows for the Jean Claude CLI while maintaining the flexibility needed for diverse development tasks.
