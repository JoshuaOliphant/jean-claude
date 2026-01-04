# ABOUTME: Async execution module using the Claude Agent SDK
# ABOUTME: Provides SDK-based execution with streaming, retry logic, and observability

"""Claude Agent SDK executor module.

This module provides async execution of Claude Agent prompts using the official
Claude Agent SDK. It maintains compatibility with the existing ExecutionResult
model while adding proper async support and subagent capabilities.
"""

import json
import time
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import anyio

from claude_agent_sdk import (
    ClaudeAgentOptions,
    AgentDefinition,
    query,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    HookMatcher,
)
from claude_agent_sdk.types import Message

from jean_claude.core.agent import (
    ExecutionResult,
    RetryCode,
    PromptRequest,
    TemplateRequest,
    OUTPUT_JSONL,
    OUTPUT_JSON,
    FINAL_OBJECT_JSON,
    generate_workflow_id,
)
from jean_claude.core.security import bash_security_hook


async def _string_to_async_generator(prompt: str) -> AsyncIterator[dict[str, Any]]:
    """Convert string prompt to async generator for SDK MCP servers.

    SDK MCP servers have a bug with string prompts that causes ProcessTransport
    errors. Using async generator prompts works around this issue.
    See: https://github.com/anthropics/claude-agent-sdk-python/issues/386

    Args:
        prompt: The prompt string to convert

    Yields:
        Dict with structure: {type: "user", message: {role: "user", content: "..."}}
    """
    yield {
        "type": "user",
        "message": {"role": "user", "content": prompt},
        "parent_tool_use_id": None,
    }


def _extract_error_message(exception: Exception) -> str:
    """Extract meaningful error message from exception, handling ExceptionGroups.

    Python 3.11+ uses ExceptionGroup for concurrent operations. When an ExceptionGroup
    is raised, str(e) only shows "unhandled errors in a TaskGroup (N sub-exceptions)"
    without the actual error details. This function extracts the real errors.

    Args:
        exception: The exception to extract message from

    Returns:
        Human-readable error message with actual exception details
    """
    # Check if it's an ExceptionGroup (Python 3.11+)
    if hasattr(exception, 'exceptions'):
        # Extract all underlying exceptions
        underlying_errors = []
        for exc in exception.exceptions:
            # Recursively handle nested ExceptionGroups
            if hasattr(exc, 'exceptions'):
                underlying_errors.append(_extract_error_message(exc))
            else:
                # Include exception type and message
                exc_type = type(exc).__name__
                exc_msg = str(exc)
                underlying_errors.append(f"{exc_type}: {exc_msg}")

        return " | ".join(underlying_errors)
    else:
        # Regular exception - include type and message
        exc_type = type(exception).__name__
        exc_msg = str(exception)
        return f"{exc_type}: {exc_msg}"


