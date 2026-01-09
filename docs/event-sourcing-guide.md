# Event Sourcing: A Guide for Junior Engineers

This document explains event sourcing principles and how we use them in Jean Claude. By the end, you'll understand *why* we chose this pattern and *how* to work with it effectively.

---

## Table of Contents

1. [What Problem Are We Solving?](#what-problem-are-we-solving)
2. [The Traditional Approach vs Event Sourcing](#the-traditional-approach-vs-event-sourcing)
3. [Core Concepts](#core-concepts)
4. [How Jean Claude Uses Event Sourcing](#how-jean-claude-uses-event-sourcing)
5. [Practical Examples](#practical-examples)
6. [Common Patterns](#common-patterns)
7. [When to Use Event Sourcing](#when-to-use-event-sourcing)
8. [Further Reading](#further-reading)

---

## What Problem Are We Solving?

Imagine you're building a workflow system where AI agents collaborate on coding tasks. You need to track:
- What happened during the workflow?
- In what order did things happen?
- What decisions were made and why?
- If something went wrong, how do we debug it?

**The naive approach** is to store "current state" in a file:

```json
{
  "workflow_id": "abc-123",
  "status": "completed",
  "features_completed": 5,
  "last_updated": "2026-01-09T10:00:00"
}
```

This tells you *where you are*, but not *how you got there*. You lose the story.

**Event sourcing** flips this around. Instead of storing current state, we store *every change that happened*:

```json
{"event": "workflow.started", "timestamp": "2026-01-09T09:00:00"}
{"event": "feature.planned", "name": "auth-system", "timestamp": "2026-01-09T09:05:00"}
{"event": "feature.started", "name": "auth-system", "timestamp": "2026-01-09T09:10:00"}
{"event": "feature.completed", "name": "auth-system", "timestamp": "2026-01-09T09:45:00"}
...
```

Now we have the complete story. We can answer questions like:
- "How long did each feature take?"
- "What was happening at 9:30?"
- "Did we retry any features?"

---

## The Traditional Approach vs Event Sourcing

Let's compare with a concrete example: tracking a shopping cart.

### Traditional Approach (CRUD)

Store current state, update in place:

```python
# Shopping cart state
cart = {
    "items": [
        {"product": "laptop", "quantity": 1, "price": 999},
        {"product": "mouse", "quantity": 2, "price": 25}
    ],
    "total": 1049
}

# When user adds an item:
def add_item(cart, product, quantity, price):
    cart["items"].append({"product": product, "quantity": quantity, "price": price})
    cart["total"] += quantity * price
    save_to_database(cart)  # Overwrites previous state
```

**What you know:** Current cart contents.
**What you lose:** The user first added a laptop, then removed it, then added it back, then added two mice.

### Event Sourcing Approach

Store every change as an immutable event:

```python
# Events (never modified, only appended)
events = [
    {"type": "item_added", "product": "laptop", "quantity": 1, "price": 999, "time": "10:00"},
    {"type": "item_removed", "product": "laptop", "quantity": 1, "time": "10:05"},
    {"type": "item_added", "product": "laptop", "quantity": 1, "price": 999, "time": "10:10"},
    {"type": "item_added", "product": "mouse", "quantity": 2, "price": 25, "time": "10:15"}
]

# To get current state, replay all events:
def get_cart_state(events):
    cart = {"items": [], "total": 0}
    for event in events:
        if event["type"] == "item_added":
            cart["items"].append(...)
            cart["total"] += event["quantity"] * event["price"]
        elif event["type"] == "item_removed":
            # Remove item, adjust total
            pass
    return cart
```

**What you know:** Current cart contents AND the complete history.
**Benefits:**
- "What did the cart look like at 10:07?" - Replay events up to that time
- "How many times did users change their mind?" - Count add/remove pairs
- "Undo" is trivial - don't replay the last event

---

## Core Concepts

### 1. Events Are Immutable Facts

An event is something that **happened**. It's a fact about the past. You can't change the past.

```python
# This is an event - a fact about what happened
event = Event(
    id="uuid-123",
    timestamp="2026-01-09T10:00:00",
    event_type="feature.completed",
    data={"name": "auth-system", "agent_id": "coder-001"}
)

# Events are NEVER modified
# ❌ event.data["name"] = "new-name"  # WRONG - never do this
# ✅ emit a new "feature.renamed" event instead
```

**Key insight:** Events describe what happened, not what *should* happen. Use past tense:
- ✅ `feature.completed` (past tense - it happened)
- ❌ `complete.feature` (imperative - a command, not an event)

### 2. State Is Derived, Not Stored

Instead of storing state directly, we **derive** state by replaying events:

```python
def derive_state(events: list[Event]) -> WorkflowState:
    """Build current state by replaying all events."""
    state = WorkflowState()  # Start with empty state

    for event in events:
        if event.type == "workflow.started":
            state.status = "running"
        elif event.type == "feature.completed":
            state.completed_features.append(event.data["name"])
        elif event.type == "workflow.completed":
            state.status = "completed"

    return state
```

This means:
- State can always be rebuilt from events
- If your state code has a bug, fix it and replay - you get correct state
- You never lose data (events are the source of truth)

### 3. Append-Only Storage

Events are only ever **appended**. Never updated, never deleted.

```
events.jsonl (append-only log):
{"id": 1, "type": "started", ...}
{"id": 2, "type": "feature.planned", ...}
{"id": 3, "type": "feature.completed", ...}  ← only add new lines
```

**Why append-only?**
- Simpler concurrency (no conflicts when two processes write)
- Natural audit trail
- Time-travel debugging (replay to any point)
- Crash recovery (partially written event = skip it)

### 4. Projections (Read Models)

Replaying all events every time would be slow. A **projection** is a pre-computed view optimized for a specific use case:

```python
# Projection: Notes indexed by category
{
    "notes": [note1, note2, note3, ...],
    "by_category": {
        "learning": [0, 2],      # indices into notes array
        "decision": [1],
        "warning": []
    },
    "by_agent": {
        "coder-agent": [0, 1, 2]
    }
}
```

Each projection is built by a **projection builder** that knows how to handle events:

```python
class NotesProjectionBuilder:
    def apply_event(self, state: dict, event: Event) -> dict:
        """Apply one event and return new state."""
        if event.type == "agent.note.learning":
            # Add note, update indexes
            new_state = copy.deepcopy(state)
            new_state["notes"].append(event.data)
            new_state["by_category"]["learning"].append(len(new_state["notes"]) - 1)
            return new_state
        return state
```

### 5. Snapshots (Performance Optimization)

As events accumulate, replaying from the beginning gets slow. A **snapshot** captures state at a point in time:

```
Event Stream:
[E1] [E2] [E3] ... [E100] [SNAPSHOT] [E101] [E102] ... [E150]
                      ↑
              Save state here

To rebuild current state:
1. Load snapshot (state at E100)
2. Replay only E101-E150 (50 events instead of 150)
```

In Jean Claude, we snapshot every 100 events:

```python
def rebuild_state(workflow_id: str) -> dict:
    # 1. Try to load snapshot
    snapshot = get_snapshot(workflow_id)

    if snapshot:
        state = snapshot.data
        events = get_events_after(snapshot.sequence_number)
    else:
        state = initial_state()
        events = get_all_events()

    # 2. Replay remaining events
    for event in events:
        state = apply_event(state, event)

    return state
```

---

## How Jean Claude Uses Event Sourcing

### Dual-Persistence Architecture

Jean Claude writes events to **two places** simultaneously:

```
┌─────────────────────────────────────────────────────────────────┐
│  Event Emission                                                 │
│  (notes.add_learning(...))                                      │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
           ┌────────────┴────────────┐
           │                         │
           ▼                         ▼
┌──────────────────────┐  ┌──────────────────────────────────────┐
│  SQLite Database     │  │  JSONL File                          │
│  .jc/events.db       │  │  agents/{workflow_id}/events.jsonl   │
│                      │  │                                      │
│  ✅ Indexed queries  │  │  ✅ Human-readable                   │
│  ✅ Cross-workflow   │  │  ✅ tail -f for monitoring           │
│  ✅ ACID transactions│  │  ✅ Per-workflow isolation           │
└──────────────────────┘  └──────────────────────────────────────┘
```

**Why two?**
- **SQLite**: Fast queries, indexes, dashboard analytics
- **JSONL**: Human-readable, easy debugging, real-time tailing

### Event Types in Jean Claude

We have ~26 event types organized by category:

```python
class EventType(str, Enum):
    # Workflow lifecycle
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PHASE_CHANGED = "workflow.phase_changed"
    WORKFLOW_COMPLETED = "workflow.completed"

    # Feature tracking
    FEATURE_PLANNED = "feature.planned"
    FEATURE_STARTED = "feature.started"
    FEATURE_COMPLETED = "feature.completed"
    FEATURE_FAILED = "feature.failed"

    # Agent notes (10 types)
    AGENT_NOTE_OBSERVATION = "agent.note.observation"
    AGENT_NOTE_LEARNING = "agent.note.learning"
    AGENT_NOTE_DECISION = "agent.note.decision"
    # ... etc
```

### The Notes System: A Concrete Example

The agent notes system is pure event sourcing. Here's the full flow:

**Step 1: Agent records a note**
```python
from jean_claude.core.notes_api import Notes
from jean_claude.core.events import EventLogger

# Setup
event_logger = EventLogger(project_root)
notes = Notes(workflow_id="my-workflow", base_dir=project_root / "agents")

# Record a learning
notes.add_learning(
    agent_id="coder-agent",
    title="Auth uses JWT tokens",
    content="All API routes validate JWT tokens via middleware",
    tags=["auth", "security"],
    event_logger=event_logger  # Enables event emission
)
```

**Step 2: Event is emitted**
```python
# Internally, this creates an event:
Event(
    id=UUID("abc-123"),
    timestamp=datetime.now(),
    workflow_id="my-workflow",
    event_type=EventType.AGENT_NOTE_LEARNING,
    data={
        "agent_id": "coder-agent",
        "title": "Auth uses JWT tokens",
        "content": "All API routes validate JWT tokens via middleware",
        "tags": ["auth", "security"]
    }
)
```

**Step 3: Event is persisted**
```sql
-- SQLite
INSERT INTO events (id, timestamp, workflow_id, event_type, data)
VALUES ('abc-123', '2026-01-09T10:00:00', 'my-workflow',
        'agent.note.learning', '{"agent_id": "coder-agent", ...}');
```

```json
// JSONL (appended)
{"id": "abc-123", "timestamp": "2026-01-09T10:00:00", "event_type": "agent.note.learning", ...}
```

**Step 4: Dashboard queries**
```python
# Dashboard rebuilds projection to show notes
projection = event_store.rebuild_projection(
    workflow_id="my-workflow",
    builder=NotesProjectionBuilder()
)

# Result:
{
    "notes": [{"title": "Auth uses JWT tokens", ...}],
    "by_category": {"learning": [0]},
    "by_agent": {"coder-agent": [0]},
    "by_tag": {"auth": [0], "security": [0]}
}
```

---

## Practical Examples

### Example 1: Adding a New Note Type

Say we want to add a "blocker" note category for issues blocking progress.

**Step 1: Add the event type** (`events.py`)
```python
class EventType(str, Enum):
    # ... existing types ...
    AGENT_NOTE_BLOCKER = "agent.note.blocker"  # NEW
```

**Step 2: Add projection handler** (`notes_projection_builder.py`)
```python
class NotesProjectionBuilder(ProjectionBuilder):
    def apply_agent_note_blocker(self, state: dict, event: Event) -> dict:
        """Handle blocker notes."""
        new_state = copy.deepcopy(state)
        note = {
            "category": "blocker",
            "agent_id": event.data["agent_id"],
            "title": event.data["title"],
            "content": event.data["content"],
            "timestamp": event.timestamp
        }
        new_state["notes"].append(note)
        # Update indexes...
        return new_state
```

**Step 3: Add API method** (`notes_api.py`)
```python
class Notes:
    def add_blocker(self, agent_id: str, title: str, content: str, **kwargs):
        """Record a blocker that's preventing progress."""
        self._emit_note(
            event_type=EventType.AGENT_NOTE_BLOCKER,
            agent_id=agent_id,
            title=title,
            content=content,
            **kwargs
        )
```

**Step 4: Use it!**
```python
notes.add_blocker(
    agent_id="coder-agent",
    title="Waiting for API credentials",
    content="Cannot test OAuth flow without production API keys"
)
```

### Example 2: Querying Events

```python
from jean_claude.core.events import EventLogger, EventType

logger = EventLogger(project_root)

# Get all events for a workflow
all_events = logger.get_workflow_events("my-workflow")

# Filter by event type
completions = logger.get_workflow_events(
    "my-workflow",
    event_types=[EventType.FEATURE_COMPLETED]
)

# Calculate duration of each feature
feature_times = {}
for event in all_events:
    if event.event_type == EventType.FEATURE_STARTED:
        feature_times[event.data["name"]] = {"start": event.timestamp}
    elif event.event_type == EventType.FEATURE_COMPLETED:
        name = event.data["name"]
        if name in feature_times:
            feature_times[name]["end"] = event.timestamp
            feature_times[name]["duration"] = (
                event.timestamp - feature_times[name]["start"]
            )

# Now you can answer: "How long did auth-system take?"
```

### Example 3: Time-Travel Debugging

One of the killer features of event sourcing is time-travel:

```python
def get_state_at_time(workflow_id: str, target_time: datetime) -> dict:
    """Rebuild state as it was at a specific point in time."""
    all_events = logger.get_workflow_events(workflow_id)

    # Filter to events before target time
    events_before = [e for e in all_events if e.timestamp <= target_time]

    # Replay only those events
    state = initial_state()
    for event in events_before:
        state = apply_event(state, event)

    return state

# What was the state at 9:30?
past_state = get_state_at_time("my-workflow", datetime(2026, 1, 9, 9, 30))
```

This is invaluable for debugging: "The agent made a bad decision at 9:45. What state did it see that led to that decision?"

---

## Common Patterns

### Pattern 1: Event Naming Convention

Use consistent naming:
```
{domain}.{entity}.{past_tense_verb}

Examples:
- workflow.started (not workflow.start)
- feature.completed (not feature.complete)
- agent.note.learning (category as "verb")
```

### Pattern 2: Event Payload Design

Include enough context to rebuild state without external lookups:

```python
# ❌ BAD - requires looking up feature details
{"type": "feature.completed", "feature_id": "abc-123"}

# ✅ GOOD - self-contained
{
    "type": "feature.completed",
    "feature_id": "abc-123",
    "name": "auth-system",
    "description": "Implement JWT authentication",
    "files_changed": ["auth.py", "middleware.py"],
    "tests_passed": 12
}
```

### Pattern 3: Idempotent Event Handlers

Projection handlers should be **idempotent** - applying the same event twice should have the same effect as applying it once:

```python
# ❌ BAD - not idempotent
def apply_feature_completed(state, event):
    state["completed_count"] += 1  # Duplicates cause wrong count!
    return state

# ✅ GOOD - idempotent
def apply_feature_completed(state, event):
    feature_id = event.data["feature_id"]
    if feature_id not in state["completed_features"]:
        state["completed_features"].add(feature_id)
        state["completed_count"] = len(state["completed_features"])
    return state
```

### Pattern 4: Correlation IDs for Tracing

Link related events with correlation IDs:

```python
# Request starts with a correlation_id
correlation_id = str(uuid4())

emit_event(EventType.FEATURE_STARTED, data={
    "correlation_id": correlation_id,
    "name": "auth-system"
})

# All related events share it
emit_event(EventType.AGENT_TOOL_USE, data={
    "correlation_id": correlation_id,
    "tool": "edit_file",
    "file": "auth.py"
})

emit_event(EventType.FEATURE_COMPLETED, data={
    "correlation_id": correlation_id,
    "name": "auth-system"
})

# Now you can trace: "What happened during auth-system implementation?"
events = [e for e in all_events if e.data.get("correlation_id") == correlation_id]
```

---

## When to Use Event Sourcing

### Good Fit

Event sourcing is excellent when you need:

1. **Complete audit trail** - "What happened and when?"
2. **Debugging complex workflows** - "Why did the agent do that?"
3. **Analytics on historical data** - "How long do features typically take?"
4. **Undo/replay capability** - "Revert to state before the bug"
5. **Multiple read models** - Dashboard shows different views of same data

### Not Always Needed

Event sourcing adds complexity. Consider simpler approaches when:

1. **Simple CRUD operations** - Just updating a user profile? CRUD is fine.
2. **No audit requirements** - If you don't need history, don't store it.
3. **High-frequency updates** - 1000 updates/second might be too much.
4. **Querying current state only** - If you never need history, just store state.

### Jean Claude's Sweet Spot

For Jean Claude, event sourcing is perfect because:
- Workflows are long-running (hours) with many steps
- We need to debug agent decisions
- Multiple agents need to see each other's notes
- The dashboard shows real-time progress
- We need to answer "what happened?" after the fact

---

## Further Reading

### In This Repository
- [Event Store Architecture](event-store-architecture.md) - Deep technical details
- [Agent Note-Taking System](../CLAUDE.md#agent-note-taking-system) - Notes API usage

### External Resources
- [Martin Fowler: Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) - Canonical explanation
- [Greg Young: CQRS and Event Sourcing](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf) - The original paper

### Key Files in Jean Claude

| File | Purpose |
|------|---------|
| `src/jean_claude/core/events.py` | Event model, EventLogger, writers |
| `src/jean_claude/core/event_store.py` | Query engine, projection rebuilding |
| `src/jean_claude/core/projection_builder.py` | Base class for projections |
| `src/jean_claude/core/notes_projection_builder.py` | Notes-specific projection |
| `src/jean_claude/core/notes_api.py` | High-level Notes API |

---

## Summary

**Event sourcing is about storing facts, not state.**

1. **Events are immutable** - Record what happened, never change it
2. **State is derived** - Replay events to build current state
3. **Append-only storage** - Simple, safe, auditable
4. **Projections optimize reads** - Pre-compute views for fast queries
5. **Snapshots optimize replays** - Don't replay from the beginning every time

In Jean Claude:
- Events go to SQLite (queries) and JSONL (debugging)
- Notes system is pure event sourcing
- Dashboard rebuilds projections from events
- Complete workflow history enables debugging and analytics

The investment in event sourcing pays off when you need to answer: "What happened, when, and why?"
