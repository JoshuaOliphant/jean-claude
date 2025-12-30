# Worktree Integration: Monitoring & Dashboard Impact

## Critical Problem: Data Visibility

When workflows run in worktrees, where does their data go?

### The Issue

```
Main Repo                         Worktree (trees/beads-y97/)
├── agents/                       ├── agents/              ← SEPARATE!
│   └── beads-abc123/             │   └── beads-y97/
│       ├── state.json            │       ├── state.json
│       ├── logs/                 │       ├── logs/
│       └── events.jsonl          │       └── events.jsonl
└── dashboard
    (reads from main repo)        (workflow writes here)
                                   ↑
                                   Dashboard can't see this!
```

**Problem**: If workflows write to their worktree's `agents/` directory, the dashboard (running in main repo) won't see them.

## Solution: Centralized State Directory

**All workflows write to the MAIN REPO's `agents/` directory**, regardless of where they execute.

```
Main Repo                         Worktree (trees/beads-y97/)
├── agents/          ←────────────── Workflows write here
│   ├── beads-abc123/               (even from worktree)
│   ├── beads-y97/   ←────┐
│   └── beads-7gq/        │
└── dashboard             │
    (reads from here) ────┘         Execution happens here,
                                    but state goes to main repo
```

### Why This Works

✅ **Single Source of Truth** - All workflow data in one place
✅ **Dashboard Visibility** - Can see all workflows, running or not
✅ **Parallel Monitoring** - Monitor multiple worktree workflows simultaneously
✅ **Persistent Across Crashes** - State survives worktree deletion
✅ **Log Aggregation** - All logs in one place

---

## Architecture Changes

### 1. Separation of Concerns

We need to track TWO roots:

```python
class WorkflowState(BaseModel):
    # ... existing fields ...

    # NEW: Track both roots
    main_repo_root: Path | None = None      # Where agents/ lives
    worktree_path: Path | None = None       # Where code executes

    def get_state_root(self) -> Path:
        """Get root for state/logs (always main repo)."""
        return self.main_repo_root or Path.cwd()

    def get_execution_root(self) -> Path:
        """Get root for code execution (worktree or main)."""
        return self.worktree_path or self.main_repo_root or Path.cwd()

    def save(self, state_root: Path | None = None) -> None:
        """Save to main repo's agents/ directory."""
        root = state_root or self.get_state_root()
        state_dir = root / "agents" / self.workflow_id
        # ... save logic ...
```

### 2. Path Resolution Strategy

```python
# In run_two_agent_workflow()
async def run_two_agent_workflow(
    description: str,
    project_root: Path,  # Main repo root
    workflow_id: str,
    # ...
    use_worktree: bool = True,
) -> WorkflowState:
    """Run workflow with proper path separation."""

    # Main repo root (where agents/ directory lives)
    main_repo_root = project_root

    # Execution root (where code runs)
    if use_worktree:
        worktree_path = create_workflow_worktree(workflow_id, repo_root=main_repo_root)
        execution_root = worktree_path
    else:
        execution_root = main_repo_root

    # Create state with both roots
    state = WorkflowState(
        workflow_id=workflow_id,
        main_repo_root=main_repo_root,      # For agents/
        worktree_path=worktree_path if use_worktree else None,  # For code
        # ...
    )

    # Save to main repo (not worktree!)
    state.save(main_repo_root)

    # Execute in worktree
    # ... run agents in execution_root ...

    # Logs/events write to main repo
    log_file = main_repo_root / "agents" / workflow_id / "logs" / f"{session_id}.log"
    event_file = main_repo_root / "agents" / workflow_id / "events.jsonl"
```

### 3. Event Logger Updates

```python
# src/jean_claude/core/events.py
class EventLogger:
    def __init__(self, project_root: Path):
        """Initialize event logger.

        Args:
            project_root: Main repo root (where agents/ directory lives)
        """
        self.project_root = project_root  # Always main repo, not worktree

    def emit(self, workflow_id: str, event_type: str, data: dict) -> None:
        """Emit event to main repo's agents/ directory."""
        events_file = self.project_root / "agents" / workflow_id / "events.jsonl"
        # ... write event ...
```

---

## Dashboard Enhancements

### 1. Worktree Status Display

Add worktree info to dashboard:

```python
# In dashboard/app.py
def get_workflow_state(workflow_id: str) -> dict | None:
    """Get workflow state with worktree info."""
    state_file = project_root / "agents" / workflow_id / "state.json"

    if state_file.exists():
        state = json.load(state_file.open())

        # Enrich with worktree status
        if state.get("worktree_path"):
            worktree_path = Path(state["worktree_path"])
            state["worktree_active"] = worktree_path.exists()
            state["worktree_branch"] = state.get("worktree_branch")

        return state
    return None
```

### 2. Dashboard UI Updates

```html
<!-- In templates/dashboard.html -->
<div class="workflow-card">
  <h3>{{ workflow.workflow_name }}</h3>
  <p>Phase: {{ workflow.phase }}</p>
  <p>Progress: {{ workflow.current_feature_index }}/{{ workflow.features|length }}</p>

  <!-- NEW: Worktree info -->
  {% if workflow.worktree_path %}
  <div class="worktree-info">
    <span class="badge badge-blue">
      <svg>...</svg> Isolated Worktree
    </span>
    <p class="text-xs">
      Branch: <code>{{ workflow.worktree_branch }}</code>
    </p>
    {% if workflow.worktree_active %}
    <p class="text-xs text-green-600">
      ✓ Worktree active at {{ workflow.worktree_path }}
    </p>
    {% else %}
    <p class="text-xs text-yellow-600">
      ⚠ Worktree removed (workflow in main repo)
    </p>
    {% endif %}
  </div>
  {% endif %}
</div>
```

### 3. Real-time Updates

SSE streaming continues to work because it reads from main repo:

```python
# In dashboard/app.py
async def workflow_updates() -> AsyncGenerator[str, None]:
    """Stream workflow updates from main repo."""
    while True:
        # Read from main repo's agents/ directory
        workflows = get_all_workflows()  # Uses project_root / "agents"

        # Works for both worktree and non-worktree workflows
        yield {
            "event": "workflow_update",
            "data": json.dumps(workflows)
        }

        await asyncio.sleep(1)
```

---

## Status Command Enhancements

### Current Output
```bash
$ jc status
Workflow: beads-jean_claude-y97
Phase: implementing
Progress: 4/7 features (57%)
```

### Enhanced with Worktree Info
```bash
$ jc status
Workflow: beads-jean_claude-y97
Phase: implementing
Progress: 4/7 features (57%)
Worktree: trees/beads-jean_claude-y97/ (branch: beads/jean_claude-y97) ✓
Last updated: 2 minutes ago
```

### Implementation

```python
# src/jean_claude/cli/commands/status.py
def status(workflow_id: str | None = None):
    """Show workflow status."""
    state = WorkflowState.load(workflow_id, project_root)

    console.print(f"Workflow: {state.workflow_id}")
    console.print(f"Phase: {state.phase}")
    console.print(f"Progress: {state.current_feature_index}/{len(state.features)} features")

    # NEW: Worktree info
    if state.worktree_path:
        if state.worktree_path.exists():
            console.print(f"Worktree: {state.worktree_path} (branch: {state.worktree_branch}) ✓")
        else:
            console.print(f"[yellow]Worktree removed (was: {state.worktree_path})[/yellow]")
```

---

## Logs Command Enhancements

### Current Behavior
```bash
$ jc logs beads-jean_claude-y97
# Shows logs from agents/beads-jean_claude-y97/logs/
```

### With Worktrees (No Change Needed!)
```bash
$ jc logs beads-jean_claude-y97
# Still works - logs are in main repo's agents/
# Doesn't matter if workflow ran in worktree
```

The logs command **already works** because logs are written to main repo.

---

## Multi-Workflow Monitoring

Dashboard can now monitor multiple parallel workflows:

```
Dashboard View (http://localhost:8765)

┌─────────────────────────────────────────────────────────┐
│ Active Workflows (3 running)                            │
├─────────────────────────────────────────────────────────┤
│ beads-jean_claude-y97                                   │
│ Phase: implementing                                     │
│ Progress: 4/7 (57%)                                     │
│ 🌲 Worktree: trees/beads-jean_claude-y97/ ✓            │
│                                                         │
│ beads-jean_claude-7gq                                   │
│ Phase: implementing                                     │
│ Progress: 2/9 (22%)                                     │
│ 🌲 Worktree: trees/beads-jean_claude-7gq/ ✓            │
│                                                         │
│ beads-jean_claude-400                                   │
│ Phase: planning                                         │
│ Progress: 0/14 (0%)                                     │
│ 🌲 Worktree: trees/beads-jean_claude-400/ ✓            │
└─────────────────────────────────────────────────────────┘

Updates in real-time via SSE
```