async def _execute_prompt_async(
    request: PromptRequest,
    agents: Optional[dict[str, AgentDefinition]] = None,
) -> ExecutionResult:
    """Execute a single prompt attempt using the Claude Agent SDK.

    Args:
        request: The prompt request configuration
        agents: Optional dict of SDK AgentDefinition instances

    Returns:
        ExecutionResult with output and status
    """
    start_time = time.time()

    # Set up output directory for observability
    output_dir = request.output_dir or Path.cwd() / "agents" / generate_workflow_id()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Map model names to SDK format
    model_map = {
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-20250514",
        "haiku": "claude-haiku-3-5-20241022",
    }
    model = model_map.get(request.model, request.model)

    # Configure security hooks if enabled
    hooks = None
    if request.enable_security_hooks:
        # Create a wrapper that injects workflow_type into context
        async def security_hook_wrapper(
            tool_input: dict[str, Any],
            tool_use_id: str | None = None,
            hook_context: Any = None,
        ) -> dict[str, Any]:
            # Inject workflow type into context for the security hook
            context = {"workflow_type": request.workflow_type}
            return await bash_security_hook(tool_input, tool_use_id, context)

        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[security_hook_wrapper])
            ]
        }

    # Build SDK options
    options = ClaudeAgentOptions(
        model=model,
        cwd=str(request.working_dir) if request.working_dir else None,
        max_turns=100,
        permission_mode="acceptEdits" if request.dangerously_skip_permissions else None,
        hooks=hooks,
        agents=agents,  # Subagent definitions for Task tool delegation
        mcp_servers=request.mcp_servers,  # Agent SDK MCP servers (like mailbox tools)
        allowed_tools=request.allowed_tools,  # Allowed tool names
    )

    messages: list[dict[str, Any]] = []
    text_blocks: list[str] = []
    result_message: Optional[dict[str, Any]] = None
    session_id: Optional[str] = None
    cost_usd: Optional[float] = None

    try:
        # Use async generator prompt when MCP servers present (SDK bug workaround)
        # See: https://github.com/anthropics/claude-agent-sdk-python/issues/386
        if request.mcp_servers and isinstance(request.prompt, str):
            prompt_input = _string_to_async_generator(request.prompt)
        else:
            prompt_input = request.prompt

        async for message in query(prompt=prompt_input, options=options):
            # Serialize message for observability
            msg_dict = _serialize_message(message)
            messages.append(msg_dict)

            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        text_blocks.append(block.text)

            elif isinstance(message, ResultMessage):
                result_message = msg_dict
                session_id = getattr(message, "session_id", None)
                cost_usd = getattr(message, "total_cost_usd", None)

        # Save outputs for observability
        _save_outputs(output_dir, messages, result_message)

        duration_ms = int((time.time() - start_time) * 1000)

        # Build output from collected text blocks
        output = "\n".join(text_blocks) if text_blocks else "No response received"

        # Check for errors in result message
        is_error = result_message.get("is_error", False) if result_message else False
        subtype = result_message.get("subtype", "") if result_message else ""

        if subtype == "error_during_execution":
            return ExecutionResult(
                output="Error during execution",
                success=False,
                session_id=session_id,
                retry_code=RetryCode.ERROR_DURING_EXECUTION,
                duration_ms=duration_ms,
            )

        return ExecutionResult(
            output=output,
            success=not is_error,
            session_id=session_id,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
        )

    except CLINotFoundError:
        return ExecutionResult(
            output="Claude Code CLI not found. Please install with: npm install -g @anthropic-ai/claude-code",
            success=False,
            retry_code=RetryCode.NONE,
        )

    except ProcessError as e:
        return ExecutionResult(
            output=f"Claude Code error: exit code {e.exit_code}",
            success=False,
            retry_code=RetryCode.CLAUDE_CODE_ERROR,
        )

    except ClaudeSDKError as e:
        return ExecutionResult(
            output=f"SDK error: {e}",
            success=False,
            retry_code=RetryCode.EXECUTION_ERROR,
        )

    except TimeoutError:
        return ExecutionResult(
            output="Command timed out",
            success=False,
            retry_code=RetryCode.TIMEOUT_ERROR,
        )

    except Exception as e:
        # Extract actual errors from ExceptionGroups (Python 3.11+)
        error_message = _extract_error_message(e)
        return ExecutionResult(
            output=f"Execution error: {error_message}",
            success=False,
            retry_code=RetryCode.EXECUTION_ERROR,
        )


def _serialize_message(message: Any) -> dict[str, Any]:
    """Serialize a SDK message to a dictionary for observability."""
    msg_dict: dict[str, Any] = {"type": type(message).__name__}

    if isinstance(message, AssistantMessage):
        msg_dict["content"] = []
        for block in message.content:
            if isinstance(block, TextBlock):
                msg_dict["content"].append({"type": "text", "text": block.text})
            else:
                msg_dict["content"].append({"type": type(block).__name__})

    elif isinstance(message, ResultMessage):
        msg_dict["type"] = "result"
        msg_dict["session_id"] = getattr(message, "session_id", None)
        msg_dict["total_cost_usd"] = getattr(message, "total_cost_usd", None)
        msg_dict["is_error"] = getattr(message, "is_error", False)
        msg_dict["subtype"] = getattr(message, "subtype", "")
        msg_dict["result"] = getattr(message, "result", "")

    return msg_dict


def _save_outputs(
    output_dir: Path,
    messages: list[dict[str, Any]],
    result_message: Optional[dict[str, Any]],
) -> None:
    """Save execution outputs for observability."""
    # Save JSONL format
    jsonl_file = output_dir / OUTPUT_JSONL
    with open(jsonl_file, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    # Save JSON array format
    json_file = output_dir / OUTPUT_JSON
    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)

    # Save final result if available
    if result_message:
        final_file = output_dir / FINAL_OBJECT_JSON
        with open(final_file, "w") as f:
            json.dump(result_message, f, indent=2)


async def execute_prompt_async(
    request: PromptRequest,
    max_retries: int = 3,
    agents: Optional[dict[str, AgentDefinition]] = None,
) -> ExecutionResult:
    """Execute a prompt with Claude Code SDK with retry logic.

    This is the async version of execute_prompt() that uses the SDK
    instead of subprocess calls.

    Args:
        request: The prompt request configuration
        max_retries: Maximum retry attempts (default: 3)
        agents: Optional dict of SDK AgentDefinition instances

    Returns:
        ExecutionResult with output and status
    """
    retry_delays = [1, 3, 5]
    last_result = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
            await anyio.sleep(delay)

        result = await _execute_prompt_async(request, agents=agents)
        last_result = result

        if result.success or result.retry_code == RetryCode.NONE:
            return result

        if attempt >= max_retries:
            return result

    return last_result or ExecutionResult(
        output="Execution failed",
        success=False,
        retry_code=RetryCode.EXECUTION_ERROR,
    )


