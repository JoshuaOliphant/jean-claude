# Auto-Continue Workflow Support

Jean Claude now supports autonomous, long-running workflows that execute until completion using the auto-continue pattern from Anthropic's autonomous coding agent quickstart.

## Overview

Auto-continue workflows enable:

- **Long-running execution**: Workflows run until all features are complete, not just a fixed number of turns
- **Fresh context per iteration**: Each iteration starts with clean state, bypassing context window limits
- **Verification-first**: Tests run before each new feature to prevent regression
- **Graceful interruption**: SIGINT/SIGTERM handling allows safe stopping mid-workflow
- **State persistence**: Full state saved after every iteration for resumability

## Architecture

### Two-Tier Pattern

```
┌─────────────────────────────────────────┐
│   Planning Agent (Initial)              │
│   - Analyzes requirements               │
│   - Creates feature list                │
│   - Saves state.json                    │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│   Auto-Continue Loop                    │
│   While not complete:                   │
│     1. Read state.json                  │
│     2. Verify existing tests            │
│     3. Execute one feature              │
│     4. Update state.json                │
│     5. Sleep (delay)                    │
└─────────────────────────────────────────┘
```

### State Machine

State is persisted in `agents/{workflow_id}/state.json`:

```json
{
  "workflow_id": "abc123",
  "workflow_type": "feature",
  "features": [
    {
      "name": "User Authentication",
      "description": "Implement JWT auth",
      "status": "completed",
      "test_file": "tests/test_auth.py",
      "tests_passing": true
    },
    {
      "name": "User Profile",
      "description": "Add profile endpoints",
      "status": "in_progress",
      "test_file": "tests/test_profile.py",
      "tests_passing": false
    }
  ],
  "current_feature_index": 1,
  "iteration_count": 5,
  "max_iterations": 50,
  "total_cost_usd": 0.25,
  "total_duration_ms": 15000
}
```

## Usage

### CLI Command

```bash
# Run workflow with auto-continue
jc run feature "Build user authentication system" --auto-continue

# With custom settings
jc run chore "Refactor API" \
  --auto-continue \
  --max-iterations 100 \
  --delay 5.0 \
  --model opus
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--auto-continue` | Enable auto-continue mode | `false` |
| `--max-iterations` | Safety limit for iterations | `50` |
| `--delay` | Seconds between iterations | `2.0` |
| `--skip-verify` | Skip test verification | `false` |
| `--model` | Claude model (sonnet/opus/haiku) | `sonnet` |

### Programmatic API

```python
from pathlib import Path
from jean_claude.orchestration import initialize_workflow, run_auto_continue

# Initialize workflow
state = await initialize_workflow(
    workflow_id="my-workflow",
    workflow_name="My Feature",
    workflow_type="feature",
    features=[
        ("Auth", "Implement authentication", "tests/test_auth.py"),
        ("Profile", "User profiles", "tests/test_profile.py"),
    ],
    project_root=Path.cwd(),
    max_iterations=50,
)

# Run auto-continue loop
final_state = await run_auto_continue(
    state=state,
    project_root=Path.cwd(),
    max_iterations=50,
    delay_seconds=2.0,
    model="sonnet",
)

# Check results
if final_state.is_complete():
    print("✓ All features completed!")
else:
    print(f"✗ Stopped at {final_state.progress_percentage}%")
```

## Workflow Lifecycle

### 1. Initialization

The planning agent creates a feature list:

```python
state = WorkflowState(
    workflow_id="abc123",
    features=[...],
    max_iterations=50,
)
state.save(project_root)
```

### 2. Iteration Loop

Each iteration:

1. **Load State**: Read `state.json` from disk
2. **Verify Tests** (if enabled): Run existing tests, fail if broken
3. **Get Next Feature**: `state.get_next_feature()`
4. **Execute Feature**: Run agent with feature-specific prompt
5. **Update State**: Mark complete/failed, save to disk
6. **Delay**: Sleep before next iteration

### 3. Termination

Loop ends when:
- ✅ All features complete (`state.is_complete()`)
- ❌ A feature fails (`state.is_failed()`)
- 🛑 Max iterations reached
- ⚠️  User interrupt (SIGINT/SIGTERM)

### 4. Resumption

Resume from where it left off:

```python
from jean_claude.orchestration import resume_workflow

state = resume_workflow("abc123", project_root)
final_state = await run_auto_continue(state, project_root)
```

## Safety Features

### 1. Max Iteration Limit

Prevents infinite loops with configurable limit (default: 50).

### 2. Verification-First

Before each feature, runs all existing tests:

```python
if verify_first and state.should_verify():
    result = run_verification(state, project_root)
    if not result.passed:
        console.print("Tests failed! Fix before continuing.")
        break
```

### 3. Signal Handling

Gracefully handles interrupts:

```python
def signal_handler(signum, frame):
    interrupted = True
    console.print("Interrupt received. Finishing current iteration...")
```

Current iteration completes, state is saved, then exits cleanly.

### 4. State Persistence

State saved after **every iteration**:

```python
state.iteration_count += 1
state.save(project_root)  # Always save!
```

Even if process crashes, can resume from last saved state.

## Observability

### Output Structure

