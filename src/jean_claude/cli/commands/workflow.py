# ABOUTME: CLI command for two-agent workflow orchestration
# ABOUTME: Runs initializer (Opus) to plan features, then coder (Sonnet) to implement them

"""Workflow command for two-agent orchestration."""

from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console

from jean_claude.orchestration.two_agent import run_two_agent_workflow


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
    "--initializer-model",
    "-i",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="opus",
    help="Model for initializer agent (default: opus)",
)
@click.option(
    "--coder-model",
    "-c",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="sonnet",
    help="Model for coder agent (default: sonnet)",
)
@click.option(
    "--max-iterations",
    "-n",
    type=int,
    default=None,
    help="Maximum iterations for coder (default: features * 3)",
)
@click.option(
    "--auto-confirm",
    "-y",
    is_flag=True,
    help="Skip confirmation prompt and proceed automatically",
)
@click.option(
    "--working-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Working directory (default: current directory)",
)
def workflow(
    description: Optional[str],
    spec_file: Optional[Path],
    workflow_id: Optional[str],
    initializer_model: str,
    coder_model: str,
    max_iterations: Optional[int],
    auto_confirm: bool,
    working_dir: Optional[Path],
) -> None:
    """Run two-agent workflow (initializer + coder).

    This command implements the two-agent pattern from Anthropic's
    autonomous coding quickstart:

    \b
    1. Initializer Agent (Opus by default):
       - Analyzes the task description or spec file
       - Creates comprehensive feature breakdown
       - Defines all test files upfront

    \b
    2. Coder Agent (Sonnet by default):
       - Implements features one at a time
       - Runs verification tests before each feature
       - Updates state after completion
       - Continues until all features complete

    The workflow uses file-based state persistence in agents/{workflow_id}/state.json
    to coordinate between agents and survive context resets.

    You must provide either DESCRIPTION or --spec-file (not both).

    \b
    Examples:
        # Basic usage (Opus plans, Sonnet codes)
        jc workflow "Build a user authentication system with JWT and OAuth2"

    \b
        # From spec file
        jc workflow --spec-file specs/feature-auth.md
        jc workflow -s specs/feature-auth.md

    \b
        # Custom workflow ID
        jc workflow "Add logging middleware" --workflow-id auth-logging

    \b
        # Use Opus for both agents (slower but higher quality)
        jc workflow "Complex feature" -i opus -c opus

    \b
        # Auto-confirm (no prompt)
        jc workflow "Simple task" --auto-confirm

    \b
        # Custom working directory
        jc workflow "Add tests" --working-dir /path/to/project

    \b
    Modular Alternative:
        # Run initializer and coder separately
        jc initialize "Task description" -w my-workflow
        jc implement my-workflow
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
        final_state = anyio.run(
            run_two_agent_workflow,
            task_description,
            project_root,
            workflow_id,
            initializer_model,
            coder_model,
            max_iterations,
            auto_confirm,
        )

        # Success message
        if final_state.is_complete():
            console.print()
            console.print("[bold green]Workflow completed successfully![/bold green]")
            console.print(
                f"[dim]State saved to: agents/{final_state.workflow_id}/state.json[/dim]"
            )
        elif final_state.is_failed():
            console.print()
            console.print("[bold red]Workflow failed[/bold red]")
            console.print(f"[dim]Check state: agents/{final_state.workflow_id}/state.json[/dim]")
            raise SystemExit(1)
        else:
            console.print()
            console.print("[bold yellow]Workflow incomplete[/bold yellow]")
            console.print(
                f"[dim]Resume with: jc implement {final_state.workflow_id}[/dim]"
            )

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Workflow cancelled by user[/yellow]")
        raise SystemExit(130)  # Standard exit code for SIGINT

    except Exception as e:
        console.print()
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)