### Benefits

✅ See all workflows in one place
✅ Monitor progress across parallel workflows
✅ Identify which workflows are isolated
✅ Track resource usage (3 worktrees = 3x disk space)

---

## New Monitoring Features

### 1. Worktree Health Check

```python
# src/jean_claude/cli/commands/worktrees.py
@worktrees.command("health")
def worktree_health():
    """Check health of all worktrees."""
    from jean_claude.integrations.worktree import list_workflow_worktrees

    worktrees = list_workflow_worktrees()

    for wt in worktrees:
        state = WorkflowState.load(wt.workflow_id, Path.cwd())

        # Check consistency
        if state.worktree_path != wt.path:
            console.print(f"[yellow]⚠ Mismatch:[/yellow] {wt.workflow_id}")
            console.print(f"  State says: {state.worktree_path}")
            console.print(f"  Actual: {wt.path}")

        # Check if orphaned
        if wt.exists and not state_file.exists():
            console.print(f"[red]✗ Orphaned:[/red] {wt.workflow_id}")
            console.print(f"  Worktree exists but no state file")

        # Check if stale
        age = datetime.now() - state.updated_at
        if age.days > 7:
            console.print(f"[yellow]⚠ Stale:[/yellow] {wt.workflow_id}")
            console.print(f"  Last updated {age.days} days ago")
```

### 2. Resource Usage Monitoring

```python
@worktrees.command("usage")
def worktree_usage():
    """Show disk usage of worktrees."""
    import shutil

    trees_dir = Path.cwd() / "trees"
    if not trees_dir.exists():
        console.print("No worktrees found")
        return

    total_size = 0
    table = Table(title="Worktree Disk Usage")
    table.add_column("Workflow")
    table.add_column("Size", justify="right")
    table.add_column("Status")

    for worktree_dir in trees_dir.iterdir():
        if worktree_dir.is_dir():
            size = sum(f.stat().st_size for f in worktree_dir.rglob('*') if f.is_file())
            total_size += size

            state = WorkflowState.load(worktree_dir.name, Path.cwd())
            status = f"[green]{state.phase}[/green]" if state else "[yellow]unknown[/yellow]"

            table.add_row(
                worktree_dir.name,
                f"{size / 1024 / 1024:.1f} MB",
                status
            )

    console.print(table)
    console.print(f"\nTotal: {total_size / 1024 / 1024:.1f} MB")
```

### 3. Parallel Workflow View

```bash
$ jc status --all
Active Workflows:

  beads-jean_claude-y97  [implementing]  4/7 (57%)  🌲 isolated
  beads-jean_claude-7gq  [implementing]  2/9 (22%)  🌲 isolated
  beads-jean_claude-400  [planning]      0/14 (0%)  🌲 isolated

Completed Today: 3
Failed Today: 0
Resource Usage: 150 MB (3 worktrees)
```

---

## Event Stream Integration

Events are written to main repo, so SSE streaming works seamlessly:

```javascript
// Dashboard frontend
const eventSource = new EventSource('/api/workflows/stream');

eventSource.addEventListener('workflow_update', (event) => {
  const workflows = JSON.parse(event.data);

  // Update UI for all workflows
  workflows.forEach(workflow => {
    updateWorkflowCard(workflow);

    // Highlight worktree-based workflows
    if (workflow.worktree_path) {
      addWorktreeIndicator(workflow);
    }
  });
});
```

---

## Cleanup Integration

### Automatic Cleanup on Success

```python
# In run_two_agent_workflow()
if final_state.is_complete() and use_worktree:
    console.print("[bold blue]Merging to main and cleaning up...[/bold blue]")

    # Merge changes
    merge_workflow_to_main(workflow_id, delete_after_merge=True)

    # Update state to reflect worktree removal
    final_state.worktree_path = None
    final_state.worktree_branch = None
    final_state.save(main_repo_root)

    console.print("[green]✓[/green] Changes merged, worktree cleaned up")
```

### Manual Cleanup

```bash
# Clean up all completed workflows
$ jc worktrees cleanup
Cleaning up completed workflow: beads-jean_claude-y97
Cleaning up completed workflow: beads-jean_claude-7gq
✓ Cleaned up 2 worktree(s)

# Dashboard updates automatically (state.json updated)
```

