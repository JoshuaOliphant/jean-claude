# Claude SDK MCP Integration Fixes

**Date**: 2026-01-01
**Authors**: Knowledge Capturer Agent
**Status**: Completed and Verified

## Summary

Fixed 3 critical bugs preventing Claude Agent SDK from working with MCP servers. All tests pass, workflow running successfully.

## Context

Jean Claude uses the Claude Agent SDK Python implementation to orchestrate AI workflows. MCP (Model Context Protocol) servers provide tools like filesystem access. The integration was completely broken with 3 separate bugs.

## Bugs Fixed

### Bug 1: ProcessTransport Race Condition

**Symptom**: `CLIConnectionError: ProcessTransport is not ready for writing`

**Impact**: Complete failure when using MCP servers

**Root Cause**: SDK bug (#386, #266, #176) - ProcessTransport accepts writes before initialization completes when using string prompts.

**Solution**: Convert string prompts to async generators

**Code Added**:
```python
# src/jean_claude/core/sdk_executor.py

async def _string_to_async_generator(prompt: str) -> AsyncIterator[dict[str, Any]]:
    """Convert string prompt to async generator format required by SDK.

    This works around ProcessTransport race condition by allowing SDK
    to pull messages at its own pace rather than having data pushed
    before it's ready.

    References:
        - GitHub Issue #386: Async generator workaround
        - GitHub Issue #266: ProcessTransport race condition
        - GitHub Issue #176: Transport not ready errors
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": prompt},
        "parent_tool_use_id": None,
    }
```

**Changes**:
- `src/jean_claude/core/sdk_executor.py`: Added helper function, updated all `query()` calls
- `src/jean_claude/orchestration/auto_continue.py`: Re-enabled MCP servers

**Why It Works**: Async generators use pull-based flow - SDK requests messages when ready, eliminating race condition.

### Bug 2: Incorrect Message Format

**Symptom**:
- "Expected message type 'user' or 'control', got 'text'"
- "'role' field undefined"

**Impact**: SDK rejected all prompts even after fixing race condition

**Discovery Process**:
1. Started with documentation example: `{"type": "text", "text": prompt}` ❌
2. Tried adding type: `{"type": "user", "content": prompt}` ❌
3. Tried adding role: `{"role": "user", "content": prompt}` ❌
4. Read SDK source code: Found correct format ✅

**Correct Format**:
```python
{
    "type": "user",                          # Top-level wrapper
    "message": {                             # Nested message object
        "role": "user",                      # Role within message
        "content": prompt                    # Actual content
    },
    "parent_tool_use_id": None              # Tool use context
}
```

**Source**: `.venv/lib/python3.12/site-packages/claude_agent_sdk/query.py:48-54`

**Lesson**: Documentation showed `ClaudeSDKClient` examples (different interface). We use `query()` function (different format). Always verify format in source code.

### Bug 3: Hook Decision Vocabulary Mismatch

**Symptom**: `ZodError: Invalid enum value. Expected 'approve' | 'block', received 'allow'`

**Impact**: Security hooks failed validation even when logic was correct

**Root Cause**: Hook returned `{decision: "allow"}` but SDK expects `{decision: "approve"}`

**Fix**: One-word change
```python
# src/jean_claude/core/security.py:243

# BEFORE
return {"decision": "allow"}

# AFTER
return {"decision": "approve"}
```

**Changes**:
- `src/jean_claude/core/security.py`: Changed vocabulary
- `tests/test_security.py`: Updated test expectations

**Lesson**: Zod validation errors show exact expected values. Trust them.

## Testing Strategy

**Approach**: Test immediately after each fix, don't batch changes

```bash
# After Bug 1 fix
uv run pytest tests/orchestration/test_auto_continue.py -v
# ✅ ProcessTransport errors gone

# After Bug 2 fix
uv run pytest tests/orchestration/test_auto_continue.py -v
# ✅ Message format errors gone

# After Bug 3 fix
uv run pytest tests/test_security.py -v
# ✅ All 21 tests pass

# Verify no regressions
uv run pytest tests/
# ✅ All 37 tests pass
```

**Result**:
- ✅ All tests passing
- ✅ Workflow running successfully for 30+ minutes
- ✅ 1/15 features completed (event-data-models)
- ✅ Zero errors in logs

## Debugging Techniques Used

1. **Error Message Analysis**
   - Read full output, not just summary
   - Zod errors show exact expected values
   - Used those values directly

2. **ExceptionGroup Extraction**
   - Python 3.11+ wraps errors in ExceptionGroups
   - Created recursive unwrapper to get root cause
   - Found actual SDK errors hidden in wrappers

3. **Source Code Inspection**
   - Used `uv run python -c "from sdk import query; import inspect; print(inspect.signature(query))"`
   - Read actual SDK source in `.venv/`
   - Found correct message format in code vs docs

4. **Upstream Issue Search**
   - Searched GitHub issues for error messages
   - Found #386, #266, #176 documenting race condition
   - Found async generator workaround

5. **Iterative Testing**
   - Changed one thing at a time
   - Ran tests immediately after each change
   - Built confidence incrementally

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `src/jean_claude/core/sdk_executor.py` | Added `_string_to_async_generator()`, updated calls | Fix race condition and message format |
| `src/jean_claude/orchestration/auto_continue.py` | Re-enabled MCP servers | Stop disabling broken functionality |
| `src/jean_claude/core/security.py` | Changed "allow" to "approve" | Fix hook vocabulary |
| `tests/test_security.py` | Updated expectations | Match new vocabulary |

## Commits

- `2e61baf` - Initial ProcessTransport investigation
- `95713be` - Async generator workaround
- `589cc93` - Message format correction
- `916ff88` - Hook vocabulary fix

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Security tests passing | 0/21 | 21/21 ✅ |
| Auto-continue tests passing | 0/16 | 16/16 ✅ |
| All tests passing | 0/37 | 37/37 ✅ |
| Workflow runtime | Immediate crash | 30+ minutes ✅ |
| Features completed | 0/15 | 1/15 ✅ |
| MCP servers working | No | Yes ✅ |

## Lessons Learned

### For SDK Integration

1. **Don't trust documentation blindly** - Verify in source code
2. **Different interfaces need different formats** - `ClaudeSDKClient` vs `query()`
3. **Async generators solve race conditions** - Pull vs push model
4. **Validation errors are precise** - Use exact values they specify

### For Debugging

1. **Read full error messages** - Critical clues in details
2. **Unwrap ExceptionGroups** - Python 3.11+ hides root causes
3. **Search upstream issues** - Others have likely hit same bugs
4. **Test after each change** - Know what fixed it
5. **Check source code** - Don't assume docs are current

### For Testing

1. **Test immediately** - Don't batch changes
2. **Run full suite** - Catch regressions early
3. **Trust test failures** - They show exactly what's wrong
4. **Don't skip verification** - Running workflow confirms it works

## Future Considerations

### When SDK Bug is Fixed

If SDK fixes ProcessTransport race condition:
- Async generator approach still works
- Could add feature detection to use strings when safe
- Keep generator approach for compatibility

### Message Format Changes

If SDK changes message format:
- Update `_string_to_async_generator()` only
- All callers continue working unchanged
- Encapsulation pays off

### Other SDK Interfaces

If we use `ClaudeSDKClient` class:
- May need different message format
- Check source code, don't assume same format
- Write tests immediately

## Related Documentation

- [Pattern: Claude SDK MCP Integration](../patterns/claude-sdk-mcp-integration.md)
- [Pattern: SDK Debugging Techniques](../patterns/sdk-debugging-techniques.md)
- [Decision: Async Generator for SDK Prompts](../decisions/async-generator-for-sdk-prompts.md)

## Tags

#implementation #sdk-integration #mcp-servers #debugging #bug-fixes #async #race-conditions
