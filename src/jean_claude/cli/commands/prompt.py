# ABOUTME: Implementation of the 'jc prompt' command
# ABOUTME: Executes adhoc prompts with Claude Code

"""Execute adhoc prompts with Claude."""

from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from jean_claude.core.agent import (
    ExecutionResult,
    PromptRequest,
    RetryCode,
    check_claude_installed,
    execute_prompt,
    generate_workflow_id,
)
from jean_claude.core.sdk_executor import execute_prompt_streaming
from jean_claude.cli.streaming import stream_output

console = Console()


@click.command()
@click.argument("text")
@click.option(
    "--model",
    "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="Claude model to use",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Directory for output files (default: agents/<id>/)",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Output raw text without formatting",
)
@click.option(
    "--stream",
    is_flag=True,
    help="Stream output in real-time as it arrives",
)
@click.option(
    "--show-thinking",
    is_flag=True,
    help="Show tool uses and internal thinking (requires --stream)",
)
def prompt(
    text: str,
    model: str,
    output_dir: Optional[Path],
    raw: bool,
    stream: bool,
    show_thinking: bool,
) -> None:
    """Execute an adhoc prompt with Claude.

    \b
    Examples:
      jc prompt "Explain the authentication flow"
      jc prompt "Add logging to API endpoints" --model opus
      jc prompt "Quick question" -m haiku
    """
    # Check Claude installation first
    error = check_claude_installed()
    if error:
        console.print(
            Panel(
                f"[red]{error}[/red]\n\n"
                "Please install Claude Code CLI:\n"
                "  [cyan]npm install -g @anthropic-ai/claude-code[/cyan]",
                title="[red]Claude Code Not Found[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)

    # Generate workflow ID for tracking
    workflow_id = generate_workflow_id()

    # Set up output directory
    if output_dir is None:
        output_dir = Path.cwd() / "agents" / workflow_id

    # Create request
    request = PromptRequest(
        prompt=text,
        model=model,
        working_dir=Path.cwd(),
        output_dir=output_dir,
    )

    if not raw:
        console.print()
        console.print(f"[dim]Workflow ID: {workflow_id}[/dim]")
        console.print(f"[dim]Model: {model}[/dim]")
        console.print()

    # Execute with streaming or traditional approach
    result: ExecutionResult
    output_text: Optional[str] = None

    if stream:
        # Use streaming execution
        async def run_streaming() -> str:
            message_stream = execute_prompt_streaming(request)
            return await stream_output(message_stream, console, show_thinking)

        try:
            # Run async streaming in sync context
            output_text = anyio.run(run_streaming)

            # Create a minimal result for metadata display
            result = ExecutionResult(
                output=output_text,
                success=True,
                session_id=None,
                duration_ms=None,
                cost_usd=None,
            )
        except Exception as e:
            # Handle streaming errors
            result = ExecutionResult(
                output=f"Streaming error: {e}",
                success=False,
                retry_code=RetryCode.EXECUTION_ERROR,
            )
    elif raw:
        result = execute_prompt(request)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Executing prompt...", total=None)
            result = execute_prompt(request)

    # Display result
    if result.success:
        # For streaming mode, output was already shown in real-time
        if stream:
            console.print()  # Add blank line after streaming
            console.print("[green]✓ Complete[/green]")
            console.print(f"[dim]Output saved to: {output_dir}[/dim]")
        elif raw:
            console.print(result.output)
        else:
            # Try to render as markdown for better formatting
            try:
                console.print(Panel(
                    Markdown(result.output),
                    title="[green]Response[/green]",
                    border_style="green",
                ))
            except Exception:
                # Fall back to plain text
                console.print(Panel(
                    result.output,
                    title="[green]Response[/green]",
                    border_style="green",
                ))

            # Show metadata
            metadata_parts = []
            if result.session_id:
                metadata_parts.append(f"Session: {result.session_id}")
            if result.duration_ms:
                duration_sec = result.duration_ms / 1000
                metadata_parts.append(f"Duration: {duration_sec:.1f}s")
            if result.cost_usd:
                metadata_parts.append(f"Cost: ${result.cost_usd:.4f}")

            if metadata_parts:
                console.print(f"[dim]{' | '.join(metadata_parts)}[/dim]")

            console.print(f"[dim]Output saved to: {output_dir}[/dim]")
    else:
        console.print(
            Panel(
                f"[red]{result.output}[/red]",
                title="[red]Error[/red]",
                border_style="red",
            )
        )
        if result.retry_code.value != "none":
            console.print(f"[dim]Retry code: {result.retry_code.value}[/dim]")
        raise SystemExit(1)
