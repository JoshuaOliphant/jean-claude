#!/usr/bin/env python3
"""Test coordinator polling pattern with sleep intervals."""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.tools.mailbox_tools import poll_ntfy_responses

console = Console()

workflow_id = "mobile-test-001"

console.print(Panel.fit(
    "[bold cyan]Coordinator Polling Pattern Test[/bold cyan]\n\n"
    f"Waiting for La Boeuf to respond to workflow: [yellow]{workflow_id}[/yellow]",
    border_style="cyan"
))
console.print()

console.print("[dim]Expected message format:[/dim]")
console.print(f"  [cyan]{workflow_id}: Your response here[/cyan]")
console.print()

# Poll with sleep intervals (as documented in CLAUDE.md)
max_attempts = 30  # 30 × 10 seconds = 5 minutes
found_response = None

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    console=console,
) as progress:
    task = progress.add_task("Polling for response...", total=max_attempts)

    for attempt in range(max_attempts):
        # Poll ntfy
        responses = poll_ntfy_responses()
        matching = [r for r in responses if r['workflow_id'] == workflow_id]

        if matching:
            found_response = matching[0]
            progress.update(task, completed=max_attempts)
            break

        # Update progress
        elapsed = (attempt + 1) * 10
        progress.update(
            task,
            advance=1,
            description=f"Polling... ({elapsed}s / {max_attempts * 10}s)"
        )

        # Sleep before next poll
        if attempt < max_attempts - 1:
            time.sleep(10)

console.print()

if found_response:
    console.print(Panel(
        f"[bold green]✅ SUCCESS! Response Received[/bold green]\n\n"
        f"[dim]Workflow ID:[/dim] [cyan]{found_response['workflow_id']}[/cyan]\n"
        f"[dim]Response:[/dim] [yellow]{found_response['response']}[/yellow]\n"
        f"[dim]Timestamp:[/dim] {found_response['timestamp']}\n\n"
        f"[dim]The coordinator polling pattern is working perfectly![/dim]",
        border_style="green"
    ))
else:
    console.print(Panel(
        f"[yellow]⏱️ Timeout[/yellow]\n\n"
        f"No response received after {max_attempts * 10} seconds.\n\n"
        f"[dim]Make sure you sent:[/dim]\n"
        f"  [cyan]{workflow_id}: Your answer[/cyan]",
        border_style="yellow"
    ))
