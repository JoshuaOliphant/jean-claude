#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click>=8.1.7",
#     "pydantic>=2.10.3",
#     "python-dotenv>=1.0.1",
#     "rich>=13.0.0",
# ]
# ///
# ABOUTME: TDD planning script that breaks specifications into GitHub issue-sized chunks.
# ABOUTME: Analyzes complexity and dependencies to create actionable implementation plans.

import os
import sys
import uuid
import click
from pathlib import Path
from typing import Optional, Literal
from rich.console import Console
from rich.panel import Panel

# Add adw_modules to path
sys.path.insert(0, str(Path(__file__).parent / "adw_modules"))

from agent import (
    execute_template,
    AgentTemplateRequest,
)


@click.command()
@click.argument("spec_input")
@click.option(
    "--spec-file",
    is_flag=True,
    help="Treat spec_input as a file path to read",
)
@click.option(
    "--model",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="Claude model to use (sonnet=balanced, opus=max intelligence, haiku=fast)",
)
@click.option(
    "--adw-id",
    help="Custom ADW ID (default: auto-generated)",
)
@click.option(
    "--create-issues",
    is_flag=True,
    help="Create GitHub issues for each task (requires gh CLI)",
)
@click.option(
    "--working-dir",
    type=click.Path(exists=True),
    help="Working directory for execution",
)
def main(
    spec_input: str,
    spec_file: bool,
    model: Literal["sonnet", "opus", "haiku"],
    adw_id: Optional[str],
    create_issues: bool,
    working_dir: Optional[str],
):
    """
    Create a TDD implementation plan from a specification.

    Breaks down large tasks into GitHub issue-sized chunks following TDD principles.

    Examples:

        # From description
        ./adws/adw_plan_tdd.py "Add user authentication with JWT"

        # From spec file
        ./adws/adw_plan_tdd.py specs/feature-auth.md --spec-file

        # Use Opus for complex planning
        ./adws/adw_plan_tdd.py "Build real-time chat system" --model opus

        # Create GitHub issues automatically
        ./adws/adw_plan_tdd.py "Add OAuth2 support" --create-issues
    """
    console = Console()

    # Generate ADW ID if not provided
    if not adw_id:
        adw_id = str(uuid.uuid4())[:8]

    # Read spec from file if specified
    if spec_file:
        spec_path = Path(spec_input)
        if not spec_path.exists():
            console.print(f"[red]Spec file not found: {spec_input}[/red]")
            sys.exit(1)
        specification = spec_path.read_text()
        console.print(f"[dim]Read specification from: {spec_input}[/dim]")
    else:
        specification = spec_input

    console.print(
        Panel(
            f"[bold blue]TDD Planning[/bold blue]\n\n"
            f"[cyan]ADW ID:[/cyan] {adw_id}\n"
            f"[cyan]Model:[/cyan] {model}\n"
            f"[cyan]Working Dir:[/cyan] {working_dir or 'current'}",
            title="[bold blue]Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Create plans directory if it doesn't exist
    plans_dir = Path("specs/plans")
    plans_dir.mkdir(parents=True, exist_ok=True)

    # Execute /plan-tdd command
    console.print("[dim]Generating task breakdown...[/dim]")

    template_request = AgentTemplateRequest(
        slash_command="/plan-tdd",
        args=[adw_id, specification],
        adw_id=adw_id,
        agent_name="plan-tdd",
        model=model,
        working_dir=working_dir,
    )

    result = execute_template(template_request)

    if not result.success:
        console.print(f"[red]Plan generation failed[/red]")
        console.print(f"[dim]Output: {result.output[:800]}[/dim]")
        sys.exit(1)

    console.print("[green]Plan generation complete![/green]")
    console.print()

    # Find the generated plan file
    plan_file = plans_dir / f"plan-{adw_id}.md"

    if not plan_file.exists():
        console.print(f"[yellow]Plan file not found at expected location: {plan_file}[/yellow]")
        console.print("[dim]The plan may have been created with a different name.[/dim]")
        console.print()
        console.print("[dim]Check specs/plans/ directory for the generated plan.[/dim]")
        sys.exit(0)

    console.print(f"[cyan]Plan saved to:[/cyan] {plan_file}")
    console.print()

    # Parse plan to show summary
    plan_content = plan_file.read_text()

    # Count tasks (simple parsing)
    task_lines = [line for line in plan_content.split('\n') if line.startswith('### Task ')]
    num_tasks = len(task_lines)

    # Count complexity
    complexity_s = plan_content.count('**Complexity**: S')
    complexity_m = plan_content.count('**Complexity**: M')
    complexity_l = plan_content.count('**Complexity**: L')

    console.print("[bold]Plan Summary:[/bold]")
    console.print(f"   Total tasks: {num_tasks}")
    console.print(f"   Simple (S):  {complexity_s} tasks")
    console.print(f"   Medium (M):  {complexity_m} tasks")
    console.print(f"   Large (L):   {complexity_l} tasks")
    console.print()

    # Show complexity insights
    if complexity_l > 0:
        console.print("[yellow]Warning: Contains Large tasks - consider breaking down further[/yellow]")
    if complexity_s + complexity_m > 20:
        console.print("[dim]Tip: Consider grouping related small tasks for efficiency[/dim]")
    console.print()

    # Create GitHub issues if requested
    if create_issues:
        console.print("[dim]Creating GitHub issues...[/dim]")

        # Check if gh CLI is available
        import subprocess
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            console.print("[red]GitHub CLI (gh) not found. Install: brew install gh[/red]")
            console.print("[dim]Skipping issue creation.[/dim]")
            sys.exit(1)

        # Parse tasks and create issues
        console.print("[yellow]GitHub issue creation not yet implemented.[/yellow]")
        console.print("[dim]You can manually create issues from the plan.[/dim]")
        console.print()

    # Show next steps
    console.print("[bold]Next Steps:[/bold]")
    console.print()
    console.print("1. Review the plan:")
    console.print(f"   [dim]cat {plan_file}[/dim]")
    console.print()
    console.print("2. Implement tasks in order:")
    console.print("[dim]   # Extract task specs from plan and use /implement[/dim]")
    console.print("[dim]   # Or manually implement following the task breakdown[/dim]")
    console.print()
    console.print("3. Track progress:")
    console.print("[dim]   # Mark tasks complete in the plan file[/dim]")
    console.print("[dim]   # Or create GitHub issues for tracking[/dim]")
    console.print()

    console.print(f"[dim]Full output available in: agents/{adw_id}/plan-tdd/[/dim]")


if __name__ == "__main__":
    main()
