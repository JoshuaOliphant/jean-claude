# Code Patterns

Reusable patterns discovered during Jean Claude development.

## Pattern Categories

### Testing Patterns
- [Mock Patching Location](./mock-patching-location.md) - Patch where objects are used, not defined

### SDK Integration Patterns
- [Claude SDK MCP Integration](./claude-sdk-mcp-integration.md) - Complete guide to integrating MCP servers with Claude Agent SDK
- [SDK Debugging Techniques](./sdk-debugging-techniques.md) - Proven techniques for debugging SDK integration issues

### Async Patterns
- Race condition prevention with async generators
- ExceptionGroup handling in Python 3.11+
- Pull vs push models for async communication

## Recent Additions (2026-01-01)

### Claude Agent SDK MCP Integration

Complete patterns for working with Claude Agent SDK and MCP servers:
- ProcessTransport race condition workaround (async generators)
- Correct message format for `query()` function
- Hook decision vocabulary ("approve/block" not "allow/deny")
- Error extraction from ExceptionGroups
- Source code inspection techniques

**Files**:
- [claude-sdk-mcp-integration.md](./claude-sdk-mcp-integration.md) - Integration patterns and solutions
- [sdk-debugging-techniques.md](./sdk-debugging-techniques.md) - Debugging methodology

**Related Documentation**:
- [Decision: Async Generator for SDK Prompts](../decisions/async-generator-for-sdk-prompts.md)
- [Implementation: Claude SDK MCP Integration Fixes](../doc/implementation/claude-sdk-mcp-integration-fixes.md)

## How to Use

When you discover a pattern that works well:

1. Document it in this directory
2. Include code examples
3. Explain when to use it
4. Note any gotchas
5. Add to this README index

## Example Pattern Template

```markdown
# Pattern Name

## Problem
What problem does this solve?

## Solution
How does it solve it?

## Example
```python
# Code example
```

## When to Use
- Scenario 1
- Scenario 2

## Gotchas
- Thing to watch out for
```

## Tags Index

Search patterns by tags:

- `#sdk-integration` - Claude SDK MCP Integration, SDK Debugging Techniques
- `#async-patterns` - Async generators, race conditions
- `#debugging` - SDK Debugging Techniques
- `#mcp-servers` - Claude SDK MCP Integration
- `#testing` - Mock Patching Location
- `#error-handling` - ExceptionGroup extraction, message format validation
