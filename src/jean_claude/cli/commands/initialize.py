# ABOUTME: CLI command for running the initializer agent standalone
# ABOUTME: Creates feature breakdown from description or spec file, outputs WorkflowState

"""Initialize command for feature breakdown."""

from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console
from rich.panel import Panel

from jean_claude.orchestration.two_agent import run_initializer


console = Console()


@click.command()
@click.argument("description", required=False)
@click.option(
    "--spec-file",
    "-s",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Read task description from spec file instead of argument",
)
@click.option(
    "--workflow-id",
    "-w",
    type=str,
    default=None,
    help="Workflow ID (auto-generated if not provided)",
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="opus",
    help="Model for initializer (default: opus)",
)
@click.option(
    "--working-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Working directory (default: current directory)",
)
def initialize(
    description: Optional[str],
    spec_file: Optional[Path],
    workflow_id: Optional[str],
    model: str,
    working_dir: Optional[Path],
) -> None:
    """Run initializer agent to create feature breakdown.

    The initializer analyzes a task description or spec file and creates
    a comprehensive feature breakdown with test files defined upfront.

    You must provide either DESCRIPTION or --spec-file (not both).

    \b
    Examples:
        # From description
        jc initialize "Build user authentication with JWT"

    \b
        # From spec file
        jc initialize --spec-file specs/feature-auth.md
        jc initialize -s specs/feature-auth.md

    \b
        # Custom workflow ID and model
        jc initialize "Add logging" -w my-logging -m sonnet

    \b
    Output:
        Creates agents/{workflow-id}/state.json with feature list.
        Use `jc implement {workflow-id}` to execute the features.
    """
    # Validate input: must have exactly one of description or spec_file
    if description and spec_file:
        console.print("[red]Error: Provide either DESCRIPTION or --spec-file, not both[/red]")
        raise SystemExit(1)

    if not description and not spec_file:
        console.print("[red]Error: Must provide DESCRIPTION or --spec-file[/red]")
        console.print("[dim]Use --help for usage examples[/dim]")
        raise SystemExit(1)

    # Read description from spec file if provided
    task_description: str
    if spec_file:
        console.print(f"[dim]Reading spec file: {spec_file}[/dim]")
        task_description = spec_file.read_text()
    else:
        task_description = description  # type: ignore

    project_root = working_dir or Path.cwd()

    try:
        state = anyio.run(
            run_initializer,
            task_description,
            project_root,
            workflow_id,
            model,
        )

        # Success message
        console.print()
        console.print(
            Panel(
                f"[bold green]Initializer complete![/bold green]\n\n"
                f"Features: [cyan]{len(state.features)}[/cyan]\n"
                f"Workflow ID: [cyan]{state.workflow_id}[/cyan]\n"
                f"State file: [cyan]agents/{state.workflow_id}/state.json[/cyan]\n\n"
                "Next step:\n"
                f"  [cyan]jc implement {state.workflow_id}[/cyan]",
                title="[bold green]Success[/bold green]",
                border_style="green",
            )
        )

    except ValueError as e:
        console.print(f"[bold red]Initializer failed:[/bold red] {e}")
        raise SystemExit(1)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Cancelled by user[/yellow]")
        raise SystemExit(130)
