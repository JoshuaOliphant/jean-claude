# Jean Claude: Event-Sourced Workflow Architecture

**Version:** 2.0
**Status:** Final Design
**Author:** Claude Sonnet 4.5 + Josh Oliphant
**Date:** 2025-12-29

---

## Executive Summary

Jean Claude is evolving to an **event-sourced architecture** with **git worktree isolation** for parallel workflow execution. This architecture solves three critical problems:

1. **Isolation**: Parallel workflows execute in isolated worktrees without conflicts
2. **Observability**: Real-time monitoring via event streams (no polling)
3. **Auditability**: Complete, immutable history of all workflow actions

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Event Store** | SQLite | ACID guarantees, excellent performance, single file |
| **Compaction** | Snapshots (every 100 events) | Bounded replay, preserves audit trail |
| **Execution Isolation** | Git Worktrees | True isolation, native git integration |
| **Monitoring** | Event subscriptions | Push-based, real-time, no polling |
| **Migration** | 3-phase incremental | Low risk, can rollback at any phase |

---

## Problems Solved

### Problem 1: Parallel Workflow Conflicts

**Current State:**
```
Main Repo (single working directory)
├── src/
│   └── core/message_writer.py
└── Workflow A modifies ─┐
    Workflow B modifies ─┴─> CONFLICT!
```

**Issue:** Multiple workflows modifying the same files simultaneously create:
- Circular imports
- Test contamination
- Merge conflicts
- Cascading failures

**Solution:** Git worktrees provide execution isolation.

### Problem 2: Monitoring via Polling

**Current State:**
```python
# Dashboard polls filesystem
while True:
    state = load_state_json(workflow_id)  # Disk I/O
    update_ui(state)
    sleep(1)  # Poll interval
```

**Issues:**
- Wasteful (reads even when nothing changed)
- Delayed (1 second lag)
- Race conditions (reading during write)
- No historical view

**Solution:** Event subscriptions push updates in real-time.

### Problem 3: No Audit Trail

**Current State:**
```python
state.phase = "implementing"  # Overwrites previous value
state.save()  # Old state lost forever
```

**Issues:**
- Can't answer "when did this change?"
- Can't reproduce past failures
- No compliance trail
- Can't time-travel debug

**Solution:** Immutable event log preserves complete history.

---

