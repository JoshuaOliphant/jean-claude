# ABOUTME: Agent execution module for running Claude Code prompts programmatically
# ABOUTME: Provides SDK-based and subprocess execution with retry logic, JSONL parsing, and observability

"""Agent execution module for Claude Code.

This module provides the core execution functionality for running Claude Code
prompts and templates. It supports two execution backends:

1. **SDK Backend** (default): Uses the official Claude Code SDK for native Python
   async execution with proper streaming and error handling.

2. **Subprocess Backend** (fallback): Uses subprocess calls to the Claude CLI
   for environments where the SDK is not available.

The SDK backend is preferred as it provides better performance, proper async
support, and cleaner error handling.
"""

import json
import os
import subprocess
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import anyio
from pydantic import BaseModel


class RetryCode(str, Enum):
    """Codes indicating different types of errors that may be retryable."""

    CLAUDE_CODE_ERROR = "claude_code_error"
    TIMEOUT_ERROR = "timeout_error"
    EXECUTION_ERROR = "execution_error"
    ERROR_DURING_EXECUTION = "error_during_execution"
    NONE = "none"


class ExecutionResult(BaseModel):
    """Result from agent execution."""

    output: str
    success: bool
    session_id: Optional[str] = None
    retry_code: RetryCode = RetryCode.NONE
    cost_usd: Optional[float] = None
    duration_ms: Optional[int] = None


class PromptRequest(BaseModel):
    """Request configuration for executing a prompt."""

    prompt: str
    model: Literal["sonnet", "opus", "haiku"] = "sonnet"
    working_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    dangerously_skip_permissions: bool = False
    workflow_type: Literal["readonly", "development", "testing"] = "development"
    enable_security_hooks: bool = True


class TemplateRequest(BaseModel):
    """Request for executing a slash command template."""

    slash_command: str
    args: List[str]
    model: Literal["sonnet", "opus", "haiku"] = "sonnet"
    working_dir: Optional[Path] = None
    output_dir: Optional[Path] = None


# Output file name constants
OUTPUT_JSONL = "cc_raw_output.jsonl"
OUTPUT_JSON = "cc_raw_output.json"
FINAL_OBJECT_JSON = "cc_final_object.json"


def generate_workflow_id() -> str:
    """Generate a short 8-character UUID for workflow tracking."""
    return str(uuid.uuid4())[:8]


