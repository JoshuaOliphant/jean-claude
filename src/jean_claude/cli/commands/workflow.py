# ABOUTME: CLI command for two-agent workflow orchestration
# ABOUTME: Runs initializer (Opus) to plan features, then coder (Sonnet) to implement them

"""Workflow command for two-agent orchestration."""

from pathlib import Path

import anyio
import click
from rich.console import Console
from rich.panel import Panel

from jean_claude.core.evaluation import evaluate_workflow, save_evaluation
from jean_claude.core.events import EventLogger, EventType
from jean_claude.core.state import WorkflowState
from jean_claude.orchestration.evaluator_agent import run_evaluator_agent
from jean_claude.orchestration.two_agent import run_two_agent_workflow

console = Console()


def _run_evaluation(
    state: WorkflowState,
    project_root: Path,
    event_logger: EventLogger,
    ai_eval: bool = False,
) -> None:
    """Run post-workflow evaluation and display results.

    Args:
        state: The workflow state to evaluate
        project_root: Project root path
        event_logger: Event logger for emitting evaluation events
        ai_eval: Whether to run AI agent evaluation (adds qualitative analysis)
    """
    console.print()
    console.print("[bold blue]Running post-workflow evaluation...[/bold blue]")

    try:
        # Run metric-based evaluation
        evaluation = evaluate_workflow(state)

        # Save evaluation to disk
        eval_path = save_evaluation(evaluation, project_root)

        # Emit evaluation event
        event_logger.emit(
            workflow_id=state.workflow_id,
            event_type=EventType.WORKFLOW_EVALUATED,
            data={
                "quality_score": evaluation.quality_score,
                "grade": evaluation.grade,
                "completion_rate": evaluation.metrics.completion_rate,
                "test_pass_rate": evaluation.metrics.test_pass_rate,
                "summary": evaluation.summary,
            }
        )

        # Display evaluation results
        grade_colors = {
            "A": "green",
            "B": "cyan",
            "C": "yellow",
            "D": "orange1",
            "F": "red",
        }
        grade_color = grade_colors.get(evaluation.grade, "white")

        # Build metrics display
        metrics_lines = [
            f"[bold]Quality Score:[/bold] [{grade_color}]{evaluation.quality_score:.0%}[/{grade_color}] (Grade: [{grade_color}]{evaluation.grade}[/{grade_color}])",
            "",
            "[dim]Metrics:[/dim]",
            f"  Completion Rate: {evaluation.metrics.completion_rate:.0%}",
            f"  Test Pass Rate: {evaluation.metrics.test_pass_rate:.0%}",
            f"  Iteration Efficiency: {evaluation.metrics.iteration_efficiency:.0%}",
            f"  Cost Efficiency: {evaluation.metrics.cost_efficiency:.0%}",
            f"  Time Efficiency: {evaluation.metrics.time_efficiency:.0%}",
        ]

        # Add recommendations if any
        if evaluation.recommendations:
            metrics_lines.append("")
            metrics_lines.append("[dim]Recommendations:[/dim]")
            for rec in evaluation.recommendations:
                metrics_lines.append(f"  • {rec}")

        console.print(Panel(
            "\n".join(metrics_lines),
            title="[bold]Workflow Evaluation[/bold]",
            border_style=grade_color,
        ))

        console.print(f"[green]✓[/green] Evaluation saved to: [cyan]{eval_path}[/cyan]")
        console.print()

        # Run AI agent evaluation if requested
        if ai_eval:
            console.print("[bold blue]Running AI evaluator agent...[/bold blue]")
            try:
                agent_eval = anyio.run(run_evaluator_agent, state, project_root, "haiku")

                # Display AI evaluation results
                rating_colors = {
                    "excellent": "green",
                    "good": "cyan",
                    "acceptable": "yellow",
                    "needs_improvement": "orange1",
                    "poor": "red",
                }
                rating_color = rating_colors.get(agent_eval.quality_rating, "white")

                ai_lines = [
                    f"[bold]AI Assessment:[/bold] [{rating_color}]{agent_eval.quality_rating.upper()}[/{rating_color}]",
                    "",
                    f"[italic]{agent_eval.overall_assessment}[/italic]",
                ]

                if agent_eval.strengths:
                    ai_lines.append("")
                    ai_lines.append("[green]Strengths:[/green]")
                    for s in agent_eval.strengths[:5]:
                        ai_lines.append(f"  ✓ {s}")

                if agent_eval.improvements:
                    ai_lines.append("")
                    ai_lines.append("[yellow]Improvements:[/yellow]")
                    for i in agent_eval.improvements[:5]:
                        ai_lines.append(f"  → {i}")

                if agent_eval.potential_issues:
                    ai_lines.append("")
                    ai_lines.append("[red]Potential Issues:[/red]")
                    for p in agent_eval.potential_issues[:3]:
                        ai_lines.append(f"  ⚠ {p}")

                console.print(Panel(
                    "\n".join(ai_lines),
                    title="[bold]AI Code Review[/bold]",
                    border_style=rating_color,
                ))

                console.print("[green]✓[/green] AI evaluation complete")
                console.print()

            except Exception as agent_error:
                console.print(f"[yellow]⚠[/yellow] AI evaluation failed: {agent_error}")
                console.print("[dim]Metric-based evaluation was still successful[/dim]")
                console.print()

    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Evaluation failed: {e}")
        console.print("[dim]Workflow completed but evaluation could not be generated[/dim]")
        console.print()


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
@click.option(
    "--ai-eval",
    is_flag=True,
    default=False,
    help="Enable AI evaluator agent for qualitative code review",
)
def workflow(
    description: str | None,
    spec_file: Path | None,
    workflow_id: str | None,
    initializer_model: str,
    coder_model: str,
    max_iterations: int | None,
    auto_confirm: bool,
    working_dir: Path | None,
    ai_eval: bool,
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
        # With AI evaluation
        jc workflow "Add feature" --ai-eval

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
        try:
            task_description = spec_file.read_text()
        except FileNotFoundError as e:
            console.print(f"[bold red]Error:[/bold red] Spec file not found at [cyan]{spec_file}[/cyan]")
            console.print(f"[dim]Details: {e}[/dim]")
            console.print("[dim]Check that the file path is correct[/dim]")
            raise click.Abort()
        except PermissionError as e:
            console.print(f"[bold red]Error:[/bold red] Permission denied reading spec file at [cyan]{spec_file}[/cyan]")
            console.print(f"[dim]Details: {e}[/dim]")
            console.print("[dim]Check file permissions[/dim]")
            raise click.Abort()
        except OSError as e:
            console.print(f"[bold red]Error:[/bold red] Failed to read spec file at [cyan]{spec_file}[/cyan]")
            console.print(f"[dim]Details: {e}[/dim]")
            console.print("[dim]Check file system availability and file integrity[/dim]")
            raise click.Abort()
    else:
        task_description = description  # type: ignore

    project_root = working_dir or Path.cwd()
    event_logger = EventLogger(project_root)

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
            # Run post-workflow evaluation
            _run_evaluation(final_state, project_root, event_logger, ai_eval)
        elif final_state.is_failed():
            console.print()
            console.print("[bold red]Workflow failed[/bold red]")
            console.print(f"[dim]Check state: agents/{final_state.workflow_id}/state.json[/dim]")
            # Run post-workflow evaluation for failed workflows
            _run_evaluation(final_state, project_root, event_logger, ai_eval)
            raise SystemExit(1)
        else:
            console.print()
            console.print("[bold yellow]Workflow incomplete[/bold yellow]")
            console.print(
                f"[dim]Resume with: jc implement {final_state.workflow_id}[/dim]"
            )
            # Run post-workflow evaluation for incomplete workflows
            _run_evaluation(final_state, project_root, event_logger, ai_eval)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Workflow cancelled by user[/yellow]")
        raise SystemExit(130)  # Standard exit code for SIGINT

    except Exception as e:
        console.print()
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise SystemExit(1)
