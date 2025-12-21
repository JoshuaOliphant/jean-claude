# ABOUTME: Agent execution module for running Claude Code prompts programmatically
# ABOUTME: Provides subprocess-based execution with retry logic, JSONL parsing, and observability

"""Agent execution module for Claude Code."""

import json
import os
import re
import subprocess
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

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


def execute_prompt(
    request: PromptRequest,
    max_retries: int = 3,
) -> ExecutionResult:
    """Execute a prompt with Claude Code with retry logic.

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


def execute_template(request: TemplateRequest) -> ExecutionResult:
    """Execute a slash command template.

    Example:
        request = TemplateRequest(
            slash_command="/implement",
            args=["plan.md"],
            model="sonnet"
        )
        result = execute_template(request)
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

    return execute_prompt(prompt_request)
