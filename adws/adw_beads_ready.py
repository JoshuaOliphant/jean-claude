#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "python-dotenv",
#   "click",
#   "rich",
# ]
# ///
# ABOUTME: Interactive Beads task picker that displays ready tasks and lets user select one to work on.
# ABOUTME: Integrates with Beads issue tracker to show tasks with no blockers, ready for implementation.

import os
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

# Add the adw_modules directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "adw_modules"))

from adw_modules.beads_integration import get_ready_beads_tasks, fetch_beads_issue


@click.command()
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of ready tasks to display (default: 10)",
)
@click.option(
    "--auto-select",
    type=int,
    help="Automatically select task by index (1-based)",
)
def main(limit: int, auto_select: int):
    """
    Display ready Beads tasks and let user select one to work on.

    Shows all tasks with no blockers that are ready for implementation.

    Examples:

        # Interactive mode - shows tasks and prompts for selection
        ./adws/adw_beads_ready.py

        # Show more tasks
        ./adws/adw_beads_ready.py --limit 20

        # Auto-select first task (useful for automation)
        ./adws/adw_beads_ready.py --auto-select 1
    """
    console = Console()

    console.print(
        Panel(
            "[bold blue]Beads Ready Tasks[/bold blue]\n\n"
            "[dim]Showing tasks with no blockers, ready to implement[/dim]",
            title="[bold blue]Task Picker[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Fetch ready tasks
    with console.status("[bold yellow]Fetching ready tasks...[/bold yellow]"):
        tasks, error = get_ready_beads_tasks(limit=limit)

    if error:
        console.print(
            Panel(
                f"[bold red]{error}[/bold red]",
                title="[bold red]Error[/bold red]",
                border_style="red",
            )
        )
        sys.exit(1)

    if not tasks:
        console.print(
            Panel(
                "[yellow]No ready tasks found![/yellow]\n\n"
                "[dim]All tasks may have blockers or be already in progress.[/dim]",
                title="[bold yellow]No Tasks[/bold yellow]",
                border_style="yellow",
            )
        )
        sys.exit(0)

    # Display tasks in a table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Task ID", style="bold")
    table.add_column("Title", style="")

    # Fetch details for each task
    task_details = []
    for idx, task_id in enumerate(tasks, 1):
        issue, error = fetch_beads_issue(task_id)
        if issue:
            table.add_row(str(idx), task_id, issue.title)
            task_details.append((task_id, issue))
        else:
            table.add_row(str(idx), task_id, f"[red]Error: {error}[/red]")

    console.print(table)
    console.print()

    # Handle auto-select
    if auto_select is not None:
        if auto_select < 1 or auto_select > len(tasks):
            console.print(
                f"[red]Invalid auto-select index: {auto_select}. Must be between 1 and {len(tasks)}[/red]"
            )
            sys.exit(1)

        selected_idx = auto_select - 1
        selected_task_id, selected_issue = task_details[selected_idx]

        console.print(f"[green]Auto-selected task {auto_select}: {selected_task_id}[/green]")
    else:
        # Interactive selection
        while True:
            selection = Prompt.ask(
                "[cyan]Select a task to work on[/cyan]",
                choices=[str(i) for i in range(1, len(tasks) + 1)] + ["q"],
                default="1",
            )

            if selection.lower() == "q":
                console.print("[dim]Cancelled.[/dim]")
                sys.exit(0)

            try:
                selected_idx = int(selection) - 1
                selected_task_id, selected_issue = task_details[selected_idx]
                break
            except (ValueError, IndexError):
                console.print(f"[red]Invalid selection: {selection}[/red]")
                continue

    # Display selected task details
    console.print()
    console.print(
        Panel(
            f"[bold]Task ID:[/bold] {selected_task_id}\n"
            f"[bold]Title:[/bold] {selected_issue.title}\n\n"
            f"[bold]Description:[/bold]\n{selected_issue.body or '[dim]No description[/dim]'}",
            title=f"[bold green]Selected Task: {selected_task_id}[/bold green]",
            border_style="green",
        )
    )
    console.print()

    # Show next steps
    console.print("[bold]Next Steps:[/bold]")
    console.print()
    console.print(f"1. Start working on this task:")
    console.print(f"   [dim]# Use an ADW workflow to plan and implement[/dim]")
    console.print(f"   [cyan]./adws/adw_sdlc_iso.py {selected_task_id}[/cyan]")
    console.print()
    console.print(f"2. Or plan it first:")
    console.print(f"   [cyan]./adws/adw_plan_iso.py {selected_task_id}[/cyan]")
    console.print()
    console.print(f"3. Update task status:")
    console.print(f"   [dim]bd update {selected_task_id} --status in_progress[/dim]")
    console.print()

    # Output the task ID for scripting
    console.print(f"[dim]Task ID: {selected_task_id}[/dim]")

    # Exit with success
    sys.exit(0)


if __name__ == "__main__":
    main()
