# SDK Integration Debugging Techniques

**Date**: 2026-01-01
**Context**: Techniques that successfully debugged Claude Agent SDK MCP integration
**Confidence**: High
**Applicability**: Any Python SDK integration, especially async SDKs

## Overview

Proven debugging techniques for SDK integration issues, especially when dealing with async operations, message formats, and validation errors. These techniques successfully resolved 3 critical bugs in the Claude Agent SDK integration.

## Technique 1: Error Message Deep Analysis

**Pattern**: Read full error output, not just summary. Modern error messages contain critical clues.

**Example**:
```
ZodError: Invalid enum value. Expected 'approve' | 'block', received 'allow'
```

**Analysis**:
- Error type: Zod validation (TypeScript schema validator)
- Expected values: Explicitly listed - "approve" or "block"
- Received value: "allow"
- Action: Change "allow" to "approve"

**Key**: The error message told us EXACTLY what to do. Trust validation errors.

## Technique 2: ExceptionGroup Extraction

**Problem**: Python 3.11+ wraps exceptions in ExceptionGroups, hiding root causes

**Solution**: Recursive error unwrapping
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

**Usage in debugging**:
```python
try:
    result = await query(prompt, mcp_servers=mcp_servers)
except Exception as e:
    # Don't just print(e) - it only shows wrapper
    detailed_error = _extract_error_message(e)
    print(f"Actual error: {detailed_error}")
```

**Pattern**: For modern Python SDKs using exception groups, always unwrap to find root cause.

## Technique 3: Source Code Inspection

**Pattern**: When documentation fails, read the source code directly

**Method 1: Inspect SDK types**
```bash
uv run python -c "from claude_agent_sdk import query; import inspect; print(inspect.signature(query))"
```

**Method 2: Read implementation**
```bash
# Find SDK installation
uv run python -c "import claude_agent_sdk; print(claude_agent_sdk.__file__)"

# Read the source
cat .venv/lib/python3.12/site-packages/claude_agent_sdk/query.py
```

**Method 3: Use IDE navigation**
- In VS Code: Cmd+Click on function name
- Jumps to actual implementation in .venv/

**Real Example**:
Documentation showed: `{"type": "text", "text": prompt}`
Source code showed: `{"type": "user", "message": {"role": "user", "content": prompt}}`

**Lesson**: Documentation may be for different interfaces. Source code is always correct.

## Technique 4: Iterative Format Testing

**Pattern**: When format errors occur, iterate systematically with immediate testing

**Process**:
1. Try format from documentation
2. Run test immediately: `uv run pytest tests/test_sdk.py -v`
3. Read error message carefully
4. Adjust format based on error
5. Repeat until tests pass

**Example iteration**:
```python
# Attempt 1: From docs
{"type": "text", "text": prompt}
# Error: Expected message type 'user' or 'control', got 'text'

# Attempt 2: Fix type
{"type": "user", "content": prompt}
# Error: 'role' field undefined

# Attempt 3: Add role
{"role": "user", "content": prompt}
# Error: Expected message type 'user' or 'control'

# Attempt 4: Nested structure (from source)
{"type": "user", "message": {"role": "user", "content": prompt}}
# ✅ Tests pass!
```

**Key**: Each iteration provides new clues. Don't batch changes - test after each attempt.

## Technique 5: Web Search for Upstream Issues

**Pattern**: SDK bugs are often already reported. Search GitHub issues before deep debugging.

**Process**:
1. Copy exact error message
2. Search: `site:github.com/organization/repo "error message"`
3. Look for open and closed issues
4. Check issue comments for workarounds

**Real Example**:
- Error: "ProcessTransport is not ready for writing"
- Search: `site:github.com/anthropic-ai/agent-sdk "ProcessTransport is not ready"`
- Found: Issues #386, #266, #176
- Workaround: Use async generators instead of strings

**Benefit**: Don't reinvent solutions. Others have likely hit the same issue.

## Technique 6: Async Race Condition Analysis

**Pattern**: For "not ready" errors in async code, suspect race conditions

