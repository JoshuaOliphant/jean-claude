# ABOUTME: Auto-continue orchestrator for long-running Jean Claude workflows
# ABOUTME: Runs workflows in a loop until all features are complete with state persistence

"""Auto-continue orchestrator for long-running workflows.

This module implements the auto-continue pattern from Anthropic's autonomous
coding agent quickstart. It enables workflows to run for extended periods
by:

1. **Fresh Context Per Iteration**: Each iteration starts with a clean slate
2. **File-Based State Machine**: State persists in state.json between iterations
3. **Verification-First**: Always verify existing work before new work
4. **Defense-in-Depth**: Multiple safety layers prevent runaway execution

Key Pattern:
    - Read state.json to get next feature
    - Execute single feature
    - Update state.json with result
    - Repeat until all features complete

Safety Features:
    - Max iteration limit (default: 50)
    - Graceful interrupt handling
    - State saved after every iteration
    - Clear progress logging
"""

import asyncio
import signal
from pathlib import Path
from typing import Optional

import anyio
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from jean_claude.core.state import WorkflowState, Feature
from jean_claude.core.agent import PromptRequest, ExecutionResult, _execute_prompt_sdk_async
from jean_claude.core.verification import run_verification, VerificationResult
from jean_claude.core.events import EventLogger, EventType
from jean_claude.core.feature_commit_orchestrator import FeatureCommitOrchestrator


console = Console()


class AutoContinueError(Exception):
    """Raised when auto-continue workflow encounters an error."""

    pass


def build_feature_prompt(feature: Feature, state: WorkflowState, project_root: Path) -> str:
    """Build a prompt for implementing the next feature.

    The prompt follows the verification-first pattern:
    1. Get your bearings - read state, verify tests
    2. Implement feature
    3. Update state

    Args:
        feature: The feature to implement
        state: Current workflow state
        project_root: Project root directory

    Returns:
        Prompt string for the agent
    """
    state_file = project_root / "agents" / state.workflow_id / "state.json"

    prompt = f"""## TASK: {feature.name}

You are working on feature {state.current_feature_index + 1} of {len(state.features)} in workflow {state.workflow_id}.

## STEP 1: GET YOUR BEARINGS (MANDATORY)

Before doing ANYTHING:

1. Read the state file: {state_file}
2. Run ALL existing tests to verify nothing is broken
3. If any test fails → FIX IT FIRST (don't move to new features)
4. Only after all tests pass → proceed to feature implementation

## STEP 2: IMPLEMENT FEATURE

**Feature Name**: {feature.name}

**Description**: {feature.description}

**Requirements**:
- Write tests FIRST (TDD approach)
- Implement the feature
- Ensure all tests pass
{f"- Tests should be in: {feature.test_file}" if feature.test_file else ""}

## STEP 3: UPDATE STATE

After completing the feature:

1. Mark feature as complete in {state_file}
2. Set tests_passing to true
3. Increment current_feature_index
4. Save the state file

## CRITICAL CONSTRAINTS

⚠️ NEVER skip the verification step
⚠️ NEVER modify the feature list in state.json
⚠️ NEVER work on multiple features simultaneously
⚠️ ALWAYS save state after completion

Work on EXACTLY ONE feature this session. Do not proceed to the next feature.
"""

    return prompt


