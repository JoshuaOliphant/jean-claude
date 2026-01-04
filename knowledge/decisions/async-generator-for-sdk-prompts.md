# Use Async Generators for Claude SDK Prompts

**Date**: 2026-01-01
**Status**: Accepted
**Confidence**: High

## Context

The Claude Agent SDK Python implementation has a race condition bug in its ProcessTransport when using string prompts with MCP servers. The transport isn't ready to accept writes when prompts are passed directly as strings.

## Problem

```python
# This causes: CLIConnectionError: ProcessTransport is not ready for writing
response = await query("Write code", mcp_servers=mcp_servers)
```

Error occurs because:
1. SDK initializes ProcessTransport for MCP server communication
2. String prompt is immediately pushed to transport
3. Transport hasn't finished initialization
4. Write fails with "not ready" error

## Decision

**Convert all prompts to async generators** before passing to SDK's `query()` function.

## Implementation

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

## Rationale

### Why Async Generators Solve the Race Condition

**Push Model (Broken)**:
```
[Our Code] --push--> [SDK Transport]
                         ↓
                    (Not ready yet!)
                         ❌
```

**Pull Model (Working)**:
```
[Our Code] <--pull-- [SDK Transport]
    ↓                     ↓
 (Yields when         (Pulls when
  requested)           ready)
    ✅
```

Async generators are:
- **Lazy**: Values only generated when requested
- **Synchronizing**: Consumer controls timing
- **Backpressure-aware**: Producer waits for consumer

The SDK pulls from the generator at its own pace, after the transport is ready.

### Alternative Solutions Considered

1. **Add delays before writing**
   - ❌ Fragile - how long to wait?
   - ❌ Still races on slow systems
   - ❌ Adds latency to every call

2. **Wait for transport ready signal**
   - ❌ SDK doesn't expose ready event
   - ❌ Would require SDK changes
   - ❌ Still a push model internally

3. **Disable MCP servers**
   - ❌ Loses critical functionality
   - ❌ Workaround instead of fix
   - ❌ Users need MCP servers

4. **Use ClaudeSDKClient class instead**
   - ❌ Different interface (stateful vs functional)
   - ❌ May have same race condition
   - ❌ Requires larger refactor

5. **Async generator (Chosen)**
   - ✅ Eliminates race condition
   - ✅ SDK controls timing
   - ✅ Minimal code change
   - ✅ Works with existing API
   - ✅ Confirmed fix in upstream issues

## Trade-offs

### Advantages
- Fixes race condition completely
- Minimal code changes (single helper function)
- Works with existing SDK API
- No performance penalty
- Upstream-approved workaround (GitHub #386)

### Disadvantages
- Slightly more verbose than string prompts
- Requires understanding of async generators
- Not obvious why it's needed (needs documentation)

### Mitigations
- Helper function hides complexity
- Comprehensive documentation in this decision
- Clear comments in code explaining why

## Upstream Status

This is a **known SDK bug** with open issues:
- #386 - Async generator workaround recommended
- #266 - ProcessTransport race condition
- #176 - Transport not ready errors

SDK team acknowledges the issue. Async generators are the recommended workaround until a proper fix is released.

## Testing

Verified with:
```bash
# Security hooks with MCP servers
uv run pytest tests/test_security.py -v
# ✅ All 21 tests pass

# Auto-continue workflow with MCP servers
uv run pytest tests/orchestration/test_auto_continue.py -v
# ✅ All 16 tests pass

# Full workflow running for 30+ minutes
# ✅ No ProcessTransport errors
```

## Future Considerations

### When SDK Bug is Fixed

If/when SDK fixes the race condition:
1. Keep async generator approach (works with or without bug)
2. OR add feature detection:
   ```python
   if sdk_supports_string_prompts():
       return await query(prompt_string, ...)
   else:
       return await query(_string_to_async_generator(prompt_string), ...)
   ```

### If Message Format Changes

The generator yields specific format:
```python
{
    "type": "user",
    "message": {"role": "user", "content": prompt},
    "parent_tool_use_id": None,
}
```

If SDK changes this format:
- Update `_string_to_async_generator()` only
- All callers continue working unchanged

## Implementation Files

- `src/jean_claude/core/sdk_executor.py` - Helper function and usage
- `src/jean_claude/orchestration/auto_continue.py` - Re-enabled MCP servers
- `tests/test_security.py` - Tests with MCP servers enabled

## Related Decisions

- [Use Claude Agent SDK for orchestration](./use-claude-agent-sdk.md) (if exists)

## References

- GitHub Issue #386: https://github.com/anthropic-ai/agent-sdk/issues/386
- GitHub Issue #266: https://github.com/anthropic-ai/agent-sdk/issues/266
- GitHub Issue #176: https://github.com/anthropic-ai/agent-sdk/issues/176
- SDK Source: `.venv/lib/python3.12/site-packages/claude_agent_sdk/query.py`

## Tags

#async #race-condition #workaround #sdk-integration #generators #mcp-servers
