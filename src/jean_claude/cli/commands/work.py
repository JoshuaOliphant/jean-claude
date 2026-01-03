# ABOUTME: Implementation of the 'jc work' command for Beads task integration
# ABOUTME: Executes workflows based on Beads tasks

"""Execute Jean Claude workflows from Beads tasks."""

from pathlib import Path

import anyio
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm

from jean_claude.core.beads import (
    close_beads_task,
    fetch_beads_task,
    generate_spec_from_beads,
    update_beads_status,
)
from jean_claude.core.edit_and_revalidate import edit_and_revalidate
from jean_claude.core.evaluation import evaluate_workflow, save_evaluation
from jean_claude.core.events import EventLogger, EventType
from jean_claude.core.interactive_prompt_handler import (
    InteractivePromptHandler,
    PromptAction,
)
from jean_claude.core.state import WorkflowState
from jean_claude.core.task_validator import TaskValidator
from jean_claude.orchestration.evaluator_agent import run_evaluator_agent
from jean_claude.orchestration.two_agent import run_two_agent_workflow

console = Console()


def _run_evaluation(
    state: WorkflowState,
    project_root: Path,
    event_logger: EventLogger,
    console: Console,
    ai_eval: bool = False,
) -> None:
    """Run post-workflow evaluation and display results.

    Args:
        state: The workflow state to evaluate
        project_root: Project root path
        event_logger: Event logger for emitting evaluation events
        console: Rich console for output
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
@click.argument("beads_id")
@click.option(
    "--model",
    "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="Claude model to use",
)
@click.option(
    "--show-plan",
    is_flag=True,
    default=False,
    help="Pause after planning phase for approval before implementing",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Plan only, don't implement (dry run mode)",
)
@click.option(
    "--auto-confirm",
    is_flag=True,
    default=False,
    help="Skip confirmation prompts and proceed automatically",
)
@click.option(
    "--strict",
    is_flag=True,
    default=False,
    help="Enable strict validation mode (converts warnings to errors)",
)
@click.option(
    "--ai-eval",
    is_flag=True,
    default=False,
    help="Enable AI evaluator agent for qualitative code review",
)
def work(beads_id: str, model: str, show_plan: bool, dry_run: bool, auto_confirm: bool, strict: bool, ai_eval: bool) -> None:
    """Execute a workflow from a Beads task.

    Fetches task details from Beads, generates a specification,
    and executes a Jean Claude workflow to implement the task.

    \b
    BEADS_ID is the identifier of the Beads task to work on.

    \b
    Examples:
      jc work jean_claude-2sz.3
      jc work project-123.4 --model opus
      jc work task-abc.1 -m haiku
    """
    try:
        # Initialize EventLogger
        project_root = Path.cwd()
        event_logger = EventLogger(project_root)
        workflow_id = f"beads-{beads_id}"

        # Fetch the Beads task
        console.print(f"[bold blue]Fetching Beads task: {beads_id}[/bold blue]")
        task = fetch_beads_task(beads_id)
        console.print(f"[green]✓[/green] Task fetched: {task.title}")
        console.print()

        # Validate the task
        console.print("[bold blue]Validating task...[/bold blue]")
        validator = TaskValidator()
        validation_result = validator.validate(task)

        # Apply strict mode if requested
        if strict and validation_result.has_warnings():
            validation_result = validation_result.to_strict()

        # Check if there are errors or warnings
        if validation_result.has_errors() or validation_result.has_warnings():
            console.print("[yellow]⚠[/yellow] Validation issues found")
            console.print()

            # If strict mode and has errors, don't proceed
            if validation_result.has_errors():
                console.print("[bold red]Validation failed:[/bold red]")
                for error in validation_result.errors:
                    console.print(f"  [red]✗[/red] {error}")
                console.print()
                console.print("[dim]Fix the issues and try again, or run without --strict[/dim]")
                raise click.Abort()

            # Show interactive prompt for warnings
            prompt_handler = InteractivePromptHandler()
            action = prompt_handler.prompt(validation_result)

            if action == PromptAction.CANCEL:
                console.print()
                console.print("[yellow]Task cancelled by user[/yellow]")
                raise click.Abort()

            elif action == PromptAction.EDIT:
                console.print()
                console.print("[bold blue]Opening task for editing...[/bold blue]")

                # Edit and re-validate loop
                while True:
                    try:
                        validation_result = edit_and_revalidate(beads_id, strict=strict)

                        # If no more warnings/errors, break the loop
                        if not validation_result.has_warnings() and not validation_result.has_errors():
                            console.print("[green]✓[/green] Task validation passed after editing")
                            console.print()
                            # Re-fetch the task to get updated data
                            task = fetch_beads_task(beads_id)
                            break

                        # Still has issues, prompt again
                        console.print()
                        action = prompt_handler.prompt(validation_result)

                        if action == PromptAction.CANCEL:
                            console.print()
                            console.print("[yellow]Task cancelled by user[/yellow]")
                            raise click.Abort()

                        elif action == PromptAction.PROCEED:
                            console.print()
                            console.print("[yellow]Proceeding despite warnings...[/yellow]")
                            console.print()
                            # Re-fetch the task to get updated data
                            task = fetch_beads_task(beads_id)
                            break
                        # else: action == EDIT, continue loop

                    except (RuntimeError, KeyboardInterrupt) as e:
                        console.print()
                        console.print(f"[bold red]Error during edit:[/bold red] {e}")
                        raise click.Abort()

            elif action == PromptAction.PROCEED:
                console.print()
                console.print("[yellow]Proceeding despite warnings...[/yellow]")
                console.print()

        else:
            console.print("[green]✓[/green] Task validation passed")
            console.print()

        # Emit workflow.started event
        event_logger.emit(
            workflow_id=workflow_id,
            event_type="workflow.started",
            data={"beads_task_id": beads_id}
        )

        # Update Beads task status to 'in_progress'
        console.print("[bold blue]Updating task status to 'in_progress'...[/bold blue]")
        try:
            update_beads_status(beads_id, "in_progress")
            console.print("[green]✓[/green] Task status updated to 'in_progress'")
        except RuntimeError as e:
            # Handle status update failures gracefully - log warning but continue
            console.print(f"[yellow]⚠[/yellow] Warning: Failed to update task status: {e}")
            console.print("[dim]Continuing with workflow execution...[/dim]")
        console.print()

        # Initialize WorkflowState with Beads task information
        console.print("[bold blue]Initializing workflow state...[/bold blue]")
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            workflow_name=task.title,
            workflow_type="beads-task",
            beads_task_id=beads_id,
            beads_task_title=task.title,
            phase="planning"
        )
        console.print("[green]✓[/green] Workflow state initialized")
        console.print()

        # Generate specification from the task
        console.print("[bold blue]Generating specification...[/bold blue]")
        spec_content = generate_spec_from_beads(task)
        console.print("[green]✓[/green] Specification generated")
        console.print()

        # Create specs directory if it doesn't exist
        specs_dir = Path("specs")
        specs_dir.mkdir(exist_ok=True)

        # Write spec to file
        spec_filename = f"beads-{beads_id}.md"
        spec_path = specs_dir / spec_filename
        try:
            spec_path.write_text(spec_content)
        except PermissionError as e:
            console.print(f"[bold red]Error:[/bold red] Permission denied writing spec file to [cyan]{spec_path}[/cyan]")
            console.print(f"[dim]Details: {e}[/dim]")
            console.print("[dim]Check file and directory permissions[/dim]")
            raise click.Abort()
        except OSError as e:
            console.print(f"[bold red]Error:[/bold red] Failed to write spec file to [cyan]{spec_path}[/cyan]")
            console.print(f"[dim]Details: {e}[/dim]")
            console.print("[dim]Check disk space and file system availability[/dim]")
            raise click.Abort()
        console.print(f"[green]✓[/green] Specification saved to: [cyan]{spec_path}[/cyan]")
        console.print()

        # Display the spec to the user
        console.print("[bold blue]Task Specification:[/bold blue]")
        console.print(Panel(Markdown(spec_content), border_style="blue"))
        console.print()

        # Save workflow state (initial planning phase)
        console.print("[bold blue]Saving workflow state...[/bold blue]")
        workflow_state.save(project_root)
        console.print("[green]✓[/green] Workflow state saved (phase: planning)")
        console.print()

        # Show current configuration
        console.print("[dim]Configuration:[/dim]")
        console.print(f"[dim]  Model: {model}[/dim]")
        console.print(f"[dim]  Show plan: {show_plan}[/dim]")
        console.print(f"[dim]  Dry run: {dry_run}[/dim]")
        console.print(f"[dim]  Auto confirm: {auto_confirm}[/dim]")
        console.print(f"[dim]  Strict validation: {strict}[/dim]")
        console.print()

        # Handle dry-run mode: only planning, no execution
        if dry_run:
            console.print()
            console.print("[bold yellow]DRY RUN MODE[/bold yellow]")
            console.print("[dim]Planning complete. Skipping workflow execution.[/dim]")
            console.print()

            # Emit workflow.completed event for dry-run
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="workflow.completed",
                data={"beads_task_id": beads_id, "dry_run": True}
            )

            console.print("[bold green]Dry run completed successfully![/bold green]")
            return

        # Handle show-plan mode: wait for user approval
        if show_plan:
            console.print()
            confirmed = Confirm.ask(
                "[yellow]Proceed with workflow execution?[/yellow]",
                default=True,
            )

            if not confirmed:
                console.print()
                console.print("[yellow]Workflow cancelled by user[/yellow]")

                # Emit workflow.completed event for cancelled workflow
                event_logger.emit(
                    workflow_id=workflow_id,
                    event_type="workflow.completed",
                    data={"beads_task_id": beads_id, "cancelled": True}
                )

                return

        # Execute workflow using run_two_agent_workflow
        console.print()
        console.print("[bold blue]Starting workflow execution...[/bold blue]")
        console.print()

        try:
            # Phase transition: planning -> implementing
            console.print("[bold blue]Transitioning to implementing phase...[/bold blue]")
            from_phase = workflow_state.phase
            workflow_state.phase = "implementing"
            workflow_state.save(project_root)
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="workflow.phase_changed",
                data={
                    "beads_task_id": beads_id,
                    "from_phase": from_phase,
                    "to_phase": "implementing"
                }
            )
            console.print("[green]✓[/green] Phase transition complete (phase: implementing)")
            console.print()

            # Run the two-agent workflow
            # Pass the spec content as description, using the --model flag for both agents
            final_state = anyio.run(
                run_two_agent_workflow,
                spec_content,  # Use generated spec as task description
                project_root,
                workflow_id,  # Use beads-{task_id} as workflow_id
                model,  # initializer_model
                model,  # coder_model (same as initializer when using --model flag)
                None,  # max_iterations (let workflow decide)
                auto_confirm,  # Pass auto_confirm flag through
                event_logger,  # Pass event_logger for feature events
            )

            # Phase transition: implementing -> verifying (use final_state from workflow)
            console.print()
            console.print("[bold blue]Transitioning to verifying phase...[/bold blue]")
            from_phase = final_state.phase
            final_state.phase = "verifying"
            final_state.save(project_root)
            event_logger.emit(
                workflow_id=workflow_id,
                event_type="workflow.phase_changed",
                data={
                    "beads_task_id": beads_id,
                    "from_phase": from_phase,
                    "to_phase": "verifying"
                }
            )
            console.print("[green]✓[/green] Phase transition complete (phase: verifying)")
            console.print()

            # Check workflow result
            if final_state.is_complete():
                # Phase transition: verifying -> complete
                console.print("[bold blue]Transitioning to complete phase...[/bold blue]")
                from_phase = final_state.phase
                final_state.phase = "complete"
                final_state.save(project_root)
                event_logger.emit(
                    workflow_id=workflow_id,
                    event_type="workflow.phase_changed",
                    data={
                        "beads_task_id": beads_id,
                        "from_phase": from_phase,
                        "to_phase": "complete"
                    }
                )
                console.print("[green]✓[/green] Phase transition complete (phase: complete)")
                console.print()

                # Emit workflow.completed event
                event_logger.emit(
                    workflow_id=workflow_id,
                    event_type="workflow.completed",
                    data={"beads_task_id": beads_id}
                )

                console.print("[bold green]Workflow completed successfully![/bold green]")
                console.print()

                # Run post-workflow evaluation
                _run_evaluation(final_state, project_root, event_logger, console, ai_eval)

                # Close Beads task on successful completion
                console.print("[bold blue]Closing Beads task...[/bold blue]")
                try:
                    close_beads_task(beads_id)
                    console.print("[green]✓[/green] Task closed successfully")
                except RuntimeError as e:
                    console.print(f"[yellow]⚠[/yellow] Warning: Failed to close task: {e}")
                    console.print("[dim]Task completion tracking may be incomplete[/dim]")

            elif final_state.is_failed():
                console.print()
                console.print("[bold red]Workflow failed[/bold red]")
                console.print(f"[dim]Check state: agents/{final_state.workflow_id}/state.json[/dim]")

                # Run post-workflow evaluation even for failed workflows
                _run_evaluation(final_state, project_root, event_logger, console, ai_eval)

                raise click.Abort()
            else:
                console.print()
                console.print("[bold yellow]Workflow incomplete[/bold yellow]")
                console.print(f"[dim]Resume with: jc implement {final_state.workflow_id}[/dim]")

                # Run post-workflow evaluation for incomplete workflows
                _run_evaluation(final_state, project_root, event_logger, console, ai_eval)

        except KeyboardInterrupt:
            console.print()
            console.print("[yellow]Workflow cancelled by user[/yellow]")
            raise click.Abort()
        except Exception as workflow_error:
            # Don't close task on workflow failure
            console.print()
            console.print(f"[bold red]Workflow error:[/bold red] {workflow_error}")
            raise click.Abort()

    except RuntimeError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