async def run_auto_continue(
    state: WorkflowState,
    project_root: Path,
    max_iterations: Optional[int] = None,
    delay_seconds: float = 2.0,
    model: str = "sonnet",
    verify_first: bool = True,
    event_logger: Optional[EventLogger] = None,
) -> WorkflowState:
    """Run workflow in a loop until all features complete.

    This implements the core auto-continue pattern:
    - Each iteration processes ONE feature
    - State persists between iterations
    - Fresh context each time
    - Continues until complete or max iterations
    - Verification-first: runs tests before new work (if enabled)

    Args:
        state: Initial workflow state with features
        project_root: Project root directory
        max_iterations: Maximum iterations before stopping (uses state.max_iterations if None)
        delay_seconds: Seconds to wait between iterations (default: 2.0)
        model: Claude model to use (default: "sonnet")
        verify_first: Run verification tests before each iteration (default: True)

    Returns:
        Final workflow state

    Raises:
        AutoContinueError: If workflow fails unrecoverably
    """
    max_iter = max_iterations or state.max_iterations
    output_dir = project_root / "agents" / state.workflow_id / "auto_continue"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup interrupt handling
    interrupted = False

    def signal_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        console.print("\n[yellow]⚠ Interrupt received. Finishing current iteration...[/yellow]")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    console.print()
    console.print(
        Panel(
            f"[bold blue]Starting Auto-Continue Workflow[/bold blue]\n\n"
            f"Workflow ID: [cyan]{state.workflow_id}[/cyan]\n"
            f"Type: [cyan]{state.workflow_type}[/cyan]\n"
            f"Total Features: [cyan]{len(state.features)}[/cyan]\n"
            f"Max Iterations: [cyan]{max_iter}[/cyan]\n"
            f"Model: [cyan]{model}[/cyan]",
            border_style="blue",
        )
    )
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"Processing features...",
            total=len(state.features),
            completed=state.current_feature_index,
        )

        while state.iteration_count < max_iter and not interrupted:
            # Get next feature
            feature = state.get_next_feature()

            if feature is None:
                console.print("[green]✓ All features completed![/green]")
                break

            # VERIFICATION-FIRST: Run tests before starting new work
            if verify_first and state.should_verify():
                console.print()
                console.print("[blue]Running verification tests...[/blue]")

                verification_result = run_verification(state, project_root)
                state.mark_verification(verification_result.passed)
                state.save(project_root)

                if verification_result.skipped:
                    console.print(f"[dim]Skipped: {verification_result.skip_reason}[/dim]")
                elif verification_result.passed:
                    console.print(
                        f"[green]✓ Verification passed[/green] "
                        f"({verification_result.tests_run} test files, "
                        f"{verification_result.duration_ms}ms)"
                    )
                else:
                    console.print(
                        f"[red]✗ Verification failed![/red] "
                        f"Fix these tests before continuing:"
                    )
                    for failed_test in verification_result.failed_tests:
                        console.print(f"  [red]• {failed_test}[/red]")
                    console.print()
                    console.print("[yellow]Output:[/yellow]")
                    console.print(verification_result.test_output)
                    console.print()
                    console.print("[yellow]Stopping workflow due to test failures[/yellow]")
                    break

                console.print()

            # Start the feature
            state.start_feature()
            progress.update(
                task,
                description=f"[cyan]Feature {state.current_feature_index + 1}/{len(state.features)}: {feature.name}[/cyan]",
            )

            # Emit feature.started event
            if event_logger:
                event_logger.emit(
                    workflow_id=state.workflow_id,
                    event_type=EventType.FEATURE_STARTED,
                    data={
                        "feature_name": feature.name,
                        "feature_index": state.current_feature_index,
                        "total_features": len(state.features),
                    }
                )

            # Build prompt
            prompt = build_feature_prompt(feature, state, project_root)

            # Execute
            iteration_dir = output_dir / f"iteration_{state.iteration_count:03d}"
            iteration_dir.mkdir(parents=True, exist_ok=True)

            request = PromptRequest(
                prompt=prompt,
                model=model,
                working_dir=project_root,
                output_dir=iteration_dir,
                dangerously_skip_permissions=True,
            )

            try:
                result: ExecutionResult = await _execute_prompt_sdk_async(request, max_retries=3)

                # Update state based on result
                if result.success:
                    state.mark_feature_complete()
                    if feature.test_file:
                        feature.tests_passing = True

                    # Update tracking
                    if result.cost_usd:
                        state.total_cost_usd += result.cost_usd
                    if result.duration_ms:
                        state.total_duration_ms += result.duration_ms
                    if result.session_id:
                        state.session_ids.append(result.session_id)

                    progress.update(task, completed=state.current_feature_index)
                    console.print(
                        f"[green]✓ Completed: {feature.name}[/green] "
                        f"({state.progress_percentage:.1f}% done)"
                    )

                    # Trigger commit workflow for completed feature
                    try:
                        console.print("[dim]Creating commit for completed feature...[/dim]")
                        commit_orchestrator = FeatureCommitOrchestrator(repo_path=project_root)

                        # Determine feature number (1-based index)
                        feature_number = state.current_feature_index

                        # Get Beads task ID (if available)
                        beads_task_id = state.beads_task_id or "unknown"

                        commit_result = commit_orchestrator.commit_feature(
                            feature_name=feature.name,
                            feature_description=feature.description,
                            beads_task_id=beads_task_id,
                            feature_number=feature_number,
                            total_features=len(state.features),
                            feature_context=feature.name
                        )

                        if commit_result["success"]:
                            console.print(
                                f"[green]✓ Commit created: {commit_result['commit_sha']}[/green]"
                            )
                        else:
                            # Log commit failure but don't block workflow
                            console.print(
                                f"[yellow]⚠ Commit failed ({commit_result['step']}): "
                                f"{commit_result['error']}[/yellow]"
                            )
                            console.print("[dim]Continuing workflow despite commit failure...[/dim]")

                    except Exception as commit_error:
                        # Handle commit errors gracefully without blocking workflow
                        console.print(
                            f"[yellow]⚠ Commit error: {str(commit_error)}[/yellow]"
                        )
                        console.print("[dim]Continuing workflow despite commit error...[/dim]")

                    # Emit feature.completed event
                    if event_logger:
                        event_logger.emit(
                            workflow_id=state.workflow_id,
                            event_type=EventType.FEATURE_COMPLETED,
                            data={
                                "feature_name": feature.name,
                                "feature_index": state.current_feature_index - 1,
                                "total_features": len(state.features),
                                "cost_usd": result.cost_usd,
                                "duration_ms": result.duration_ms,
                            }
                        )
                else:
                    state.mark_feature_failed(result.output)
                    console.print(f"[red]✗ Failed: {feature.name}[/red]")
                    console.print(f"[red]Error: {result.output}[/red]")

                    # Emit feature.failed event
                    if event_logger:
                        event_logger.emit(
                            workflow_id=state.workflow_id,
                            event_type=EventType.FEATURE_FAILED,
                            data={
                                "feature_name": feature.name,
                                "feature_index": state.current_feature_index,
                                "error": result.output[:500] if result.output else "Unknown error",
                            }
                        )

                    # Decide whether to continue or stop
                    # For now, stop on first failure
                    console.print("[yellow]Stopping due to feature failure[/yellow]")
                    break

            except Exception as e:
                state.mark_feature_failed(str(e))
                console.print(f"[red]✗ Exception during feature execution: {e}[/red]")
                break

            # Save state after each iteration
            state.iteration_count += 1
            state.save(project_root)

            # Delay before next iteration
            if state.get_next_feature() is not None and not interrupted:
                await anyio.sleep(delay_seconds)

    # Final state save
    state.save(project_root)

    # Summary
    console.print()
    summary = state.get_summary()
    status_color = "green" if state.is_complete() else "yellow" if state.is_failed() else "blue"

    console.print(
        Panel(
            f"[bold]Workflow Summary[/bold]\n\n"
            f"Features Completed: [cyan]{summary['completed_features']}/{summary['total_features']}[/cyan]\n"
            f"Features Failed: [cyan]{summary['failed_features']}[/cyan]\n"
            f"Progress: [cyan]{summary['progress_percentage']:.1f}%[/cyan]\n"
            f"Iterations: [cyan]{summary['iteration_count']}[/cyan]\n"
            f"Total Cost: [cyan]${summary['total_cost_usd']:.4f}[/cyan]\n"
            f"Total Duration: [cyan]{summary['total_duration_ms'] / 1000:.1f}s[/cyan]\n"
            f"Status: [bold {status_color}]{'COMPLETE' if state.is_complete() else 'FAILED' if state.is_failed() else 'INCOMPLETE'}[/bold {status_color}]",
            border_style=status_color,
        )
    )

    return state


