# Git Worktrees + Monitoring: Architectural Exploration

## Problem Space Analysis

We're solving **three interconnected problems**:

1. **Isolation**: Parallel workflows need independent execution environments
2. **Observability**: Need to monitor all workflows in real-time
3. **Coordination**: Workflows must merge back without conflicts

Current approach: File-based state with polling
- State stored in mutable `state.json` files
- Dashboard polls filesystem for updates
- No audit trail
- No time-travel debugging
- Difficult to reason about concurrent workflows

**Question**: What if we designed this system from scratch?

---

## Approach 1: Event Sourcing Architecture

### Core Concept

**State is not stored - it's derived from an append-only event log.**

Every action becomes an immutable event:
- `WorkflowStarted(workflow_id, description)`
- `WorktreeCreated(workflow_id, path, branch)`
- `FeaturePlanned(workflow_id, feature_name)`
- `TestPassed(workflow_id, feature_name, test_file)`
- `WorktreeMerged(workflow_id, commit_sha)`
- `WorkflowCompleted(workflow_id)`

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Event Store (Append-Only)                                  │
│                                                             │
│ beads-y97.events                                           │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 1. WorkflowStarted {...}                                ││
│ │ 2. WorktreeCreated {path: "trees/beads-y97"}            ││
│ │ 3. FeaturePlanned {name: "extract-utils"}               ││
│ │ 4. FeatureStarted {name: "extract-utils"}               ││
│ │ 5. TestPassed {feature: "extract-utils", tests: 5}      ││
│ │ 6. FeatureCompleted {name: "extract-utils"}             ││
│ │ 7. WorktreeMerged {commit: "abc123"}                    ││
│ │ 8. WorkflowCompleted {}                                 ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Events flow to projections
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Projections (Materialized Views)                           │
├─────────────────────────────────────────────────────────────┤
│ ExecutionView         DashboardView       AuditLogView     │
│ (for agents)          (for monitoring)    (for compliance) │
│                                                             │
│ current_feature: 1    progress: "4/7"     all_events[]     │
│ worktree_path: ...    phase: "impl"       timestamps       │
│ iteration: 3          worktree: ✓         user_actions     │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

```python
# Event definitions
@dataclass(frozen=True)  # Immutable
class WorkflowEvent:
    event_id: str
    workflow_id: str
    timestamp: datetime
    event_type: str
    data: dict

class WorktreeCreated(WorkflowEvent):
    event_type = "worktree.created"

class FeatureCompleted(WorkflowEvent):
    event_type = "feature.completed"

# Event store (append-only)
class EventStore:
    def append(self, event: WorkflowEvent) -> None:
        """Append event to log (never update/delete)."""
        log_file = self.base_path / f"{event.workflow_id}.events"
        with log_file.open('a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')

    def get_events(self, workflow_id: str,
                   since_event: int = 0) -> list[WorkflowEvent]:
        """Read events from log."""
        # Returns events in order

    def subscribe(self, workflow_id: str,
                  callback: Callable[[WorkflowEvent], None]) -> None:
        """Subscribe to new events (real-time)."""
        # Watch file for new lines, call callback

# Projection (derived state)
class WorkflowProjection:
    """Build current state from event stream."""

    def __init__(self, workflow_id: str, event_store: EventStore):
        self.workflow_id = workflow_id
        self.state = self._build_state(event_store.get_events(workflow_id))

    def _build_state(self, events: list[WorkflowEvent]) -> dict:
        """Fold/reduce events into current state."""
        state = {
            'phase': 'planning',
            'features': [],
            'worktree_path': None,
            # ...
        }

        for event in events:
            state = self._apply_event(state, event)

        return state

    def _apply_event(self, state: dict, event: WorkflowEvent) -> dict:
        """Apply single event to state (pure function)."""
        if event.event_type == "worktree.created":
            return {**state, 'worktree_path': event.data['path']}
        elif event.event_type == "feature.completed":
            features = state['features'] + [event.data['feature']]
            return {**state, 'features': features}
        # ... more event handlers
        return state

# Dashboard projection (optimized for queries)
class DashboardProjection:
    """Optimized view for dashboard."""

    def __init__(self, event_store: EventStore):
        self.workflows = {}

        # Build from all events
        for workflow_id in self._get_all_workflow_ids():
            events = event_store.get_events(workflow_id)
            self.workflows[workflow_id] = self._build_dashboard_view(events)

        # Subscribe to updates
        event_store.subscribe_all(self._on_event)

    def _build_dashboard_view(self, events: list[WorkflowEvent]) -> dict:
        """Build view optimized for dashboard queries."""
        return {
            'workflow_id': ...,
            'progress_percentage': ...,
            'estimated_completion': ...,
            'resource_usage': ...,
            # Derived/computed fields for UI
        }

    def _on_event(self, event: WorkflowEvent) -> None:
        """Incrementally update view when event arrives."""
        # Update only affected workflow
        self.workflows[event.workflow_id] = self._apply_event_to_view(
            self.workflows.get(event.workflow_id, {}),
            event
        )

        # Notify subscribers (SSE clients)
        self.notify_subscribers(event.workflow_id)
```

