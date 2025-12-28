# ABOUTME: Two-agent orchestration pattern from Anthropic's autonomous coding quickstart
# ABOUTME: Initializer agent plans features, coder agent executes them iteratively

"""Two-agent orchestration pattern for complex workflows.

This module implements the two-agent pattern from Anthropic's autonomous
coding agent quickstart:

1. **Initializer Agent** (Opus) - Runs once at start:
   - Analyzes entire project scope
   - Creates comprehensive feature list
   - Defines all test cases upfront
   - Saves to WorkflowState

2. **Coder Agent** (Sonnet) - Runs in loop:
   - Reads WorkflowState each session
   - Implements ONE feature at a time
   - Updates state after completion
   - Fresh context each iteration

Key Benefits:
    - Context window efficiency (reset per feature)
    - Clear separation of planning vs execution
    - State file as shared memory between agents
    - Better model selection (Opus plans, Sonnet codes)

Pattern Reference:
    docs/autonomous-agent-patterns.md - Section: Two-Agent Pattern
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from jean_claude.core.state import WorkflowState, Feature
from jean_claude.core.agent import PromptRequest, ExecutionResult, _execute_prompt_sdk_async
from jean_claude.core.events import EventLogger
from jean_claude.orchestration.auto_continue import run_auto_continue


console = Console()


# Initializer prompt template
INITIALIZER_PROMPT = """You are an initializer agent for Jean Claude workflows.

Your job is to analyze the task and create a comprehensive feature breakdown.

## TASK DESCRIPTION

{description}

## YOUR MISSION

Break this task into small, focused, testable features that can be implemented
independently.

## OUTPUT FORMAT

You MUST output ONLY valid JSON in this exact structure:

```json
{{
  "features": [
    {{
      "name": "feature-name",
      "description": "Detailed description of what to implement",
      "test_file": "tests/test_feature.py"
    }}
  ]
}}
```

## CRITICAL REQUIREMENTS

1. **Small Features**: Each feature should be MAX 100 lines of code
2. **Independent**: Features should be self-contained when possible
3. **Testable**: Every feature MUST have a test file specified
4. **Ordered**: List features in dependency order (implement dependencies first)
5. **Comprehensive**: Cover ALL aspects of the task
6. **Test-First**: Think about how to test each feature

## GUIDELINES

- Break large features into smaller chunks
- Each feature should solve ONE specific problem
- Test files should follow pytest conventions
- Descriptions should be clear enough for another agent to implement
- Don't create features that depend on unimplemented external systems
- Aim for 5-15 features for most tasks

## EXAMPLES

Good feature breakdown:
```json
{{
  "features": [
    {{
      "name": "basic-data-model",
      "description": "Create User model with SQLAlchemy including fields: id, username, email, created_at",
      "test_file": "tests/test_user_model.py"
    }},
    {{
      "name": "user-validation",
      "description": "Add email validation and username uniqueness constraints to User model",
      "test_file": "tests/test_user_validation.py"
    }},
    {{
      "name": "user-repository",
      "description": "Implement UserRepository with CRUD operations: create, get_by_id, get_by_email, update, delete",
      "test_file": "tests/test_user_repository.py"
    }}
  ]
}}
```

Bad feature (too large):
```json
{{
  "features": [
    {{
      "name": "complete-user-system",
      "description": "Build entire user authentication system with login, registration, password reset, email verification, and OAuth",
      "test_file": "tests/test_auth.py"
    }}
  ]
}}
```

## NOW ANALYZE THE TASK

Analyze the task description above and create a feature breakdown.

