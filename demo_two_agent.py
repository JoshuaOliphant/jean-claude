#!/usr/bin/env python3
"""Demo script to test two-agent workflow pattern.

This script demonstrates the two-agent pattern:
1. Initializer (Opus) - Plans features
2. Coder (Sonnet) - Implements them

Run with: uv run python demo_two_agent.py
"""

import asyncio
from pathlib import Path

from rich.console import Console

from jean_claude.orchestration.two_agent import run_initializer


console = Console()


async def main():
    """Run a simple demo of the two-agent initializer."""
    project_root = Path.cwd()

    console.print()
    console.print("[bold blue]Two-Agent Pattern Demo[/bold blue]")
    console.print("[dim]Testing initializer agent only (no actual execution)[/dim]")
    console.print()

    # Simple task description
    description = """
    Create a simple calculator module with the following features:
    - Addition, subtraction, multiplication, division
    - Error handling for division by zero
    - Input validation
    - Comprehensive test coverage
    """

    console.print("[yellow]Note:[/yellow] This will call Claude's API to generate the feature plan.")
    console.print("[yellow]Set ANTHROPIC_API_KEY in .env or use Claude Max subscription.[/yellow]")
    console.print()

    try:
        # Run initializer only
        state = await run_initializer(
            description=description,
            project_root=project_root,
            workflow_id="demo-calculator",
            model="haiku",  # Use haiku for cheaper demo
        )

        console.print()
        console.print("[green]✓ Initializer completed successfully![/green]")
        console.print()
        console.print("[bold]Generated Feature Plan:[/bold]")
        console.print(f"  Workflow ID: [cyan]{state.workflow_id}[/cyan]")
        console.print(f"  Total Features: [cyan]{len(state.features)}[/cyan]")
        console.print(f"  Max Iterations: [cyan]{state.max_iterations}[/cyan]")
        console.print()

        # Show state file location
        state_file = project_root / "agents" / state.workflow_id / "state.json"
        console.print(f"[dim]State saved to: {state_file}[/dim]")
        console.print()

        console.print("[yellow]To execute this plan with the coder agent, run:[/yellow]")
        console.print(f"[cyan]  jc workflow 'Create calculator' --workflow-id {state.workflow_id}[/cyan]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    raise SystemExit(exit_code)