**Symptoms**:
- Intermittent failures
- "Not ready" messages
- Timing-dependent behavior

**Solutions**:
1. **Add synchronization**: Use generators for pull-based flow
2. **Add delays**: `await asyncio.sleep(0)` to yield control
3. **Use locks**: `asyncio.Lock()` for critical sections
4. **Check initialization**: Ensure resources are ready before use

**Example**:
```python
# WRONG - Push model, may race
async def send_prompt(prompt: str):
    return await sdk.query(prompt)  # SDK might not be ready

# RIGHT - Pull model, SDK controls timing
async def send_prompt(prompt: str):
    async def prompt_generator():
        yield {"type": "user", "message": {"role": "user", "content": prompt}}

    return await sdk.query(prompt_generator())
```

**Pattern**: Generators provide implicit synchronization - consumer pulls at its own pace.

## Technique 7: Immediate Test-Driven Debugging

**Pattern**: Write/run tests immediately after each change, don't batch

**Process**:
1. Make minimal change
2. Run relevant tests: `uv run pytest tests/test_specific.py -v`
3. If tests fail, read output carefully
4. Make next minimal change
5. Repeat

**Benefits**:
- Know exactly which change caused success/failure
- Catch regressions immediately
- Build confidence incrementally

**Example**:
```bash
# Fix 1: Add async generator
uv run pytest tests/test_sdk.py::test_query_with_mcp -v
# ✅ ProcessTransport error gone

# Fix 2: Correct message format
uv run pytest tests/test_sdk.py::test_query_with_mcp -v
# ✅ Format error gone

# Fix 3: Change hook vocabulary
uv run pytest tests/test_security.py -v
# ✅ All 21 tests pass

# Verify no regressions
uv run pytest tests/
# ✅ All tests pass
```

**Key**: Each test run validates progress and prevents backsliding.

## Technique 8: Documentation Skepticism

**Pattern**: Trust but verify. Documentation can be outdated, wrong, or for different interfaces.

**Verification Methods**:
1. Check source code (see Technique 3)
2. Look at test files in SDK repo
3. Search for examples in GitHub issues
4. Try both documented and inferred formats

**Red Flags**:
- Documentation examples that cause errors
- Type mismatches between docs and error messages
- Examples that don't match function signatures

**Example**:
- Docs showed: `ClaudeSDKClient` examples
- We used: `query()` function (different interface)
- Result: Wrong message format
- Fix: Read `query()` source code directly

**Lesson**: Documentation may lag behind code. Source code is always current.

## Debugging Workflow Summary

1. **Read error message carefully** - Full output, not just summary
2. **Unwrap ExceptionGroups** - Get to root cause
3. **Search upstream issues** - Don't reinvent solutions
4. **Inspect source code** - Documentation may be wrong
5. **Iterate with tests** - Test after each minimal change
6. **Trust validation errors** - They tell you exactly what's wrong
7. **Consider async races** - Use generators for synchronization

## Anti-Patterns to Avoid

❌ **Assuming documentation is correct** - Always verify with source
❌ **Making multiple changes at once** - Can't tell what fixed it
❌ **Ignoring full error messages** - Critical clues in details
❌ **Giving up after first failure** - Iterate systematically
❌ **Skipping tests** - How do you know it's fixed?
❌ **Working around instead of fixing** - Understand root cause

## Success Metrics

These techniques led to:
- ✅ 3 critical bugs fixed in one session
- ✅ All 37 tests passing
- ✅ Workflow running successfully for 30+ minutes
- ✅ Root causes understood, not just symptoms
- ✅ Knowledge captured for future debugging

## Applicability

These techniques work for:
- Python SDK integrations (especially async)
- TypeScript/JavaScript SDK integrations (Zod validation)
- Any library with complex message formats
- Race condition debugging
- Validation error debugging

## Related Patterns

- [Claude SDK MCP Integration](./claude-sdk-mcp-integration.md) - Specific patterns found
- [Mock Patching Location](./mock-patching-location.md) - Testing patterns

## Tags

#debugging #sdk-integration #async #error-handling #testing #source-code-analysis #race-conditions