### Workflow Execution

```python
class EventSourcedWorkflow:
    """Workflow that emits events instead of mutating state."""

    def __init__(self, workflow_id: str, event_store: EventStore):
        self.workflow_id = workflow_id
        self.event_store = event_store

    async def run(self, description: str) -> None:
        """Execute workflow, emitting events."""

        # Emit: workflow started
        await self.emit(WorkflowStarted(
            workflow_id=self.workflow_id,
            description=description,
            timestamp=datetime.now()
        ))

        # Create worktree
        worktree_path = await self._create_worktree()
        await self.emit(WorktreeCreated(
            workflow_id=self.workflow_id,
            path=worktree_path,
            branch=f"beads/{self.workflow_id}"
        ))

        # Plan features
        features = await self._plan_features(description)
        for feature in features:
            await self.emit(FeaturePlanned(
                workflow_id=self.workflow_id,
                feature_name=feature.name,
                description=feature.description
            ))

        # Implement features
        for feature in features:
            await self.emit(FeatureStarted(
                workflow_id=self.workflow_id,
                feature_name=feature.name
            ))

            success = await self._implement_feature(feature, worktree_path)

            if success:
                await self.emit(FeatureCompleted(
                    workflow_id=self.workflow_id,
                    feature_name=feature.name,
                    tests_passing=True
                ))
            else:
                await self.emit(FeatureFailed(
                    workflow_id=self.workflow_id,
                    feature_name=feature.name,
                    error=...
                ))

        # Merge worktree
        commit_sha = await self._merge_worktree(worktree_path)
        await self.emit(WorktreeMerged(
            workflow_id=self.workflow_id,
            commit_sha=commit_sha,
            branch=f"beads/{self.workflow_id}"
        ))

        # Complete
        await self.emit(WorkflowCompleted(
            workflow_id=self.workflow_id,
            duration_ms=...
        ))

    async def emit(self, event: WorkflowEvent) -> None:
        """Emit event to store."""
        self.event_store.append(event)
        # Event store notifies all subscribers automatically
```

### Dashboard (Real-time, No Polling)

```python
class EventSourcedDashboard:
    """Dashboard that subscribes to event stream."""

    def __init__(self, event_store: EventStore):
        self.projection = DashboardProjection(event_store)
        self.subscribers = []  # SSE clients

    async def stream_updates(self) -> AsyncGenerator[str, None]:
        """SSE endpoint - push updates when events arrive."""
        queue = asyncio.Queue()

        # Subscribe to projection updates
        self.projection.on_update(lambda wf_id: queue.put_nowait(wf_id))

        while True:
            workflow_id = await queue.get()
            workflow = self.projection.workflows[workflow_id]

            yield {
                "event": "workflow_update",
                "data": json.dumps(workflow)
            }

    def get_workflow(self, workflow_id: str) -> dict:
        """Query current state (from projection)."""
        return self.projection.workflows.get(workflow_id)

    def list_workflows(self) -> list[dict]:
        """Query all workflows (from projection)."""
        return list(self.projection.workflows.values())
```

### Benefits

