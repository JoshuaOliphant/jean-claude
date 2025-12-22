# ABOUTME: CLI command for running the coder agent on existing workflow state
# ABOUTME: Implements features from WorkflowState using auto-continue loop

"""Implement command for executing features from workflow state."""

from pathlib import Path
from typing import Optional

import anyio
import click
from rich.console import Console
from rich.panel import Panel

from jean_claude.core.state import WorkflowState
from jean_claude.orchestration import run_auto_continue, AutoContinueError


console = Console()


@click.command()
@click.argument("workflow_id", required=False)
@click.option(
    "--state-file",
    "-s",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to state.json file (alternative to workflow ID)",
)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="sonnet",
    help="Model for coder agent (default: sonnet)",
)
@click.option(
    "--max-iterations",
    "-n",
    type=int,
    default=None,
    help="Maximum iterations (default: from state or features * 3)",
)
@click.option(
    "--delay",
    type=float,
    default=2.0,
    help="Delay between iterations in seconds (default: 2.0)",
)
@click.option(
    "--skip-verify",
    is_flag=True,
    help="Skip verification tests before each iteration",
)
@click.option(
    "--working-dir",
    "-d",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Working directory (default: current directory)",
)
def implement(
    workflow_id: Optional[str],
    state_file: Optional[Path],
    model: str,
    max_iterations: Optional[int],
    delay: float,
    skip_verify: bool,
    working_dir: Optional[Path],
) -> None:
    """Run coder agent to implement features from workflow state.

    The coder agent reads the WorkflowState (created by `jc initialize`)
    and implements features one at a time using the auto-continue loop.

    You must provide either WORKFLOW_ID or --state-file.

    \b
    Examples:
        # By workflow ID (looks in agents/{id}/state.json)
        jc implement two-agent-abc123

    \b
        # By state file path
        jc implement --state-file agents/my-workflow/state.json
        jc implement -s agents/my-workflow/state.json

    \b
        # Custom model and iterations
        jc implement two-agent-abc123 -m opus -n 100

    \b
        # Skip verification tests (faster but less safe)
        jc implement two-agent-abc123 --skip-verify

    \b
    Verification-First Mode:
        By default, runs tests before each feature to catch regressions.
        Use --skip-verify to disable for faster iteration.
    """
    # Validate input: must have exactly one of workflow_id or state_file
    if workflow_id and state_file:
        console.print("[red]Error: Provide either WORKFLOW_ID or --state-file, not both[/red]")
        raise SystemExit(1)

    if not workflow_id and not state_file:
        console.print("[red]Error: Must provide WORKFLOW_ID or --state-file[/red]")
        console.print("[dim]Use --help for usage examples[/dim]")
        raise SystemExit(1)

    project_root = working_dir or Path.cwd()

    # Load workflow state
    try:
        if state_file:
            console.print(f"[dim]Loading state from: {state_file}[/dim]")
            state = WorkflowState.load_from_file(state_file)
        else:
            console.print(f"[dim]Loading workflow: {workflow_id}[/dim]")
            state = WorkflowState.load(workflow_id, project_root)  # type: ignore
    except FileNotFoundError as e:
        console.print(f"[red]Error: State file not found[/red]")
        console.print(f"[dim]{e}[/dim]")
        console.print()
        console.print("[yellow]Hint: Run `jc initialize` first to create the workflow state[/yellow]")
        raise SystemExit(1)

    # Show current state
    pending = [f for f in state.features if f.status == "pending"]
    completed = [f for f in state.features if f.status == "completed"]
    failed = [f for f in state.features if f.status == "failed"]

    console.print()
    console.print(
        Panel(
            f"[bold blue]Coder Agent[/bold blue]\n\n"
            f"Workflow: [cyan]{state.workflow_id}[/cyan]\n"
            f"Features: [green]{len(completed)} completed[/green], "
            f"[yellow]{len(pending)} pending[/yellow], "
            f"[red]{len(failed)} failed[/red]\n"
            f"Model: [cyan]{model}[/cyan]\n"
            f"Verify: [cyan]{'disabled' if skip_verify else 'enabled'}[/cyan]",
            border_style="blue",
        )
    )
    console.print()

    if state.is_complete():
        console.print("[green]All features already completed![/green]")
        return

    # Run auto-continue loop
    try:
        async def _run():
            return await run_auto_continue(
                state=state,
                project_root=project_root,
                max_iterations=max_iterations,
                delay_seconds=delay,
                model=model,
                verify_first=not skip_verify,
            )

        final_state = anyio.run(_run)

        # Result message
        if final_state.is_complete():
            console.print()
            console.print(
                Panel(
                    "[bold green]All features implemented successfully![/bold green]",
                    border_style="green",
                )
            )
        elif final_state.is_failed():
            console.print()
            console.print(
                Panel(
                    "[bold red]Some features failed[/bold red]\n\n"
                    f"Check state: [cyan]agents/{final_state.workflow_id}/state.json[/cyan]",
                    border_style="red",
                )
            )
            raise SystemExit(1)
        else:
            console.print()
            console.print(
                Panel(
                    "[bold yellow]Implementation incomplete[/bold yellow]\n\n"
                    f"Resume with: [cyan]jc implement {final_state.workflow_id}[/cyan]",
                    border_style="yellow",
                )
            )

    except AutoContinueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Cancelled by user[/yellow]")
        console.print(f"[dim]Resume with: jc implement {state.workflow_id}[/dim]")
        raise SystemExit(130)
