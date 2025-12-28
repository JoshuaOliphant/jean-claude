# ABOUTME: Subagent registry and factory module
# ABOUTME: Provides specialized subagents for context-efficient task delegation

"""Subagent definitions for Jean Claude CLI.

This module provides a registry of specialized subagents that can be used
to delegate focused tasks while keeping the main agent's context clean.

Subagents are defined as factory functions that return AgentDefinition-compatible
dictionaries. They run in isolated context and return condensed results.
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class SubagentDefinition:
    """SDK-compatible subagent definition.

    This mirrors the claude_agent_sdk.AgentDefinition structure for
    programmatic subagent configuration.

    Attributes:
        description: When to use this subagent (for automatic delegation)
        prompt: The subagent's system prompt defining its role
        tools: List of allowed tools (None = inherit all)
        model: Model to use (haiku for speed, sonnet for quality)
    """

    description: str
    prompt: str
    tools: Optional[List[str]] = None
    model: str = "haiku"

    def to_dict(self) -> Dict:
        """Convert to SDK-compatible dictionary format."""
        return {
            "description": self.description,
            "prompt": self.prompt,
            "tools": self.tools,
            "model": self.model,
        }


# Global registry for subagent factories
_SUBAGENT_REGISTRY: Dict[str, Callable[..., SubagentDefinition]] = {}


def register_subagent(name: str):
    """Decorator to register a subagent factory function.

    Example:
        @register_subagent("my-agent")
        def create_my_agent() -> SubagentDefinition:
            return SubagentDefinition(...)
    """

    def decorator(func: Callable[..., SubagentDefinition]):
        _SUBAGENT_REGISTRY[name] = func
        return func

    return decorator


def get_subagent(name: str, **kwargs) -> SubagentDefinition:
    """Get a single subagent definition by name.

    Args:
        name: The registered subagent name
        **kwargs: Additional arguments to pass to the factory

    Returns:
        SubagentDefinition instance

    Raises:
        KeyError: If subagent name not registered
    """
    if name not in _SUBAGENT_REGISTRY:
        raise KeyError(f"Unknown subagent: {name}. Available: {list(_SUBAGENT_REGISTRY.keys())}")
    return _SUBAGENT_REGISTRY[name](**kwargs)


def get_subagents(names: Optional[List[str]] = None) -> Dict[str, SubagentDefinition]:
    """Get multiple subagent definitions.

    Args:
        names: List of subagent names (None = all registered)

    Returns:
        Dictionary mapping names to SubagentDefinition instances
    """
    if names is None:
        names = list(_SUBAGENT_REGISTRY.keys())
    return {name: get_subagent(name) for name in names}


def get_subagents_for_sdk(names: Optional[List[str]] = None) -> Dict[str, Dict]:
    """Get subagent definitions in SDK-compatible format.

    This is the format expected by ClaudeAgentOptions.agents parameter.

    Args:
        names: List of subagent names (None = all registered)

    Returns:
        Dictionary mapping names to SDK-compatible agent dicts
    """
    subagents = get_subagents(names)
    return {name: agent.to_dict() for name, agent in subagents.items()}


def list_subagents() -> List[str]:
    """List all registered subagent names."""
    return list(_SUBAGENT_REGISTRY.keys())


# =============================================================================
# Built-in Subagents
# =============================================================================


@register_subagent("prime")
def create_prime_subagent() -> SubagentDefinition:
    """Create the prime subagent for project context gathering.

    The prime subagent explores a codebase and returns a condensed summary
    that another agent can use to understand the project quickly.

    Benefits:
        - Uses Haiku for fast, cheap exploration
        - Keeps file traversal out of main agent context
        - Returns focused 500-word summary
    """
    return SubagentDefinition(
        description=(
            "Project context gatherer. Use this to understand codebase structure, "
            "tech stack, and key files before starting work on a task. "
            "Invoke when you need to learn about an unfamiliar project."
        ),
        prompt="""You are a project exploration specialist. Your job is to quickly
understand a codebase and provide a condensed, actionable summary.

## Your Task

Gather the following information:

1. **Project Structure**
   - Run: `git ls-files | head -100` to see file layout
   - Identify: source directories, test directories, config files

2. **Tech Stack**
   - Read: README.md, pyproject.toml, package.json, Cargo.toml (whichever exist)
   - Identify: language, framework, key dependencies

3. **Entry Points**
   - Find: main entry point (main.py, app.py, index.js, etc.)
   - Find: CLI commands if any

4. **Testing**
   - Identify: test framework and location
   - Note: how to run tests

## Output Format

Return a focused summary (UNDER 500 WORDS) structured like this:

**Project**: [name]
**Type**: [web app / CLI / library / etc.]
**Stack**: [language, framework, key deps]

**Structure**:
- src/: [what's here]
- tests/: [testing approach]
- [other notable dirs]

**Entry Points**:
- [how to run/use]

**Testing**:
- [how to test]

**Key Files**:
- [3-5 most important files to understand]

Be concise. Focus on actionable information. Skip obvious details.""",
        tools=["Read", "Grep", "Glob", "Bash"],
        model="haiku",
    )