✅ **Time Travel**: Replay events to any point in time
✅ **Audit Trail**: Every action is recorded immutably
✅ **Real-time**: Dashboard updates instantly (no polling)
✅ **Multiple Views**: Different projections for different needs
✅ **Debugging**: See exact sequence of events that led to state
✅ **Testing**: Replay events in tests to reproduce issues
✅ **Scalability**: Event store can be partitioned/sharded
✅ **Resilience**: Events are immutable, can rebuild state from scratch

### Worktree Integration

```python
# Worktree events
class WorktreeCreated(WorkflowEvent):
    path: Path
    branch: str
    base_commit: str

class WorktreeActive(WorkflowEvent):
    # Heartbeat - worktree still exists
    pass

class WorktreeMerged(WorkflowEvent):
    commit_sha: str
    conflicts: list[str] = []

class WorktreeDeleted(WorkflowEvent):
    reason: str  # "merged" | "failed" | "manual"

# Projection for worktree management
class WorktreeProjection:
    def __init__(self, event_store: EventStore):
        self.worktrees = {}

        for wf_id in self._get_all_workflows():
            events = event_store.get_events(wf_id)
            self.worktrees[wf_id] = self._derive_worktree_state(events)

    def _derive_worktree_state(self, events: list[WorkflowEvent]) -> dict:
        """Derive current worktree state from events."""
        state = {'exists': False, 'path': None, 'branch': None}

        for event in events:
            if isinstance(event, WorktreeCreated):
                state = {'exists': True, 'path': event.path, 'branch': event.branch}
            elif isinstance(event, WorktreeDeleted):
                state = {'exists': False, 'path': None, 'branch': None}

        return state

    def list_active_worktrees(self) -> list[dict]:
        """Get all currently active worktrees."""
        return [
            {'workflow_id': wf_id, **state}
            for wf_id, state in self.worktrees.items()
            if state['exists']
        ]
```

### Drawbacks

❌ **Complexity**: Event sourcing adds conceptual overhead
❌ **Storage**: Events accumulate (need compaction strategy)
❌ **Migration**: Complete rewrite of current system
❌ **Learning Curve**: Team needs to understand event sourcing

---

## Approach 2: Actor Model (Erlang/Akka Style)

### Core Concept

**Each workflow is an actor with its own mailbox and isolated state.**

Actors communicate via messages (asynchronous, location-transparent).

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Supervision Tree                                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ RootSupervisor                                             │
│ ├── WorkflowSupervisor (one-for-one restart)               │
│ │   ├── WorkflowActor(beads-y97)                          │
│ │   │   ├── WorktreeActor                                 │
│ │   │   ├── PlannerAgent                                  │
│ │   │   └── CoderAgent                                    │
│ │   ├── WorkflowActor(beads-7gq)                          │
│ │   └── ...                                               │
│ └── MonitoringSupervisor (one-for-all restart)             │
│     ├── DashboardActor                                     │
│     ├── LogAggregator                                      │
│     └── MetricsCollector                                   │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

```python
from typing import Protocol
import asyncio

class Actor(Protocol):
    """Actor protocol."""

    async def receive(self, message: Any) -> None:
        """Process message from mailbox."""
        ...

class WorkflowActor:
    """Actor managing a single workflow."""

    def __init__(self, workflow_id: str, supervisor: ActorRef):
        self.workflow_id = workflow_id
        self.supervisor = supervisor
        self.mailbox = asyncio.Queue()
        self.state = {}

        # Child actors
        self.worktree_actor = None
        self.planner_agent = None
        self.coder_agent = None

    async def receive(self, message: Message) -> None:
        """Handle incoming messages."""
        match message:
            case StartWorkflow(description):
                await self._handle_start(description)
            case FeatureCompleted(feature_name):
                await self._handle_feature_completed(feature_name)
            case QueryState():
                # Send state to requester
                message.reply_to.tell(self.state)
            case _:
                # Unknown message
                pass

    async def _handle_start(self, description: str) -> None:
        """Start workflow execution."""
        # Spawn worktree actor
        self.worktree_actor = await self.supervisor.spawn(
            WorktreeActor,
            workflow_id=self.workflow_id
        )

        # Tell worktree actor to create worktree
        await self.worktree_actor.tell(CreateWorktree())

        # Notify monitoring
        await self.supervisor.tell(
            WorkflowStarted(workflow_id=self.workflow_id)
        )

class DashboardActor:
    """Actor that aggregates workflow states."""

    def __init__(self):
        self.workflows = {}
        self.subscribers = []  # SSE connections

    async def receive(self, message: Message) -> None:
        match message:
            case WorkflowStarted(workflow_id):
                self.workflows[workflow_id] = {'phase': 'starting'}
                await self._notify_subscribers()

            case FeatureCompleted(workflow_id, feature):
                self.workflows[workflow_id]['features'].append(feature)
                await self._notify_subscribers()

            case SubscribeToUpdates(client):
                self.subscribers.append(client)

    async def _notify_subscribers(self) -> None:
        """Push updates to all SSE clients."""
        for subscriber in self.subscribers:
            await subscriber.send(self.workflows)

class WorktreeActor:
    """Actor managing worktree lifecycle."""

    async def receive(self, message: Message) -> None:
        match message:
            case CreateWorktree():
                path = await self._create_worktree()
                await self.parent.tell(WorktreeCreated(path))

            case MergeWorktree():
                commit = await self._merge()
                await self.parent.tell(WorktreeMerged(commit))

            case CheckHealth():
                exists = self.worktree_path.exists()
                await message.reply_to.tell(WorktreeHealth(exists))
```