## Core Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Execution Layer: Git Worktrees (Isolated Code)             │
├─────────────────────────────────────────────────────────────┤
│ trees/beads-y97/     trees/beads-7gq/     trees/beads-400/ │
│ (branch: beads/y97)  (branch: beads/7gq)  (branch: beads/..)│
│                                                             │
│ Each workflow runs in its own worktree                      │
│ - Isolated working directory                                │
│ - Dedicated feature branch                                  │
│ - Independent test execution                                │
└────────┬────────────────────┬────────────────────┬──────────┘
         │                    │                    │
         │ Emit Events        │ Emit Events        │ Emit Events
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Event Store: events.db (SQLite)                             │
├─────────────────────────────────────────────────────────────┤
│ Single Source of Truth                                      │
│                                                             │
│ events table:                                               │
│ ┌─────────────────────────────────────────────────────────┐│
│ │seq│workflow_id│event_type   │timestamp │data          ││
│ │1  │beads-y97  │started      │2025-12..│{desc:"..."}  ││
│ │2  │beads-y97  │worktree.cre │2025-12..│{path:"tree..}││
│ │3  │beads-y97  │feature.plan │2025-12..│{name:"..."}  ││
│ │...│...        │...          │...      │...           ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ snapshots table (compaction):                               │
│ ┌─────────────────────────────────────────────────────────┐│
│ │workflow_id│seq │state                │created_at       ││
│ │beads-y97  │100 │{phase:"impl",...}   │2025-12-29...    ││
│ └─────────────────────────────────────────────────────────┘│
└────────┬───────────────────────┬────────────────────────────┘
         │                       │
         │ Project Events        │ Subscribe to Events
         ↓                       ↓
┌──────────────────────┐  ┌──────────────────────────────────┐
│ Projections          │  │ Monitoring & Dashboard           │
├──────────────────────┤  ├──────────────────────────────────┤
│ DashboardView        │  │ FastAPI + SSE                    │
│ (UI-optimized)       │  │ - Real-time updates              │
│                      │  │ - No polling                     │
│ ExecutionView        │  │ - Push notifications             │
│ (agent state)        │  │                                  │
│                      │  │ Worktree health monitoring       │
│ AuditLogView         │  │ Resource tracking                │
│ (compliance)         │  │ Event visualization              │
└──────────────────────┘  └──────────────────────────────────┘
```

### Separation of Concerns

| Concern | Responsibility | Location |
|---------|---------------|----------|
| **Execution** | Run code, execute tests | Worktrees (`trees/`) |
| **State** | Event log (source of truth) | SQLite (`events.db`) |
| **Views** | Derived state for queries | Projections (in-memory) |
| **Monitoring** | Real-time updates | Dashboard (SSE subscriptions) |

---

## Event Store Design

### Schema

```sql
-- Events table (append-only, never update/delete)
CREATE TABLE events (
    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id TEXT NOT NULL,
    event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,  -- ISO 8601
    data JSON NOT NULL,       -- Event payload

    -- Indexes for fast queries
    CONSTRAINT events_pk PRIMARY KEY (sequence_number)
);

CREATE INDEX idx_workflow_sequence ON events(workflow_id, sequence_number);
CREATE INDEX idx_event_type ON events(event_type);
CREATE INDEX idx_timestamp ON events(timestamp);

-- Snapshots table (compaction)
CREATE TABLE snapshots (
    workflow_id TEXT PRIMARY KEY,
    sequence_number INTEGER NOT NULL,  -- Last event included
    state JSON NOT NULL,               -- Projected state
    created_at TEXT NOT NULL
);
```

### Event Types

```python
# Workflow lifecycle events
WorkflowStarted          # {description, beads_task_id?}
WorkflowCompleted        # {duration_ms, total_cost}
WorkflowFailed           # {error, phase}

# Worktree lifecycle events
WorktreeCreated          # {path, branch, base_commit}
WorktreeActive           # {path} (heartbeat)
WorktreeMerged           # {commit_sha, conflicts:[]}
WorktreeDeleted          # {reason: "merged"|"failed"|"manual"}

# Feature lifecycle events
FeaturePlanned           # {name, description, test_file}
FeatureStarted           # {name}
FeatureCompleted         # {name, tests_passing, duration_ms}
FeatureFailed            # {name, error}

# Phase transition events
PhaseChanged             # {from_phase, to_phase}

# Test events
TestsStarted             # {test_file, feature}
TestsPassed              # {test_file, feature, count, duration_ms}
TestsFailed              # {test_file, feature, failures:[]}

# Commit events
CommitCreated            # {commit_sha, message, files:[]}
CommitFailed             # {error, files:[]}
```

### Event Structure

```python
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

@dataclass(frozen=True)  # Immutable
class WorkflowEvent:
    """Base event structure."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'workflow_id': self.workflow_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'data': self.data
        }
```

### Event Store API

```python
class EventStore:
    """SQLite-based event store with snapshot support."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_schema()
        self._subscribers: list[Callable] = []

    def append(self, event: WorkflowEvent) -> None:
        """Append event to store (ACID transaction)."""
        with self._transaction() as conn:
            conn.execute("""
                INSERT INTO events (workflow_id, event_id, event_type,
                                   timestamp, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event.workflow_id,
                event.event_id,
                event.event_type,
                event.timestamp.isoformat(),
                json.dumps(event.data)
            ))

        # Notify subscribers (real-time updates)
        self._notify_subscribers(event)

        # Check if snapshot needed
        self._maybe_create_snapshot(event.workflow_id)

    def get_events(self, workflow_id: str,
                   since_sequence: int = 0) -> list[WorkflowEvent]:
        """Get events for workflow (indexed query, fast)."""
        with self._transaction() as conn:
            cursor = conn.execute("""
                SELECT * FROM events
                WHERE workflow_id = ? AND sequence_number > ?
                ORDER BY sequence_number ASC
            """, (workflow_id, since_sequence))

            return [self._row_to_event(row) for row in cursor]

    def subscribe(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """Subscribe to new events (real-time notifications)."""
        self._subscribers.append(callback)

    def save_snapshot(self, workflow_id: str, state: dict,
                     sequence: int) -> None:
        """Save snapshot for fast state reconstruction."""
        with self._transaction() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO snapshots
                (workflow_id, sequence_number, state, created_at)
                VALUES (?, ?, ?, ?)
            """, (workflow_id, sequence, json.dumps(state),
                 datetime.now().isoformat()))

    def get_snapshot(self, workflow_id: str) -> tuple[dict, int] | None:
        """Get latest snapshot for workflow."""
        with self._transaction() as conn:
            cursor = conn.execute("""
                SELECT state, sequence_number FROM snapshots
                WHERE workflow_id = ?
            """, (workflow_id,))

            row = cursor.fetchone()
            if row:
                return json.loads(row['state']), row['sequence_number']
            return None

    def rebuild_projection(self, workflow_id: str) -> dict:
        """Rebuild current state from events (using snapshot if available)."""
        # Try to load snapshot first
        snapshot_result = self.get_snapshot(workflow_id)

        if snapshot_result:
            state, last_seq = snapshot_result
            events = self.get_events(workflow_id, since_sequence=last_seq)
        else:
            state = {}
            events = self.get_events(workflow_id)

        # Apply events to state
        for event in events:
            state = apply_event(state, event)

        return state

    def _maybe_create_snapshot(self, workflow_id: str) -> None:
        """Create snapshot if event count crosses threshold."""
        SNAPSHOT_INTERVAL = 100

        event_count = self._get_event_count(workflow_id)
        if event_count % SNAPSHOT_INTERVAL == 0:
            state = self.rebuild_projection(workflow_id)
            self.save_snapshot(workflow_id, state, event_count)
```

### Projection Builder

```python
def apply_event(state: dict, event: WorkflowEvent) -> dict:
    """Apply event to state (pure function, no side effects)."""
    new_state = state.copy()

    match event.event_type:
        case "workflow.started":
            new_state.update({
                'phase': 'planning',
                'created_at': event.timestamp,
                'description': event.data.get('description'),
                'beads_task_id': event.data.get('beads_task_id')
            })

        case "worktree.created":
            new_state.update({
                'worktree_path': event.data['path'],
                'worktree_branch': event.data['branch'],
                'base_commit': event.data['base_commit']
            })

        case "feature.planned":
            features = new_state.get('features', [])
            features.append({
                'name': event.data['name'],
                'description': event.data['description'],
                'status': 'planned',
                'tests_passing': False
            })
            new_state['features'] = features

        case "feature.completed":
            features = new_state.get('features', [])
            for feature in features:
                if feature['name'] == event.data['name']:
                    feature['status'] = 'completed'
                    feature['tests_passing'] = event.data['tests_passing']
                    feature['completed_at'] = event.timestamp
            new_state['features'] = features

        case "phase.changed":
            new_state['phase'] = event.data['to_phase']

        case "worktree.merged":
            new_state.update({
                'merge_commit': event.data['commit_sha'],
                'worktree_merged': True
            })

        case "workflow.completed":
            new_state.update({
                'phase': 'complete',
                'completed_at': event.timestamp,
                'duration_ms': event.data['duration_ms'],
                'total_cost': event.data.get('total_cost')
            })

    new_state['updated_at'] = event.timestamp
    return new_state
```

---

## Worktree Integration

### Worktree Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. jc work jean_claude-y97                                  │
│    └─> Emit: WorkflowStarted                               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Create worktree                                          │
│    git worktree add -b beads/jean_claude-y97 \             │
│                        trees/beads-jean_claude-y97 main     │
│    └─> Emit: WorktreeCreated                               │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Execute workflow in worktree                             │
│    - Plan features  └─> Emit: FeaturePlanned (×N)          │
│    - Implement      └─> Emit: FeatureStarted/Completed     │
│    - Run tests      └─> Emit: TestsPassed/Failed           │
│    - Create commits └─> Emit: CommitCreated                │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Merge worktree (on success)                              │
│    git checkout main                                        │
│    git merge --no-ff beads/jean_claude-y97                 │
│    └─> Emit: WorktreeMerged                                │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Cleanup worktree                                         │
│    git worktree remove trees/beads-jean_claude-y97          │
│    git branch -d beads/jean_claude-y97                     │
│    └─> Emit: WorktreeDeleted                               │
└─────────────────────────────────────────────────────────────┘
```

### Worktree Module

```python
# src/jean_claude/integrations/worktree.py

from pathlib import Path
import subprocess

class WorktreeManager:
    """Manages git worktrees for workflow isolation."""

    def __init__(self, repo_root: Path, event_store: EventStore):
        self.repo_root = repo_root
        self.event_store = event_store

    async def create_worktree(self, workflow_id: str,
                             base_branch: str = "main") -> Path:
        """Create worktree for workflow."""
        worktree_path = self.repo_root / "trees" / workflow_id
        branch_name = f"beads/{workflow_id.replace('beads-', '')}"

        # Create worktree with new branch
        subprocess.run([
            "git", "worktree", "add",
            "-b", branch_name,
            str(worktree_path),
            base_branch
        ], cwd=self.repo_root, check=True, capture_output=True)

        # Get base commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            check=True
        )
        base_commit = result.stdout.strip()

        # Emit event
        await self.event_store.append(WorkflowEvent(
            workflow_id=workflow_id,
            event_type="worktree.created",
            data={
                'path': str(worktree_path),
                'branch': branch_name,
                'base_commit': base_commit
            }
        ))

        return worktree_path

    async def merge_worktree(self, workflow_id: str) -> str:
        """Merge worktree branch to main."""
        # Get worktree info from events
        state = self.event_store.rebuild_projection(workflow_id)
        branch_name = state['worktree_branch']

        # Switch to main
        subprocess.run(
            ["git", "checkout", "main"],
            cwd=self.repo_root,
            check=True
        )

        # Merge
        subprocess.run([
            "git", "merge", "--no-ff",
            "-m", f"Merge workflow {workflow_id}",
            branch_name
        ], cwd=self.repo_root, check=True, capture_output=True)

        # Get merge commit SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        merge_commit = result.stdout.strip()

        # Emit event
        await self.event_store.append(WorkflowEvent(
            workflow_id=workflow_id,
            event_type="worktree.merged",
            data={
                'commit_sha': merge_commit,
                'branch': branch_name,
                'conflicts': []
            }
        ))

        return merge_commit

    async def delete_worktree(self, workflow_id: str,
                             reason: str = "merged") -> None:
        """Remove worktree and branch."""
        state = self.event_store.rebuild_projection(workflow_id)
        worktree_path = Path(state['worktree_path'])
        branch_name = state['worktree_branch']

        # Remove worktree
        subprocess.run([
            "git", "worktree", "remove",
            str(worktree_path)
        ], cwd=self.repo_root, check=True, capture_output=True)

        # Delete branch
        subprocess.run([
            "git", "branch", "-d",
            branch_name
        ], cwd=self.repo_root, check=True, capture_output=True)

        # Emit event
        await self.event_store.append(WorkflowEvent(
            workflow_id=workflow_id,
            event_type="worktree.deleted",
            data={'reason': reason}
        ))
```

### Workflow Orchestration with Worktrees

```python
# src/jean_claude/orchestration/two_agent.py

async def run_two_agent_workflow(
    description: str,
    project_root: Path,
    workflow_id: str,
    # ... other params ...
) -> dict:
    """Run two-agent workflow in isolated worktree."""

    event_store = EventStore(project_root / "events.db")
    worktree_mgr = WorktreeManager(project_root, event_store)

    # Emit: workflow started
    await event_store.append(WorkflowEvent(
        workflow_id=workflow_id,
        event_type="workflow.started",
        data={'description': description}
    ))

    # Create isolated worktree
    execution_root = await worktree_mgr.create_worktree(workflow_id)

    try:
        # Plan features (in worktree)
        features = await plan_features(description, execution_root)
        for feature in features:
            await event_store.append(WorkflowEvent(
                workflow_id=workflow_id,
                event_type="feature.planned",
                data={
                    'name': feature.name,
                    'description': feature.description,
                    'test_file': feature.test_file
                }
            ))

        # Implement features (in worktree)
        for feature in features:
            await event_store.append(WorkflowEvent(
                workflow_id=workflow_id,
                event_type="feature.started",
                data={'name': feature.name}
            ))

            success = await implement_feature(feature, execution_root)

            if success:
                await event_store.append(WorkflowEvent(
                    workflow_id=workflow_id,
                    event_type="feature.completed",
                    data={
                        'name': feature.name,
                        'tests_passing': True
                    }
                ))
            else:
                await event_store.append(WorkflowEvent(
                    workflow_id=workflow_id,
                    event_type="feature.failed",
                    data={
                        'name': feature.name,
                        'error': 'Implementation failed'
                    }
                ))
                raise RuntimeError(f"Feature {feature.name} failed")

        # Merge worktree back to main
        merge_commit = await worktree_mgr.merge_worktree(workflow_id)

        # Cleanup worktree
        await worktree_mgr.delete_worktree(workflow_id, reason="merged")

        # Emit: workflow completed
        await event_store.append(WorkflowEvent(
            workflow_id=workflow_id,
            event_type="workflow.completed",
            data={
                'merge_commit': merge_commit,
                'duration_ms': ...
            }
        ))

        # Return final state (from events)
        return event_store.rebuild_projection(workflow_id)

    except Exception as e:
        # Preserve worktree for debugging
        await event_store.append(WorkflowEvent(
            workflow_id=workflow_id,
            event_type="workflow.failed",
            data={'error': str(e)}
        ))
        raise
```

---

## Monitoring & Dashboard

### Real-Time Event Subscription

```python
# src/jean_claude/dashboard/app.py

from sse_starlette.sse import EventSourceResponse

class DashboardApp:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.projections = {}  # Cache of projections

        # Subscribe to events for real-time updates
        event_store.subscribe(self._on_event)

    def _on_event(self, event: WorkflowEvent) -> None:
        """Update projection when new event arrives."""
        # Update cached projection
        if event.workflow_id in self.projections:
            old_state = self.projections[event.workflow_id]
            new_state = apply_event(old_state, event)
            self.projections[event.workflow_id] = new_state
        else:
            # Build from scratch
            self.projections[event.workflow_id] = \
                self.event_store.rebuild_projection(event.workflow_id)

        # Notify SSE clients
        asyncio.create_task(self._notify_sse_clients(event.workflow_id))

    async def stream_updates(self) -> AsyncGenerator[str, None]:
        """SSE endpoint - push updates when events arrive."""
        queue = asyncio.Queue()

        # Register callback to push to this queue
        def on_update(workflow_id: str):
            queue.put_nowait(workflow_id)

        self.update_callbacks.append(on_update)

        try:
            while True:
                workflow_id = await queue.get()
                state = self.projections[workflow_id]

                yield {
                    "event": "workflow_update",
                    "data": json.dumps(state)
                }
        finally:
            self.update_callbacks.remove(on_update)

    @app.get("/api/workflows")
    def list_workflows(self) -> list[dict]:
        """Get all workflows (from projection cache)."""
        return list(self.projections.values())

    @app.get("/api/workflows/{workflow_id}")
    def get_workflow(self, workflow_id: str) -> dict:
        """Get specific workflow state."""
        if workflow_id not in self.projections:
            # Build on-demand
            self.projections[workflow_id] = \
                self.event_store.rebuild_projection(workflow_id)

        return self.projections[workflow_id]

    @app.get("/api/workflows/{workflow_id}/events")
    def get_workflow_events(self, workflow_id: str) -> list[dict]:
        """Get event stream for workflow (audit log)."""
        events = self.event_store.get_events(workflow_id)
        return [event.to_dict() for event in events]
```

### Dashboard UI Enhancements

```html
<!-- templates/dashboard.html -->
<div class="workflow-card">
  <h3>{{ workflow.workflow_name }}</h3>

  <!-- Phase and progress -->
  <div class="status">
    <span class="badge">{{ workflow.phase }}</span>
    <span class="progress">
      {{ workflow.features | completed }} / {{ workflow.features | length }}
    </span>
  </div>

  <!-- Worktree info -->
  {% if workflow.worktree_path %}
  <div class="worktree-info">
    <svg class="icon">...</svg>
    <span>Isolated Worktree</span>
    <code>{{ workflow.worktree_branch }}</code>
  </div>
  {% endif %}

  <!-- Real-time event stream -->
  <div class="event-stream" id="events-{{ workflow.workflow_id }}">
    <!-- Updated via SSE -->
  </div>
</div>

<script>
// Subscribe to real-time updates
const eventSource = new EventSource('/api/workflows/stream');

eventSource.addEventListener('workflow_update', (e) => {
  const workflow = JSON.parse(e.data);
  updateWorkflowCard(workflow);
});
</script>
```

---

## Data Flow

### Write Path (Workflow → Events)

```
Workflow Action
    │
    ├─> emit(WorkflowEvent)
    │
    ↓
EventStore.append()
    │
    ├─> INSERT INTO events (...)  [SQLite transaction]
    │
    ├─> Maybe create snapshot (if event_count % 100 == 0)
    │
    └─> Notify subscribers
            │
            ├─> Dashboard projection updated
            │
            └─> SSE clients notified
```

### Read Path (Dashboard Query)

```
Dashboard Query
    │
    ↓
EventStore.rebuild_projection(workflow_id)
    │
    ├─> Get snapshot (if exists)
    │       │
    │       └─> SELECT state FROM snapshots WHERE workflow_id = ?
    │
    ├─> Get events since snapshot
    │       │
    │       └─> SELECT * FROM events
    │           WHERE workflow_id = ? AND sequence > snapshot_seq
    │
    └─> Apply events to state (fold/reduce)
            │
            └─> return final_state
```

### Event Flow Diagram

```
┌──────────────┐
│ Workflow     │
│ (worktree)   │
└──────┬───────┘
       │
       │ emit event
       ↓
┌──────────────────────────────────────┐
│ Event Store (SQLite)                 │
│                                      │
│ 1. Append to events table (ACID)    │
│ 2. Check snapshot threshold          │
│ 3. Notify subscribers                │
└──────┬───────────┬───────────────────┘
       │           │
       │           │ real-time update
       │           ↓
       │     ┌─────────────────┐
       │     │ Dashboard        │
       │     │ - Update cache   │
       │     │ - Push via SSE   │
       │     └─────────────────┘
       │
       │ query
       ↓
┌──────────────────┐
│ Projections      │
│ - DashboardView  │
│ - AuditLog       │
│ - Metrics        │
└──────────────────┘
```

---

## Implementation Plan

### Phase 1: Event Store Foundation (Week 1)

**Goal:** Build event store, no workflow integration yet

**Tasks:**
1. Create `src/jean_claude/core/event_store.py`
   - SQLite schema setup
   - Append/query operations
   - Snapshot support
   - Subscription mechanism

2. Create `src/jean_claude/core/events.py`
   - Event type definitions
   - Event validation
   - Projection builder (`apply_event`)

3. Write tests
   - `tests/core/test_event_store.py`
   - `tests/core/test_projections.py`

**Deliverable:** Working event store that can append/query events

### Phase 2: Worktree Integration (Week 1)

**Goal:** Workflows run in worktrees, emit basic events

**Tasks:**
1. Create `src/jean_claude/integrations/worktree.py`
   - `create_worktree()`
   - `merge_worktree()`
   - `delete_worktree()`

2. Modify `src/jean_claude/orchestration/two_agent.py`
   - Create worktree at start
   - Emit lifecycle events
   - Merge on success
   - Cleanup

3. Write tests
   - `tests/integrations/test_worktree.py`
   - `tests/orchestration/test_event_emission.py`

**Deliverable:** Workflows run in worktrees, emit events

### Phase 3: Dashboard Event Subscriptions (Week 2)

**Goal:** Dashboard reads from events, real-time updates

**Tasks:**
1. Modify `src/jean_claude/dashboard/app.py`
   - Subscribe to event store
   - Build projections from events
   - SSE push notifications
   - Remove state.json polling

2. Update dashboard UI
   - Real-time event stream
   - Worktree status display
   - Event history view

3. Write tests
   - `tests/dashboard/test_event_subscriptions.py`
   - `tests/dashboard/test_projections.py`

**Deliverable:** Dashboard shows real-time updates from events

### Phase 4: CLI Integration (Week 2)

**Goal:** All commands use events

**Tasks:**
1. Update `jc work` command
   - Emit workflow events
   - Read from event store

2. Update `jc status` command
   - Query event projections
   - Show worktree info

3. Add `jc worktrees` command group
   - `jc worktrees list`
   - `jc worktrees cleanup`
   - `jc worktrees health`

4. Write tests
   - Update all CLI command tests

**Deliverable:** Full CLI using event-sourced architecture

### Phase 5: Migration & Cleanup (Week 3)

**Goal:** Remove old state.json system

**Tasks:**
1. Remove state.json writes
   - Delete `WorkflowState.save()` calls
   - Keep `WorkflowState` class as projection view

2. Migrate existing workflows
   - Script to convert state.json → events
   - Preserve history

3. Documentation
   - Update architecture docs
   - API reference
   - Migration guide

**Deliverable:** Clean event-sourced system, old code removed

---

## Migration Strategy

### Phase 1: Dual-Write (Safe, Reversible)

```python
# Emit event AND write state.json
await event_store.append(FeatureCompleted(...))  # NEW
state.save()  # OLD - keep for safety
```

**Rollback:** Just stop emitting events, keep using state.json

### Phase 2: Read from Events (Dashboard Only)

```python
# Dashboard reads from events
state = event_store.rebuild_projection(workflow_id)
# CLI still reads state.json
```

**Rollback:** Dashboard switches back to state.json

### Phase 3: Full Cutover

```python
# Only emit events
await event_store.append(FeatureCompleted(...))
# state.save() ← DELETED
```

**Rollback:** More complex, need to restore state.json writes

---

## Performance Characteristics

### Storage

```
Event size: ~300 bytes
Snapshot size: ~5 KB

1,000 workflows:
- Events (200/workflow): 60 MB
- Snapshots (2/workflow): 10 MB
- Total: 70 MB

10,000 workflows: 700 MB (still fine)
```

### Query Performance

```
Without snapshots:
- 1,000 events: ~5ms
- 10,000 events: ~50ms

With snapshots (every 100 events):
- Load snapshot: 1ms
- Replay 50 events: 2ms
- Total: 3ms (constant time!)
```

### Concurrency

```
SQLite handles:
- Multiple readers (concurrent)
- Single writer (serialized)
- IMMEDIATE transactions prevent deadlocks
```

---

## API Reference

### Event Store

```python
class EventStore:
    def append(event: WorkflowEvent) -> None
    def get_events(workflow_id: str, since_sequence: int = 0) -> list[WorkflowEvent]
    def subscribe(callback: Callable[[WorkflowEvent], None]) -> None
    def save_snapshot(workflow_id: str, state: dict, sequence: int) -> None
    def get_snapshot(workflow_id: str) -> tuple[dict, int] | None
    def rebuild_projection(workflow_id: str) -> dict
```

### Worktree Manager

```python
class WorktreeManager:
    async def create_worktree(workflow_id: str, base_branch: str = "main") -> Path
    async def merge_worktree(workflow_id: str) -> str
    async def delete_worktree(workflow_id: str, reason: str) -> None
    def list_active_worktrees() -> list[WorktreeInfo]
```

### Dashboard

```python
class DashboardApp:
    async def stream_updates() -> AsyncGenerator[str, None]
    def list_workflows() -> list[dict]
    def get_workflow(workflow_id: str) -> dict
    def get_workflow_events(workflow_id: str) -> list[dict]
```

---

## Summary

### What We're Building

1. **Event-Sourced State**
   - Events are source of truth
   - State is derived (projections)
   - Complete audit trail

2. **Worktree Isolation**
   - Each workflow in separate worktree
   - Parallel execution without conflicts
   - Merge on success

3. **Real-Time Monitoring**
   - Event subscriptions (push, not poll)
   - Dashboard updates instantly
   - SSE streaming

### Why This Architecture

- ✅ **Solves parallel execution** - Worktrees provide isolation
- ✅ **Solves monitoring** - Event subscriptions, no polling
- ✅ **Solves auditability** - Immutable event log
- ✅ **Simple** - SQLite (single file), no external services
- ✅ **Performant** - Snapshots enable constant-time queries
- ✅ **Testable** - Pure functions, event replay
- ✅ **Debuggable** - Time-travel, full history
- ✅ **Incremental** - Can migrate in phases

### Next Steps

1. Review this architecture with team
2. Start Phase 1: Event store implementation
3. Write tests for event store
4. Integrate worktrees
5. Update dashboard
6. Migrate CLI commands
7. Remove old state.json system

---

## Appendix: Previous Design Documents

This document consolidates and supersedes:
- `worktree-integration-design.md` - Original worktree design
- `worktree-monitoring-design.md` - Monitoring implications
- `worktree-architecture-exploration.md` - Pattern exploration
- `event-store-architecture.md` - Event store deep dive

Those documents remain for historical context but this is the definitive architecture.