async def initialize_workflow(
    workflow_id: str,
    workflow_name: str,
    workflow_type: str,
    features: list[tuple[str, str, Optional[str]]],
    project_root: Path,
    max_iterations: int = 50,
) -> WorkflowState:
    """Initialize a new auto-continue workflow.

    Creates a WorkflowState with the given features and saves it to disk.

    Args:
        workflow_id: Unique workflow identifier
        workflow_name: Human-readable workflow name
        workflow_type: Type of workflow (chore, feature, bug, etc.)
        features: List of (name, description, test_file) tuples
        project_root: Project root directory
        max_iterations: Maximum iterations allowed (default: 50)

    Returns:
        Initialized WorkflowState
    """
    state = WorkflowState(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        workflow_type=workflow_type,
        max_iterations=max_iterations,
    )

    # Add features
    for name, description, test_file in features:
        state.add_feature(name, description, test_file)

    # Save initial state
    state.save(project_root)

    console.print(
        f"[green]✓ Initialized workflow with {len(features)} features[/green]"
    )

    return state


def resume_workflow(workflow_id: str, project_root: Path) -> WorkflowState:
    """Resume an existing auto-continue workflow.

    Loads state from disk and continues from where it left off.

    Args:
        workflow_id: Workflow to resume
        project_root: Project root directory

    Returns:
        Loaded WorkflowState

    Raises:
        AutoContinueError: If workflow state cannot be loaded
    """
    try:
        state = WorkflowState.load(workflow_id, project_root)
        console.print(
            f"[green]✓ Resumed workflow {workflow_id}[/green] "
            f"({state.progress_percentage:.1f}% complete)"
        )
        return state
    except FileNotFoundError as e:
        raise AutoContinueError(f"Workflow {workflow_id} not found") from e