```
agents/{workflow_id}/
├── state.json                    # Workflow state
└── auto_continue/
    ├── iteration_000/
    │   ├── cc_raw_output.jsonl
    │   ├── cc_raw_output.json
    │   └── cc_final_object.json
    ├── iteration_001/
    └── iteration_002/
```

### Progress Tracking

Real-time progress displayed:

```
╭──────────────────────────────────────────────╮
│ Starting Auto-Continue Workflow              │
│                                              │
│ Workflow ID: abc123                          │
│ Total Features: 5                            │
│ Max Iterations: 50                           │
╰──────────────────────────────────────────────╯

✓ Completed: Feature 1 (20.0% done)
✓ Completed: Feature 2 (40.0% done)
✓ Completed: Feature 3 (60.0% done)
```

### Summary Report

Final summary with metrics:

```
╭──────────────────────────────────────────────╮
│ Workflow Summary                             │
│                                              │
│ Features Completed: 5/5                      │
│ Progress: 100.0%                             │
│ Iterations: 5                                │
│ Total Cost: $0.2500                          │
│ Duration: 12.5s                              │
│ Status: COMPLETE                             │
╰──────────────────────────────────────────────╯
```

## Best Practices

### 1. Feature Granularity

Break work into **small, testable features**:

✅ Good:
- "Add login endpoint"
- "Add logout endpoint"
- "Add JWT middleware"

❌ Too large:
- "Implement entire authentication system"

### 2. Test-Driven Development

Each feature should:
1. Define tests first
2. Implement feature
3. Verify tests pass

### 3. Verification Enabled

Always verify unless you have a reason not to:

```bash
# ✅ Default - verification enabled
jc run feature "..." --auto-continue

# ⚠️  Only skip if no tests exist yet
jc run feature "..." --auto-continue --skip-verify
```

### 4. Reasonable Iterations

Set `max_iterations` based on feature count:

- **Small tasks (1-5 features)**: `--max-iterations 10`
- **Medium tasks (5-20 features)**: `--max-iterations 50` (default)
- **Large tasks (20+ features)**: `--max-iterations 100`

### 5. Appropriate Model Selection

| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| Haiku | Simple features, well-defined | Fast | Low |
| Sonnet | Most tasks, balanced quality | Medium | Medium |
| Opus | Complex architecture, critical | Slow | High |

## Examples

### Example 1: Simple Chore

```bash
jc run chore "Add logging to API endpoints" --auto-continue
```

Features automatically broken down:
1. Add logging middleware
2. Update endpoints to use logger
3. Add log rotation config
4. Update tests

### Example 2: Large Feature

```bash
jc run feature "Implement user management system" \
  --auto-continue \
  --max-iterations 100 \
  --model opus
```

Planning creates 20+ features, auto-continue executes them all.

### Example 3: Resume After Interrupt

```bash
# Start workflow
jc run feature "..." --auto-continue
# ... Press Ctrl+C after 3 features ...

# Resume later
jc run --resume abc123
```

### Example 4: Custom Delay for Rate Limits

```bash
# Slower execution to respect API rate limits
jc run feature "..." --auto-continue --delay 10.0
```

## Troubleshooting

### Workflow Stuck in Loop

**Symptom**: Same feature fails repeatedly

**Solution**:
1. Check `agents/{id}/auto_continue/iteration_XXX/` outputs
2. Review failure reason
3. Manually fix issue
4. Update `state.json` to reset feature status
5. Resume workflow

### Tests Keep Failing

**Symptom**: Verification fails every iteration

**Solution**:
1. Fix tests manually
2. Or use `--skip-verify` temporarily
3. Resume workflow

### Max Iterations Reached

**Symptom**: Workflow stops before completion

**Solution**:
```python
# Resume with higher limit
state = resume_workflow("abc123", Path.cwd())
state.max_iterations = 100
state.save(Path.cwd())

await run_auto_continue(state, Path.cwd(), max_iterations=100)
```

## Testing

Comprehensive test suite with 20 tests covering:

- ✅ Prompt generation
- ✅ Workflow initialization
- ✅ Workflow resumption
- ✅ Single feature execution
- ✅ Multiple feature execution
- ✅ Failure handling
- ✅ Max iterations respect
- ✅ State persistence
- ✅ Progress tracking
- ✅ Session tracking
- ✅ Cost/duration tracking
- ✅ Interrupt/resume lifecycle
- ✅ Empty workflow handling

Run tests:

```bash
# Unit tests
uv run pytest tests/orchestration/test_auto_continue.py

# Integration tests
uv run pytest tests/orchestration/test_auto_continue_integration.py

# All orchestration tests
uv run pytest tests/orchestration/
```

## Demo

See it in action:

```bash
uv run python demo_auto_continue.py
```

This runs a mock workflow with 4 features, showing:
- Initialization
- Progress updates
- Verification steps
- Final summary
- State persistence

## References

- [Autonomous Agent Patterns](./autonomous-agent-patterns.md)
- [Claude Agent SDK Documentation](https://docs.anthropic.com/en/docs/claude-agent-sdk)
- [WorkflowState API](../src/jean_claude/core/state.py)
- [Auto-Continue Orchestrator](../src/jean_claude/orchestration/auto_continue.py)
