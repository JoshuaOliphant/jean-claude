# ABOUTME: Implementation of the 'jc prime' command
# ABOUTME: Gathers project context using the prime subagent for context efficiency

"""Gather project context using the prime subagent."""

from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from jean_claude.core.agent import (
    PromptRequest,
    check_claude_installed,
    generate_workflow_id,
)
from jean_claude.core.sdk_executor import execute_prompt_async
from jean_claude.core.subagents import get_subagents_for_sdk

console = Console()


@click.command()
@click.option(
    "--model",
    "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="Model for the main agent (subagent uses haiku)",
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
def prime(
    model: str,
    output_dir: Optional[Path],
    raw: bool,
) -> None:
    """Gather project context using the prime subagent.

    The prime subagent explores the codebase using Haiku (fast and cheap)
    and returns a condensed summary that stays within your main context.

    \b
    Benefits:
    - Context efficiency: File exploration stays out of your main context
    - Cost reduction: Uses Haiku for exploration (10x cheaper than Sonnet)
    - Focused output: Returns a ~500 word summary, not verbose file listings

    \b
    Examples:
      jc prime                    # Quick project overview
      jc prime --model haiku      # Use Haiku for main agent too
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

    # Get prime subagent definition in SDK format
    agents = get_subagents_for_sdk(["prime"])

    # Create request that instructs main agent to use prime subagent
    request = PromptRequest(
        prompt=(
            "Use the prime agent to explore and understand this codebase. "
            "The prime agent will gather project structure, tech stack, entry points, "
            "and testing information. Once it returns its findings, present the summary "
            "to me without adding additional commentary."
        ),
        model=model,
        working_dir=Path.cwd(),
        output_dir=output_dir,
    )

    if not raw:
        console.print()
        console.print("[bold blue]🔍 Gathering project context...[/bold blue]")
        console.print(f"[dim]Workflow ID: {workflow_id}[/dim]")
        console.print(f"[dim]Main model: {model} | Subagent model: haiku[/dim]")
        console.print()

    # Execute with subagent
    async def run_prime():
        return await execute_prompt_async(request, agents=agents)

    if raw:
        result = anyio.run(run_prime)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Prime subagent exploring codebase...", total=None)
            result = anyio.run(run_prime)

    # Display result
    if result.success:
        if raw:
            console.print(result.output)
        else:
            # Render as markdown for better formatting
            try:
                console.print(
                    Panel(
                        Markdown(result.output),
                        title="[green]Project Context[/green]",
                        border_style="green",
                    )
                )
            except Exception:
                # Fall back to plain text
                console.print(
                    Panel(
                        result.output,
                        title="[green]Project Context[/green]",
                        border_style="green",
                    )
                )

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
        raise SystemExit(1)