async def execute_template_async(request: TemplateRequest) -> ExecutionResult:
    """Execute a slash command template using the SDK.

    This is the async version of execute_template() that uses the SDK.

    Args:
        request: The template request configuration

    Returns:
        ExecutionResult with output and status
    """
    # Build prompt from slash command and args
    prompt = f"{request.slash_command} {' '.join(request.args)}"

    prompt_request = PromptRequest(
        prompt=prompt,
        model=request.model,
        working_dir=request.working_dir,
        output_dir=request.output_dir,
        dangerously_skip_permissions=True,
    )

    return await execute_prompt_async(prompt_request)


def execute_prompt_sdk(
    request: PromptRequest,
    max_retries: int = 3,
    agents: Optional[dict[str, AgentDefinition]] = None,
) -> ExecutionResult:
    """Execute a prompt with Claude Code SDK (sync wrapper).

    This is a synchronous wrapper around the async SDK execution,
    suitable for use from synchronous CLI commands.

    Args:
        request: The prompt request configuration
        max_retries: Maximum retry attempts (default: 3)
        agents: Optional dict of SDK AgentDefinition instances

    Returns:
        ExecutionResult with output and status
    """

    async def _run() -> ExecutionResult:
        return await execute_prompt_async(request, max_retries, agents)

    return anyio.from_thread.run_sync(lambda: anyio.run(_run))


def execute_template_sdk(request: TemplateRequest) -> ExecutionResult:
    """Execute a slash command template using the SDK (sync wrapper).

    This is a synchronous wrapper around the async SDK execution.

    Args:
        request: The template request configuration

    Returns:
        ExecutionResult with output and status
    """
    return anyio.from_thread.run_sync(
        lambda: anyio.run(execute_template_async, request)
    )


async def execute_prompt_streaming(
    request: PromptRequest,
    agents: Optional[dict[str, AgentDefinition]] = None,
) -> AsyncIterator[Message]:
    """Execute a prompt and stream messages as they arrive.

    This function yields messages in real-time instead of collecting them
    and returning at the end. Perfect for implementing live progress displays.

    Args:
        request: The prompt request configuration
        agents: Optional dict of SDK AgentDefinition instances

    Yields:
        Message objects (AssistantMessage, ToolResultMessage, ResultMessage, etc.)

    Example:
        async for message in execute_prompt_streaming(request):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text, end="", flush=True)
    """
    import os

    # Ensure Claude CLI can be found in PATH
    # Add common installation locations to PATH
    claude_paths = [
        os.path.expanduser("~/.claude/local"),
        "/usr/local/bin",
        "/opt/homebrew/bin",
    ]
    current_path = os.environ.get("PATH", "")
    paths_to_add = [p for p in claude_paths if p not in current_path]
    if paths_to_add:
        os.environ["PATH"] = ":".join(paths_to_add) + ":" + current_path

    # Map model names to SDK format
    model_map = {
        "sonnet": "claude-sonnet-4-20250514",
        "opus": "claude-opus-4-20250514",
        "haiku": "claude-haiku-3-5-20241022",
    }
    model = model_map.get(request.model, request.model)

    # Configure security hooks if enabled
    hooks = None
    if request.enable_security_hooks:
        # Create a wrapper that injects workflow_type into context
        async def security_hook_wrapper(
            tool_input: dict[str, Any],
            tool_use_id: str | None = None,
            hook_context: Any = None,
        ) -> dict[str, Any]:
            # Inject workflow type into context for the security hook
            context = {"workflow_type": request.workflow_type}
            return await bash_security_hook(tool_input, tool_use_id, context)

        hooks = {
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[security_hook_wrapper])
            ]
        }

    # Build SDK options
    options = ClaudeAgentOptions(
        model=model,
        cwd=str(request.working_dir) if request.working_dir else None,
        max_turns=100,
        permission_mode="acceptEdits" if request.dangerously_skip_permissions else None,
        hooks=hooks,
        agents=agents,  # Subagent definitions for Task tool delegation
        mcp_servers=request.mcp_servers,  # Agent SDK MCP servers (like mailbox tools)
        allowed_tools=request.allowed_tools,  # Allowed tool names
    )

    # Use async generator prompt when MCP servers present (SDK bug workaround)
    # See: https://github.com/anthropics/claude-agent-sdk-python/issues/386
    if request.mcp_servers and isinstance(request.prompt, str):
        prompt_input = _string_to_async_generator(request.prompt)
    else:
        prompt_input = request.prompt

    # Stream messages directly to caller
    async for message in query(prompt=prompt_input, options=options):
        yield message
