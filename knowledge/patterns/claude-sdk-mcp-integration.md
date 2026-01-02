# Claude Agent SDK MCP Server Integration Patterns

**Date**: 2026-01-01
**Context**: Debugging Claude Agent SDK Python implementation for MCP server support
**Confidence**: High
**Status**: Verified working in production

## Overview

Comprehensive patterns and solutions for integrating MCP (Model Context Protocol) servers with the Claude Agent SDK Python implementation. These patterns emerged from fixing 3 critical bugs that prevented MCP servers from working correctly.

## Critical Bugs Fixed

### 1. ProcessTransport Race Condition

**Problem**: `CLIConnectionError: ProcessTransport is not ready for writing`

**Root Cause**: Known SDK bug (#386, #266, #176) - race condition when using string prompts with MCP servers. The SDK's ProcessTransport isn't ready to accept writes when string prompts are passed directly.

**Solution**: Convert string prompts to async generators

```python
async def _string_to_async_generator(prompt: str) -> AsyncIterator[dict[str, Any]]:
    """Convert string prompt to async generator format required by SDK.

    This works around ProcessTransport race condition by allowing SDK
    to pull messages at its own pace rather than having data pushed
    before it's ready.
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": prompt},
        "parent_tool_use_id": None,
    }

# Usage
prompt_gen = _string_to_async_generator(prompt_text)
response = await query(prompt_gen, mcp_servers=mcp_servers, hooks=hooks)
```

**Why This Works**: Async generators provide implicit synchronization - the SDK pulls messages at its own pace rather than having data pushed before the transport is ready. This is a pull model vs push model.

**Pattern**: For async race conditions in SDK integrations, generators provide natural synchronization boundaries.

**References**:
- GitHub issues: #386 (async generator fix), #266, #176 (ProcessTransport errors)
- Implementation: `src/jean_claude/core/sdk_executor.py`

### 2. Message Format Discovery

**Problem**: Multiple format errors:
- "Expected message type 'user' or 'control', got 'text'"
- "'role' field undefined"

**Discovery Process** (failed iterations):
1. ❌ `{"type": "text", "text": prompt}` - From ClaudeSDKClient docs, wrong interface
2. ❌ `{"type": "user", "content": prompt}` - Missing nested structure
3. ❌ `{"role": "user", "content": prompt}` - Missing type wrapper
4. ✅ `{"type": "user", "message": {"role": "user", "content": prompt}}`

**Correct Format**:
```python
{
    "type": "user",                          # Top-level type wrapper
    "message": {                             # Nested message object
        "role": "user",                      # Role within message
        "content": prompt                    # Actual prompt text
    },
    "parent_tool_use_id": None              # Tool use context (None for top-level)
}
```

**Discovery Method**: Read SDK source code directly at `.venv/lib/python3.12/site-packages/claude_agent_sdk/query.py:48-54`

**Pattern**: Documentation examples may be for different SDK interfaces (ClaudeSDKClient vs query()). Always check source code when debugging format errors.

**Lesson**: When SDK integration fails with format errors:
1. Don't assume documentation is correct
2. Inspect SDK types with Python introspection: `uv run python -c "from claude_agent_sdk import query; import inspect; print(inspect.signature(query))"`
3. Read actual implementation in `.venv/` when docs insufficient

### 3. Hook Decision Vocabulary Mismatch

**Problem**: `ZodError: Invalid enum value. Expected 'approve' | 'block', received 'allow'`

**Root Cause**: Security hook returned `{decision: "allow"}` but SDK expects `{decision: "approve"}`

**Fix**: Change hook return vocabulary
```python
# WRONG
return {"decision": "allow"}

# CORRECT
return {"decision": "approve"}
```

**Location**: `src/jean_claude/core/security.py:243`

**Pattern**: SDK vocabularies evolve - enum mismatches caught by Zod validation are helpful diagnostic signals. The error message shows exact expected values.

**Lesson**: For enum validation errors:
1. Error message shows exact expected values - use them
2. Don't assume your vocabulary matches SDK vocabulary
3. Zod/Pydantic validation errors are precise - trust them

## Integration Checklist

When integrating Claude Agent SDK with MCP servers:

- [ ] Use async generator for prompts (not raw strings)
- [ ] Use correct message format: `{type: "user", message: {role, content}}`
- [ ] Use "approve/block" for hook decisions (not "allow/deny")
- [ ] Extract error details from ExceptionGroups (Python 3.11+)
- [ ] Test immediately after each fix with pytest
- [ ] Check SDK source code when docs are insufficient

## Error Extraction Pattern

**Problem**: Python 3.11+ wraps SDK errors in ExceptionGroups, hiding the real error

**Solution**: Recursive error extraction
```python
def _extract_error_message(error: Exception) -> str:
    """Extract detailed error message from SDK exceptions.

    SDK errors are often wrapped in ExceptionGroups (Python 3.11+).
    This recursively extracts the underlying error message.
    """
    if isinstance(error, ExceptionGroup):
        # Recursively extract from first exception in group
        if error.exceptions:
            return _extract_error_message(error.exceptions[0])

    # Return string representation for leaf exceptions
    return str(error)
```

**Usage**:
```python
try:
    result = await query(prompt, mcp_servers=mcp_servers)
except Exception as e:
    error_msg = _extract_error_message(e)
    # Now error_msg contains the actual SDK error, not wrapper
```

## Testing Strategy

**Critical**: All fixes were tested immediately with pytest before committing

```bash
# Test security hooks after vocabulary fix
uv run pytest tests/test_security.py -v

# Test auto_continue after re-enabling MCP
uv run pytest tests/orchestration/test_auto_continue.py -v

# Verify no regressions
uv run pytest tests/
```

**Success Metrics**:
- ✅ All 21 security tests pass
- ✅ All 16 auto_continue tests pass
- ✅ Workflow running successfully for 30+ minutes
- ✅ No ProcessTransport errors
- ✅ No message format errors
- ✅ No hook decision errors

## Anti-Patterns Avoided

❌ **Giving up after first format attempt failed** - Kept iterating until found correct format
❌ **Assuming documentation was correct** - Verified in source code instead
❌ **Disabling MCP servers permanently** - Fixed root cause instead of working around
❌ **Making assumptions about message format** - Verified in SDK source code
❌ **Ignoring upstream GitHub issues** - Found known bugs and workarounds

## Generalizable Principles

1. **When SDK integration fails**: Check source code, not just docs
2. **For async race conditions**: Generators provide natural synchronization
3. **For enum mismatches**: Zod/validation errors show exact expected values
4. **For complex debugging**: Extract error details recursively (ExceptionGroups)
5. **For message format discovery**: Inspect SDK types with Python introspection
6. **For production fixes**: Test immediately, don't batch changes

## Context for Future Work

### SDK Interface Differences

The async generator pattern and message format are specific to the `query()` function. Other SDK interfaces may use different formats:

- `query()` function: `{type: "user", message: {role, content}}` with async generators
- `ClaudeSDKClient` class: May use different format - check docs for that interface

### Hook Vocabulary

Hook decision vocabulary is standardized across SDK:
- Approve/Block: "approve" or "block"
- Not "allow/deny", "accept/reject", "permit/forbid"

### MCP Server Configuration

MCP servers are now working correctly with:
```python
mcp_servers = [
    MCPServer(
        name="filesystem",
        command="uvx",
        args=["mcp-server-filesystem", str(project_root)],
    )
]
```

## Files Modified

- `src/jean_claude/core/sdk_executor.py` - Added async generator helper, fixed message format
- `src/jean_claude/orchestration/auto_continue.py` - Re-enabled MCP servers
- `src/jean_claude/core/security.py` - Changed "allow" to "approve"
- `tests/test_security.py` - Updated test expectations

## Related Commits

- 2e61baf - Initial ProcessTransport investigation
- 95713be - Async generator workaround
- 589cc93 - Message format correction
- 916ff88 - Hook vocabulary fix

## Tags

#sdk-integration #mcp-servers #debugging #async-patterns #race-conditions #message-formats #error-handling #claude-agent-sdk
