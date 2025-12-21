# ABOUTME: Implementation of the 'jc run' command for executing ADW workflows
# ABOUTME: Orchestrates chore, feature, and bug workflows with slash command templates

"""Execute AI Developer Workflows (chore, feature, bug)."""

from pathlib import Path
from typing import Literal, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from jean_claude.core.agent import (
    ExecutionResult,
    TemplateRequest,
    check_claude_installed,
    execute_template,
    generate_workflow_id,
)

console = Console()


@click.command()
@click.argument("workflow_type", type=click.Choice(["chore", "feature", "bug"]))
@click.argument("description")
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
def run(
    workflow_type: Literal["chore", "feature", "bug"],
    description: str,
    model: str,
    output_dir: Optional[Path],
    raw: bool,
) -> None:
    """Execute an AI Developer Workflow.

    Creates a plan using the specified workflow template (chore, feature, or bug)
    and generates a workflow ID for tracking.

    \b
    WORKFLOW_TYPE must be one of:
      • chore    - Small tasks, refactoring, documentation
      • feature  - New functionality or enhancements
      • bug      - Bug fixes and issue resolution

    \b
    Examples:
      jc run chore "Add error handling to API"
      jc run feature "User authentication" --model opus
      jc run bug "Fix null pointer in checkout" -m haiku
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

    # Build slash command
    slash_command = f"/{workflow_type}"

    # Create template request
    request = TemplateRequest(
        slash_command=slash_command,
        args=[workflow_id, description],
        model=model,
        working_dir=Path.cwd(),
        output_dir=output_dir,
    )

    if not raw:
        console.print()
        console.print(f"[bold blue]Starting {workflow_type.title()} Workflow[/bold blue]")
        console.print()
        console.print(f"[dim]Workflow ID: {workflow_id}[/dim]")
        console.print(f"[dim]Type: {workflow_type}[/dim]")
        console.print(f"[dim]Model: {model}[/dim]")
        console.print(f"[dim]Description: {description}[/dim]")
        console.print()

    # Execute with progress indicator
    result: ExecutionResult

    if raw:
        result = execute_template(request)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Executing {slash_command} workflow...", total=None)
            result = execute_template(request)

    # Display result
    if result.success:
        if raw:
            console.print(result.output)
        else:
            # Try to render as markdown for better formatting
            try:
                console.print(
                    Panel(
                        Markdown(result.output),
                        title=f"[green]{workflow_type.title()} Plan Created[/green]",
                        border_style="green",
                    )
                )
            except Exception:
                # Fall back to plain text
                console.print(
                    Panel(
                        result.output,
                        title=f"[green]{workflow_type.title()} Plan Created[/green]",
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

            console.print()
            console.print(f"[dim]Output saved to: {output_dir}[/dim]")

            # Show next steps
            spec_file = Path.cwd() / "specs" / f"{workflow_type}-{workflow_id}.md"
            console.print()
            console.print(
                Panel(
                    f"[bold green]✓ {workflow_type.title()} workflow initialized[/bold green]\n\n"
                    f"Plan saved to: [cyan]{spec_file}[/cyan]\n\n"
                    "Next steps:\n"
                    f"  • Review the plan in [cyan]{spec_file}[/cyan]\n"
                    f"  • Run [cyan]jc run implement {spec_file}[/cyan] to execute\n"
                    f"  • Or use [cyan]/implement {spec_file}[/cyan] in Claude Code",
                    title="[bold green]Success[/bold green]",
                    border_style="green",
                )
            )
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