OUTPUT ONLY THE JSON. NO ADDITIONAL TEXT BEFORE OR AFTER THE JSON.
"""


async def run_initializer(
    description: str,
    project_root: Path,
    workflow_id: Optional[str] = None,
    model: str = "opus",
) -> WorkflowState:
    """Run initializer agent to create feature list.

    The initializer analyzes the task and creates a comprehensive
    feature breakdown. It runs ONCE at the start and defines all
    the work to be done.

    Args:
        description: Task description to break down
        project_root: Project root directory
        workflow_id: Optional workflow ID (generates one if not provided)
        model: Model to use for planning (default: opus for better planning)

    Returns:
        WorkflowState with features populated

    Raises:
        ValueError: If initializer output is invalid JSON or malformed
    """
    if workflow_id is None:
        workflow_id = f"two-agent-{uuid.uuid4().hex[:8]}"

    console.print()
    console.print(
        Panel(
            f"[bold blue]Initializer Agent[/bold blue]\n\n"
            f"Analyzing task and creating feature breakdown...\n\n"
            f"Task: [cyan]{description[:100]}{'...' if len(description) > 100 else ''}[/cyan]\n"
            f"Model: [cyan]{model}[/cyan]\n"
            f"Workflow ID: [cyan]{workflow_id}[/cyan]",
            border_style="blue",
        )
    )
    console.print()

    # Build prompt
    prompt = INITIALIZER_PROMPT.format(description=description)

    # Execute initializer
    output_dir = project_root / "agents" / workflow_id / "initializer"
    output_dir.mkdir(parents=True, exist_ok=True)

    request = PromptRequest(
        prompt=prompt,
        model=model,
        working_dir=project_root,
        output_dir=output_dir,
        dangerously_skip_permissions=True,
    )

    console.print("[blue]Running initializer agent...[/blue]")
    result: ExecutionResult = await _execute_prompt_sdk_async(request, max_retries=3)

    if not result.success:
        raise ValueError(f"Initializer failed: {result.output}")

    # Parse JSON response
    output = result.output.strip()

    # Extract JSON from markdown code blocks if present
    if "```json" in output:
        start = output.find("```json") + 7
        end = output.find("```", start)
        output = output[start:end].strip()
    elif "```" in output:
        start = output.find("```") + 3
        end = output.find("```", start)
        output = output[start:end].strip()

    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        console.print(f"[red]Failed to parse initializer output as JSON[/red]")
        console.print(f"[yellow]Output:[/yellow]")
        console.print(output)
        raise ValueError(f"Initializer output is not valid JSON: {e}") from e

    # Validate structure
    if "features" not in data:
        raise ValueError("Initializer output missing 'features' key")

    if not isinstance(data["features"], list):
        raise ValueError("'features' must be a list")

    if len(data["features"]) == 0:
        raise ValueError("Feature list is empty")

    # Load existing WorkflowState or create new one
    state_path = project_root / "agents" / workflow_id / "state.json"
    if state_path.exists():
        # Preserve existing state (phase, beads_task_id, etc.)
        state = WorkflowState.load_from_file(state_path)
        # Update with new planning data
        state.workflow_name = description[:100]
        state.max_iterations = len(data["features"]) * 3
        # Clear old features if re-planning
        state.features = []
        state.current_feature_index = 0
    else:
        # Create new WorkflowState
        state = WorkflowState(
            workflow_id=workflow_id,
            workflow_name=description[:100],
            workflow_type="two-agent",
            max_iterations=len(data["features"]) * 3,  # Allow 3 attempts per feature
        )

    # Add features
    for i, feature_data in enumerate(data["features"]):
        if not isinstance(feature_data, dict):
            raise ValueError(f"Feature {i} is not a dictionary")

        name = feature_data.get("name")
        desc = feature_data.get("description")
        test_file = feature_data.get("test_file")

        if not name:
            raise ValueError(f"Feature {i} missing 'name'")
        if not desc:
            raise ValueError(f"Feature {i} missing 'description'")

        state.add_feature(name=name, description=desc, test_file=test_file)

    # Save state
    state.save(project_root)

    # Display feature list
    console.print()
    console.print("[green]✓ Feature breakdown complete![/green]")
    console.print()
    console.print(Panel("[bold]Feature List[/bold]", border_style="green"))

    for i, feature in enumerate(state.features, 1):
        console.print(
            f"[cyan]{i}.[/cyan] [bold]{feature.name}[/bold]\n"
            f"   {feature.description}\n"
            f"   [dim]Test: {feature.test_file or 'N/A'}[/dim]"
        )
        console.print()

    console.print(
        f"[bold green]Total Features: {len(state.features)}[/bold green]\n"
        f"[dim]Estimated iterations: {state.max_iterations}[/dim]"
    )
    console.print()

    return state


async def run_two_agent_workflow(
    description: str,
    project_root: Path,
    workflow_id: Optional[str] = None,
    initializer_model: str = "opus",
    coder_model: str = "sonnet",
    max_iterations: Optional[int] = None,
    auto_confirm: bool = False,
    event_logger: Optional["EventLogger"] = None,
) -> WorkflowState:
    """Run complete two-agent workflow.

    This orchestrates both agents:
    1. Initializer creates feature list
    2. User confirms (unless auto_confirm=True)
    3. Coder implements features one by one

    Args:
        description: Task description
        project_root: Project root directory
        workflow_id: Optional workflow ID
        initializer_model: Model for planning (default: opus)
        coder_model: Model for coding (default: sonnet)
        max_iterations: Max iterations for coder (default: features * 3)
        auto_confirm: Skip user confirmation (default: False)

    Returns:
        Final WorkflowState

    Raises:
        ValueError: If initializer fails
        KeyboardInterrupt: If user cancels at confirmation
    """
    # Phase 1: Initializer
    state = await run_initializer(
        description=description,
        project_root=project_root,
        workflow_id=workflow_id,
        model=initializer_model,
    )

    # User confirmation
    if not auto_confirm:
        console.print()
        confirmed = Confirm.ask(
            "[yellow]Proceed with implementation?[/yellow]",
            default=True,
        )

        if not confirmed:
            console.print("[yellow]Workflow cancelled by user[/yellow]")
            raise KeyboardInterrupt("User cancelled workflow")

    # Phase 2: Coder (auto-continue loop)
    console.print()
    console.print(
        Panel(
            f"[bold blue]Coder Agent[/bold blue]\n\n"
            f"Implementing {len(state.features)} features...\n\n"
            f"Model: [cyan]{coder_model}[/cyan]\n"
            f"Workflow ID: [cyan]{state.workflow_id}[/cyan]",
            border_style="blue",
        )
    )
    console.print()

    final_state = await run_auto_continue(
        state=state,
        project_root=project_root,
        max_iterations=max_iterations,
        model=coder_model,
        verify_first=True,
        event_logger=event_logger,
    )

    return final_state
