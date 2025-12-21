# ABOUTME: Implementation of the 'jc prompt' command
# ABOUTME: Executes adhoc prompts with Claude Code

"""Execute adhoc prompts with Claude."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from jean_claude.core.agent import (
    ExecutionResult,
    PromptRequest,
    check_claude_installed,
    execute_prompt,
    generate_workflow_id,
)

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
def prompt(
    text: str,
    model: str,
    output_dir: Optional[Path],
    raw: bool,
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

    # Execute with progress indicator
    result: ExecutionResult

    if raw:
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
        if raw:
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