### Message-Based Communication

```python
# Messages
@dataclass
class StartWorkflow:
    description: str

@dataclass
class FeatureCompleted:
    workflow_id: str
    feature_name: str

@dataclass
class QueryState:
    reply_to: ActorRef

# Actor system
class ActorSystem:
    def __init__(self):
        self.actors = {}
        self.supervisor = Supervisor()

    async def spawn(self, actor_class: type, **kwargs) -> ActorRef:
        """Spawn new actor."""
        actor = actor_class(**kwargs)
        actor_ref = ActorRef(actor)
        self.actors[actor_ref.id] = actor

        # Start actor's message loop
        asyncio.create_task(self._run_actor(actor))

        return actor_ref

    async def _run_actor(self, actor: Actor) -> None:
        """Run actor's message processing loop."""
        while True:
            message = await actor.mailbox.get()

            try:
                await actor.receive(message)
            except Exception as e:
                # Notify supervisor of failure
                await self.supervisor.handle_failure(actor, e)
```

### Benefits

✅ **Fault Tolerance**: Supervisor restarts failed actors
✅ **Concurrency**: Natural parallel execution
✅ **Isolation**: Each actor has private state
✅ **Location Transparency**: Actors can be local or remote
✅ **Backpressure**: Mailbox naturally handles overload

### Drawbacks

❌ **Complexity**: Actor model is conceptually different
❌ **Debugging**: Message flow can be hard to trace
❌ **Python Limitations**: No true actor model in stdlib (would need Pykka or custom)

---

## Approach 3: CQRS (Command Query Responsibility Segregation)

### Core Concept

**Separate write model (commands) from read model (queries).**

Commands change state, queries read optimized views.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Write Side (Commands)                                       │
├─────────────────────────────────────────────────────────────┤
│ Commands:                                                   │
│ - StartWorkflowCommand(description)                         │
│ - CreateWorktreeCommand(workflow_id)                        │
│ - CompleteFeatureCommand(workflow_id, feature)              │
│ - MergeWorktreeCommand(workflow_id)                         │
│                                                             │
│ Write Model (optimized for updates):                        │
│ - WorkflowAggregate                                        │
│ - WorktreeAggregate                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Publish events
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Read Side (Queries)                                         │
├─────────────────────────────────────────────────────────────┤
│ Queries:                                                    │
│ - GetWorkflowQuery(workflow_id)                            │
│ - ListActiveWorktreesQuery()                               │
│ - GetProgressQuery(workflow_id)                            │
│                                                             │
│ Read Model (denormalized for fast queries):                │
│ - DashboardView (JSON/dict)                                │
│ - MetricsView (time series)                                │
│ - AuditLogView (flat log)                                  │
└─────────────────────────────────────────────────────────────┘
```

### How It Works

```python
# Commands (write side)
@dataclass
class StartWorkflowCommand:
    workflow_id: str
    description: str