def find_claude_cli() -> str:
    """Find Claude Code CLI path.

    Search order:
    1. CLAUDE_CODE_PATH environment variable
    2. `which claude` command
    3. Common installation locations
    4. Fall back to "claude"
    """
    # Check environment variable first
    env_path = os.getenv("CLAUDE_CODE_PATH")
    if env_path:
        return env_path

    # Try `which claude`
    try:
        result = subprocess.run(
            ["which", "claude"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass

    # Check common locations
    common_locations = [
        os.path.expanduser("~/.claude/local/claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
        "/usr/bin/claude",
    ]

    for location in common_locations:
        if os.path.isfile(location) and os.access(location, os.X_OK):
            return location

    return "claude"


def get_subprocess_env() -> Dict[str, str]:
    """Get filtered environment variables safe for subprocess execution."""
    safe_vars = {
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "CLAUDE_CODE_PATH": os.getenv("CLAUDE_CODE_PATH", "claude"),
        "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR": os.getenv(
            "CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR", "true"
        ),
        "HOME": os.getenv("HOME"),
        "USER": os.getenv("USER"),
        "PATH": os.getenv("PATH"),
        "SHELL": os.getenv("SHELL"),
        "TERM": os.getenv("TERM"),
        "LANG": os.getenv("LANG"),
        "LC_ALL": os.getenv("LC_ALL"),
        "PYTHONPATH": os.getenv("PYTHONPATH"),
        "PYTHONUNBUFFERED": "1",
        "PWD": os.getcwd(),
    }
    return {k: v for k, v in safe_vars.items() if v is not None}


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed.

    Returns:
        Error message if not installed, None if OK
    """
    claude_path = find_claude_cli()
    try:
        result = subprocess.run(
            [claude_path, "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return f"Claude Code CLI error at: {claude_path}"
    except FileNotFoundError:
        return f"Claude Code CLI not found. Expected at: {claude_path}"
    return None


def parse_jsonl_output(
    output_file: Path,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Parse JSONL output file.

    Returns:
        Tuple of (all_messages, result_message)
    """
    try:
        with open(output_file) as f:
            messages = [json.loads(line) for line in f if line.strip()]

        result_message = None
        for msg in reversed(messages):
            if msg.get("type") == "result":
                result_message = msg
                break

        return messages, result_message
    except Exception:
        return [], None


def convert_jsonl_to_json(jsonl_file: Path) -> Path:
    """Convert JSONL file to JSON array file."""
    json_file = jsonl_file.parent / OUTPUT_JSON
    messages, _ = parse_jsonl_output(jsonl_file)

    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)

    return json_file


def save_final_result(json_file: Path) -> Optional[Path]:
    """Save the last entry from JSON array as final result."""
    try:
        with open(json_file) as f:
            messages = json.load(f)

        if not messages:
            return None

        final_file = json_file.parent / FINAL_OBJECT_JSON
        with open(final_file, "w") as f:
            json.dump(messages[-1], f, indent=2)

        return final_file
    except Exception:
        return None


def truncate_output(
    output: str,
    max_length: int = 500,
    suffix: str = "... (truncated)",
) -> str:
    """Truncate output to reasonable length for display."""
    if len(output) <= max_length:
        return output

    # Try to find good break point
    truncate_at = max_length - len(suffix)

    newline_pos = output.rfind("\n", truncate_at - 50, truncate_at)
    if newline_pos > 0:
        return output[:newline_pos] + suffix

    space_pos = output.rfind(" ", truncate_at - 20, truncate_at)
    if space_pos > 0:
        return output[:space_pos] + suffix

    return output[:truncate_at] + suffix


def _is_sdk_available() -> bool:
    """Check if the Claude Agent SDK is available."""
    try:
        from claude_agent_sdk import query  # noqa: F401
        return True
    except ImportError:
        return False


def _ensure_claude_in_path() -> None:
    """Ensure common Claude CLI locations are in PATH.

    The SDK relies on PATH to find the Claude CLI, so we add common
    installation locations to ensure it can be found.
    """
    claude_paths = [
        os.path.expanduser("~/.claude/local"),
        "/usr/local/bin",
        "/opt/homebrew/bin",
    ]
    current_path = os.environ.get("PATH", "")
    paths_to_add = [p for p in claude_paths if p not in current_path]
    if paths_to_add:
        os.environ["PATH"] = ":".join(paths_to_add) + ":" + current_path


async def _execute_prompt_sdk_async(
    request: PromptRequest,
    max_retries: int = 3,
) -> ExecutionResult:
    """Execute a prompt using the Claude Code SDK with retry logic (async).

    Args:
        request: The prompt request configuration
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        ExecutionResult with output and status
    """
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        query,
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ClaudeSDKError,
        CLINotFoundError,
        ProcessError,
    )

    # Ensure Claude CLI can be found
    _ensure_claude_in_path()

    retry_delays = [1, 3, 5]
    last_result = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
            await anyio.sleep(delay)

        # Execute single attempt
        start_time = time.time()
        output_dir = request.output_dir or Path.cwd() / "agents" / generate_workflow_id()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Pass model name directly - SDK handles short names (sonnet, opus, haiku)
        options = ClaudeAgentOptions(
            model=request.model,
            cwd=str(request.working_dir) if request.working_dir else None,
            max_turns=100,
            permission_mode="acceptEdits" if request.dangerously_skip_permissions else None,
        )

        messages: List[Dict[str, Any]] = []
        text_blocks: List[str] = []
        result_message: Optional[Dict[str, Any]] = None
        session_id: Optional[str] = None
        cost_usd: Optional[float] = None

        try:
            async for message in query(prompt=request.prompt, options=options):
                msg_dict = _serialize_sdk_message(message)
                messages.append(msg_dict)

                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            text_blocks.append(block.text)

                elif isinstance(message, ResultMessage):
                    result_message = msg_dict
                    session_id = message.session_id
                    cost_usd = message.total_cost_usd

            _save_sdk_outputs(output_dir, messages, result_message)
            duration_ms = int((time.time() - start_time) * 1000)
            output = "\n".join(text_blocks) if text_blocks else "No response received"

            is_error = result_message.get("is_error", False) if result_message else False
            subtype = result_message.get("subtype", "") if result_message else ""

            if subtype == "error_during_execution":
                result = ExecutionResult(
                    output="Error during execution",
                    success=False,
                    session_id=session_id,
                    retry_code=RetryCode.ERROR_DURING_EXECUTION,
                    duration_ms=duration_ms,
                )
            else:
                result = ExecutionResult(
                    output=output,
                    success=not is_error,
                    session_id=session_id,
                    cost_usd=cost_usd,
                    duration_ms=duration_ms,
                )

        except CLINotFoundError:
            result = ExecutionResult(
                output="Claude Code CLI not found. Please install with: npm install -g @anthropic-ai/claude-code",
                success=False,
                retry_code=RetryCode.NONE,
            )

        except ProcessError as e:
            result = ExecutionResult(
                output=f"Claude Code error: exit code {e.exit_code}",
                success=False,
                retry_code=RetryCode.CLAUDE_CODE_ERROR,
            )

        except ClaudeSDKError as e:
            result = ExecutionResult(
                output=f"SDK error: {e}",
                success=False,
                retry_code=RetryCode.EXECUTION_ERROR,
            )

        except TimeoutError:
            result = ExecutionResult(
                output="Command timed out",
                success=False,
                retry_code=RetryCode.TIMEOUT_ERROR,
            )

        except Exception as e:
            result = ExecutionResult(
                output=f"Execution error: {e}",
                success=False,
                retry_code=RetryCode.EXECUTION_ERROR,
            )

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


def _serialize_sdk_message(message: Any) -> Dict[str, Any]:
    """Serialize an SDK message to a dictionary for observability.

    Note: This function uses lazy imports to avoid circular dependencies
    and to only load SDK types when actually needed.
    """
    from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock

    msg_dict: Dict[str, Any] = {"type": type(message).__name__}

    if isinstance(message, AssistantMessage):
        msg_dict["content"] = []
        for block in message.content:
            if isinstance(block, TextBlock):
                msg_dict["content"].append({"type": "text", "text": block.text})
            else:
                msg_dict["content"].append({"type": type(block).__name__})

    elif isinstance(message, ResultMessage):
        msg_dict["type"] = "result"
        msg_dict["session_id"] = message.session_id
        msg_dict["total_cost_usd"] = message.total_cost_usd
        msg_dict["is_error"] = message.is_error
        msg_dict["subtype"] = message.subtype
        msg_dict["result"] = message.result
        msg_dict["duration_ms"] = message.duration_ms

    return msg_dict


def _save_sdk_outputs(
    output_dir: Path,
    messages: List[Dict[str, Any]],
    result_message: Optional[Dict[str, Any]],
) -> None:
    """Save SDK execution outputs for observability."""
    jsonl_file = output_dir / OUTPUT_JSONL
    with open(jsonl_file, "w") as f:
        for msg in messages:
            f.write(json.dumps(msg) + "\n")

    json_file = output_dir / OUTPUT_JSON
    with open(json_file, "w") as f:
        json.dump(messages, f, indent=2)

    if result_message:
        final_file = output_dir / FINAL_OBJECT_JSON
        with open(final_file, "w") as f:
            json.dump(result_message, f, indent=2)


def execute_prompt(
    request: PromptRequest,
    max_retries: int = 3,
    use_sdk: Optional[bool] = None,
) -> ExecutionResult:
    """Execute a prompt with Claude Code with retry logic.

    This function supports two execution backends:
    1. SDK Backend (default when available): Uses the official Claude Code SDK
    2. Subprocess Backend (fallback): Uses subprocess calls to the CLI

    Args:
        request: The prompt request configuration
        max_retries: Maximum retry attempts (default: 3)
        use_sdk: Force SDK (True) or subprocess (False) backend.
                 If None, automatically uses SDK if available.

    Returns:
        ExecutionResult with output and status
    """
    # Determine which backend to use
    if use_sdk is None:
        use_sdk = _is_sdk_available()

    if use_sdk:
        # Use SDK backend - run async code from sync CLI context
        async def _run() -> ExecutionResult:
            return await _execute_prompt_sdk_async(request, max_retries)

        return anyio.run(_run)

    # Fall back to subprocess backend
    return _execute_prompt_subprocess(request, max_retries)


def _execute_prompt_subprocess(
    request: PromptRequest,
    max_retries: int = 3,
) -> ExecutionResult:
    """Execute a prompt using subprocess (fallback backend).

    Args:
        request: The prompt request configuration
        max_retries: Maximum retry attempts (default: 3)

    Returns:
        ExecutionResult with output and status
    """
    retry_delays = [1, 3, 5]
    last_result = None

    for attempt in range(max_retries + 1):
        if attempt > 0:
            delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
            time.sleep(delay)

        result = _execute_prompt_once(request)
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


def _execute_prompt_once(request: PromptRequest) -> ExecutionResult:
    """Execute a single prompt attempt."""
    # Check Claude installation
    error_msg = check_claude_installed()
    if error_msg:
        return ExecutionResult(
            output=error_msg,
            success=False,
            retry_code=RetryCode.NONE,
        )

    claude_path = find_claude_cli()

    # Set up output directory
    output_dir = request.output_dir or Path.cwd() / "agents" / generate_workflow_id()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / OUTPUT_JSONL

    # Build command
    cmd = [
        claude_path,
        "-p",
        request.prompt,
        "--model",
        request.model,
        "--output-format",
        "stream-json",
        "--verbose",
    ]

    # Check for MCP config
    if request.working_dir:
        mcp_config = request.working_dir / ".mcp.json"
        if mcp_config.exists():
            cmd.extend(["--mcp-config", str(mcp_config)])

    if request.dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    env = get_subprocess_env()
    working_dir = str(request.working_dir) if request.working_dir else None

    try:
        with open(output_file, "w") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=working_dir,
            )

        if result.returncode == 0:
            messages, result_msg = parse_jsonl_output(output_file)
            convert_jsonl_to_json(output_file)
            save_final_result(output_file.parent / OUTPUT_JSON)

            if result_msg:
                session_id = result_msg.get("session_id")
                is_error = result_msg.get("is_error", False)
                subtype = result_msg.get("subtype", "")

                if subtype == "error_during_execution":
                    return ExecutionResult(
                        output="Error during execution",
                        success=False,
                        session_id=session_id,
                        retry_code=RetryCode.ERROR_DURING_EXECUTION,
                    )

                result_text = result_msg.get("result", "")
                if is_error and len(result_text) > 1000:
                    result_text = truncate_output(result_text, max_length=800)

                return ExecutionResult(
                    output=result_text,
                    success=not is_error,
                    session_id=session_id,
                    cost_usd=result_msg.get("total_cost_usd"),
                    duration_ms=result_msg.get("duration_ms"),
                )
            else:
                return ExecutionResult(
                    output="No result message in output",
                    success=False,
                    retry_code=RetryCode.NONE,
                )
        else:
            stderr_msg = result.stderr.strip() if result.stderr else ""
            return ExecutionResult(
                output=f"Claude Code error: {stderr_msg or f'exit code {result.returncode}'}",
                success=False,
                retry_code=RetryCode.CLAUDE_CODE_ERROR,
            )

    except subprocess.TimeoutExpired:
        return ExecutionResult(
            output="Command timed out",
            success=False,
            retry_code=RetryCode.TIMEOUT_ERROR,
        )
    except Exception as e:
        return ExecutionResult(
            output=f"Execution error: {e}",
            success=False,
            retry_code=RetryCode.EXECUTION_ERROR,
        )


def execute_template(
    request: TemplateRequest,
    use_sdk: Optional[bool] = None,
) -> ExecutionResult:
    """Execute a slash command template.

    This function supports two execution backends:
    1. SDK Backend (default when available): Uses the official Claude Code SDK
    2. Subprocess Backend (fallback): Uses subprocess calls to the CLI

    Example:
        request = TemplateRequest(
            slash_command="/implement",
            args=["plan.md"],
            model="sonnet"
        )
        result = execute_template(request)

    Args:
        request: The template request configuration
        use_sdk: Force SDK (True) or subprocess (False) backend.
                 If None, automatically uses SDK if available.

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

    return execute_prompt(prompt_request, use_sdk=use_sdk)