---

## Migration Considerations

### Legacy Workflows (No Worktree)

```python
def load_workflow(workflow_id: str) -> WorkflowState:
    """Load workflow, handling both legacy and worktree-based."""
    state = WorkflowState.load(workflow_id, Path.cwd())

    # Legacy workflow (no worktree fields)
    if not hasattr(state, 'worktree_path'):
        state.worktree_path = None
        state.main_repo_root = Path.cwd()

    return state
```

Dashboard shows:
```
Workflow: beads-jean_claude-old
Phase: complete
Progress: 10/10 (100%)
⚠ Legacy workflow (no isolation)
```

---

## Testing Strategy

### Dashboard Tests

```python
# tests/dashboard/test_worktree_integration.py
def test_dashboard_shows_worktree_workflows():
    """Test dashboard displays worktree-based workflows."""
    # Create workflow with worktree
    state = WorkflowState(
        workflow_id="test-wt",
        worktree_path=Path("/tmp/trees/test-wt"),
        worktree_branch="beads/test",
        # ...
    )
    state.save(project_root)

    # Dashboard should include worktree info
    response = client.get("/api/workflows")
    workflows = response.json()

    assert workflows[0]["worktree_path"] == "/tmp/trees/test-wt"
    assert workflows[0]["worktree_active"] is True


def test_dashboard_handles_removed_worktree():
    """Test dashboard gracefully handles removed worktree."""
    state = WorkflowState(
        workflow_id="test-wt",
        worktree_path=Path("/tmp/nonexistent"),  # Doesn't exist
        # ...
    )
    state.save(project_root)

    response = client.get("/api/workflows")
    workflows = response.json()

    assert workflows[0]["worktree_active"] is False
```

### Monitoring Tests

```python
def test_status_shows_worktree_info():
    """Test jc status displays worktree information."""
    result = cli_runner.invoke(status, ["test-wt"])

    assert "Worktree:" in result.output
    assert "beads/test" in result.output


def test_logs_work_with_worktree():
    """Test jc logs works for worktree-based workflows."""
    # Logs written to main repo
    log_file = project_root / "agents" / "test-wt" / "logs" / "session.log"
    log_file.parent.mkdir(parents=True)
    log_file.write_text("Test log entry")

    # Should work even if worktree exists
    result = cli_runner.invoke(logs, ["test-wt"])
    assert "Test log entry" in result.output
```

---

## Summary: Key Architectural Decisions

| Concern | Decision | Rationale |
|---------|----------|-----------|
| **State storage** | Main repo `agents/` | Single source of truth, survives worktree deletion |
| **Log storage** | Main repo `agents/` | Dashboard visibility, aggregation |
| **Event storage** | Main repo `agents/` | Real-time monitoring works |
| **Code execution** | Worktree `trees/` | Isolation for parallel workflows |
| **Dashboard reads** | Main repo `agents/` | Can see all workflows |
| **State tracking** | Both roots tracked | `main_repo_root` vs `worktree_path` |
| **Cleanup** | Auto on success | Keep failed for debugging |

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ Worktree (trees/beads-y97/)                                 │
│                                                             │
│  ┌──────────────┐                                          │
│  │ Workflow     │                                          │
│  │ Execution    │───────┐                                  │
│  └──────────────┘       │                                  │
│                         │                                  │
│  Code runs here,        │ State/Logs/Events                │
│  tests execute here     │ written to main repo             │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Main Repo                                                   │
│                                                             │
│  agents/beads-y97/                                         │
│  ├── state.json      ←─────────────────┐                   │
│  ├── logs/           ←─────────┐       │                   │
│  └── events.jsonl    ←───┐     │       │                   │
│                          │     │       │                   │
│  ┌──────────────┐        │     │       │                   │
│  │ Dashboard    │────────┴─────┴───────┘                   │
│  │ (port 8765)  │                                          │
│  └──────────────┘                                          │
│                                                             │
│  Monitors all workflows (worktree + non-worktree)          │
└─────────────────────────────────────────────────────────────┘
```

This architecture ensures:
- ✅ Full visibility into all workflows
- ✅ Real-time monitoring works
- ✅ Logs aggregate in one place
- ✅ Dashboard shows parallel workflows
- ✅ State persists across worktree lifecycle