class CommandHandler:
    """Handles commands, updates write model."""

    def handle(self, command: Command) -> None:
        match command:
            case StartWorkflowCommand(wf_id, desc):
                aggregate = WorkflowAggregate(wf_id)
                aggregate.start(desc)
                aggregate.save()

                # Publish events for read side
                self.event_bus.publish(
                    WorkflowStarted(workflow_id=wf_id)
                )

# Queries (read side)
@dataclass
class GetWorkflowQuery:
    workflow_id: str

class QueryHandler:
    """Handles queries, reads from read model."""

    def handle(self, query: Query) -> Any:
        match query:
            case GetWorkflowQuery(wf_id):
                return self.dashboard_view.get(wf_id)
            case ListActiveWorktreesQuery():
                return self.worktree_view.list_active()

# Read model (projection)
class DashboardView:
    """Denormalized view optimized for dashboard queries."""

    def __init__(self, event_bus: EventBus):
        self.data = {}
        event_bus.subscribe(self._on_event)

    def _on_event(self, event: Event) -> None:
        """Update view when event arrives."""
        if isinstance(event, WorkflowStarted):
            self.data[event.workflow_id] = {
                'status': 'started',
                'progress': 0,
                # ... denormalized data
            }
```

### Benefits

✅ **Optimized Reads**: Read model shaped for UI needs
✅ **Optimized Writes**: Write model shaped for business logic
✅ **Scalability**: Can scale reads/writes independently
✅ **Flexibility**: Multiple read models for different views

### Drawbacks

❌ **Eventual Consistency**: Read model may lag behind writes
❌ **Complexity**: Managing two models
❌ **Synchronization**: Keeping models in sync

---

## Approach 4: Reactive Streams (RxPY/ReactiveX)

### Core Concept

**Everything is an observable stream. Components react to streams.**

### Architecture

```python
from rx import Observable, operators as ops

# Workflow events as observable stream
workflow_events = Observable.create(lambda observer, scheduler: ...)

# Dashboard subscribes to filtered stream
workflow_events.pipe(
    ops.filter(lambda e: e.type == 'feature.completed'),
    ops.map(lambda e: transform_for_ui(e)),
    ops.debounce(0.5)  # Avoid UI thrashing
).subscribe(lambda data: update_dashboard(data))

# Metrics collector subscribes to different stream
workflow_events.pipe(
    ops.filter(lambda e: e.type in ['workflow.started', 'workflow.completed']),
    ops.window_with_time(60.0),  # 1-minute windows
    ops.map(lambda window: window.count())
).subscribe(lambda count: record_metric('workflows_per_minute', count))
```

### Benefits

✅ **Composability**: Stream operators are composable
✅ **Backpressure**: Built-in flow control
✅ **Declarative**: Describe what, not how

### Drawbacks

❌ **Complexity**: Reactive programming has steep learning curve
❌ **Debugging**: Stream flow can be opaque
❌ **Python Support**: RxPY exists but not idiomatic

---

## Comparative Analysis

| Aspect | Event Sourcing | Actor Model | CQRS | Reactive Streams |
|--------|---------------|-------------|------|------------------|
| **Complexity** | High | Medium-High | Medium | High |
| **Real-time** | Excellent | Excellent | Good | Excellent |
| **Debugging** | Excellent (replay) | Hard (async) | Good | Hard (streams) |
| **Audit Trail** | Built-in | Manual | Manual | Manual |
| **Scalability** | Excellent | Excellent | Excellent | Good |
| **Python Fit** | Good | Poor (no stdlib) | Good | Poor (not idiomatic) |
| **Worktree Fit** | Excellent | Good | Good | Medium |
| **Learning Curve** | Steep | Steep | Medium | Very Steep |
| **Migration Path** | Complete rewrite | Complete rewrite | Incremental | Incremental |

---

## Recommendation: Event Sourcing (with pragmatic simplifications)

### Why Event Sourcing?

1. **Perfect Fit for Worktrees**
   - Worktree lifecycle is naturally event-driven
   - Events: Created → Active → Merged → Deleted
   - Easy to track which worktree is in what state

2. **Monitoring is Trivial**
   - Dashboard subscribes to event stream
   - No polling needed
   - Real-time updates automatically

3. **Debugging & Auiting**
   - Complete history of what happened
   - Can replay to reproduce issues
   - Audit trail for compliance

4. **Future-Proof**
   - Can add new projections without changing events
   - Time-travel debugging
   - A/B test different projection strategies

### Simplified Implementation (Pragmatic)

Don't need full CQRS/ES framework. Keep it simple:

```python
# events.py - Event definitions
@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str = field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str
    data: dict

# event_store.py - Simple append-only log
class EventStore:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.subscribers = []

    def append(self, event: WorkflowEvent) -> None:
        """Append event (thread-safe)."""
        log_file = self.base_path / f"{event.workflow_id}.events"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with log_file.open('a') as f:
            f.write(json.dumps(asdict(event)) + '\n')

        # Notify subscribers
        for subscriber in self.subscribers:
            subscriber(event)

    def get_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Read events for workflow."""
        log_file = self.base_path / f"{workflow_id}.events"
        if not log_file.exists():
            return []

        events = []
        with log_file.open('r') as f:
            for line in f:
                if line.strip():
                    events.append(WorkflowEvent(**json.loads(line)))
        return events

    def subscribe(self, callback: Callable[[WorkflowEvent], None]) -> None:
        """Subscribe to new events."""
        self.subscribers.append(callback)

# projection.py - Build state from events
class WorkflowProjection:
    """Current workflow state (derived from events)."""

    @staticmethod
    def build(events: list[WorkflowEvent]) -> dict:
        """Fold events into current state."""
        state = {
            'phase': 'planning',
            'features': [],
            'worktree_path': None,
            'worktree_branch': None,
            'created_at': None,
            'updated_at': None,
        }

        for event in events:
            state = WorkflowProjection._apply(state, event)

        return state

    @staticmethod
    def _apply(state: dict, event: WorkflowEvent) -> dict:
        """Apply single event to state (pure function)."""
        new_state = state.copy()

        match event.event_type:
            case "workflow.started":
                new_state['created_at'] = event.timestamp
            case "worktree.created":
                new_state['worktree_path'] = event.data['path']
                new_state['worktree_branch'] = event.data['branch']
            case "feature.completed":
                new_state['features'].append(event.data)
            case "worktree.merged":
                new_state['phase'] = 'complete'

        new_state['updated_at'] = event.timestamp
        return new_state
```

### Migration Path

**Phase 1**: Add event emission alongside current state writes
```python
# Current
state.save()

# New (both)
event_store.append(FeatureCompleted(...))
state.save()  # Keep for compatibility
```

**Phase 2**: Make dashboard read from events
```python
# Current
state = WorkflowState.load(workflow_id)

# New
events = event_store.get_events(workflow_id)
state = WorkflowProjection.build(events)
```

**Phase 3**: Remove state.json writes (events are source of truth)
```python
# Only events
event_store.append(FeatureCompleted(...))
# state.save() ← removed
```

---

## Final Architecture Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│ Execution Layer (Worktrees)                                │
├─────────────────────────────────────────────────────────────┤
│ trees/beads-y97/     trees/beads-7gq/     trees/beads-400/ │
│ (isolated code)      (isolated code)      (isolated code)  │
└────────┬────────────────────┬────────────────────┬──────────┘
         │                    │                    │
         │ emit events        │ emit events        │ emit events
         ↓                    ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Event Store (Append-Only Log)                              │
├─────────────────────────────────────────────────────────────┤
│ events/                                                     │
│ ├── beads-y97.events    (immutable event log)              │
│ ├── beads-7gq.events                                       │
│ └── beads-400.events                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         │ project into views
         ↓
┌─────────────────────────────────────────────────────────────┐
│ Projections (Materialized Views)                           │
├─────────────────────────────────────────────────────────────┤
│ DashboardView    ExecutionView    AuditLogView             │
│ (UI-optimized)   (for agents)     (compliance)             │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Worktrees provide execution isolation**
2. **Events provide temporal isolation** (can replay history)
3. **Projections provide view optimization** (different views from same events)
4. **Event store is single source of truth** (immutable, append-only)

This gives us:
- ✅ Parallel execution without conflicts
- ✅ Real-time monitoring without polling
- ✅ Complete audit trail
- ✅ Time-travel debugging
- ✅ Multiple views from single source
- ✅ Simple, testable code (pure functions)

Would you like me to prototype this architecture with a working implementation?
