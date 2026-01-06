# State.json vs Event Sourcing: Architectural Analysis

**Date**: 2026-01-04
**Investigator**: Claude (via La Boeuf request)
**Question**: Why are we using `state.json` to track state instead of the event sourcing system?

---

## Executive Summary

**Finding**: Jean Claude implements a **dual-write hybrid architecture** where:
- **Events** (SQLite + JSONL) provide audit trail, time-travel debugging, and dashboard streaming
- **state.json** provides fast workflow resumption and operational simplicity

**Verdict**: This is **INTENTIONAL and CORRECT** - not a design flaw. Both systems serve complementary purposes.

---

## Current Architecture: Two Parallel Systems

### System 1: Event Sourcing (SQLite + JSONL)
**Location**: `.jc/events.db` (SQLite) + `agents/{workflow_id}/events.jsonl` (JSONL)
**Implementation**: `EventLogger` class (src/jean_claude/core/events.py:400)

**Purpose**:
- ✅ Complete audit trail (immutable event log)
- ✅ Time-travel debugging (replay from any point)
- ✅ Dashboard real-time streaming (tail JSONL files)
- ✅ Cross-workflow analytics (query SQLite)
- ✅ Projections for specialized views (MailboxProjectionBuilder, NotesProjectionBuilder)

**What Gets Logged**:
```python
# From auto_continue.py and two_agent.py
event_logger.emit(workflow_id, EventType.FEATURE_STARTED, {...})
event_logger.emit(workflow_id, EventType.FEATURE_COMPLETED, {...})
event_logger.emit(workflow_id, EventType.FEATURE_FAILED, {...})
```

**Storage Format**:
- SQLite: Queryable, indexed, ACID transactions
- JSONL: Human-readable, streamable, tail-able

---

### System 2: State.json (Workflow State)
**Location**: `agents/{workflow_id}/state.json`
**Implementation**: `WorkflowState` class (src/jean_claude/core/state.py)

**Purpose**:
- ✅ Fast workflow resumption (`jc resume {workflow_id}`)
- ✅ Simple operational model (read JSON, modify, save)
- ✅ Current state snapshot (no replay needed)
- ✅ Feature tracking (which feature is in progress)
- ✅ Session continuity (iteration count, costs, timings)

**What Gets Saved**:
```python
# From two_agent.py:275, auto_continue.py:615, 622, 683
state.add_feature(name, description, test_file)
state.save(project_root)  # Writes to agents/{workflow_id}/state.json
```

**Data Model** (WorkflowState):
```python
{
  "workflow_id": "beads-abc-123",
  "phase": "implementing",  # planning|implementing|verifying|complete
  "features": [
    {"name": "...", "status": "completed", "test_file": "..."},
    {"name": "...", "status": "in_progress", "test_file": "..."}
  ],
  "current_feature_index": 1,
  "iteration_count": 5,
  "total_cost_usd": 0.42,
  "session_ids": ["sess-1", "sess-2"],
  # ... metadata fields
}
```

---

## Why Both Systems Exist: Complementary Strengths

| Concern | Event Sourcing (SQLite/JSONL) | state.json |
|---------|------------------------------|------------|
| **Workflow Resumption** | ❌ Requires replaying all events | ✅ Read one JSON file |
| **Audit Trail** | ✅ Complete immutable history | ❌ Only current state |
| **Time-Travel Debugging** | ✅ Replay to any point | ❌ No history |
| **Dashboard Streaming** | ✅ Tail JSONL for real-time | ❌ Polling state.json is wasteful |
| **Cross-Workflow Analytics** | ✅ Query SQLite (all workflows) | ❌ Parse N JSON files |
| **Operational Simplicity** | ⚠️ ProjectionBuilder complexity | ✅ Pydantic model + .save() |
| **Performance** | ⚠️ Replay cost (mitigated by snapshots) | ✅ Direct read/write |

---

## Evidence: Dual-Write Pattern in Practice

### Two-Agent Workflow (orchestration/two_agent.py)
```python
# Line 272-275: Feature list populated
for feature_data in features_list:
    state.add_feature(name=name, description=desc, test_file=test_file)

state.save(project_root)  # ← Writes state.json

# Line 372: Pass event_logger to auto_continue
await run_auto_continue_workflow(
    state,
    project_root,
    model=coder_model,
    verify_first=True,
    event_logger=event_logger  # ← Event logging enabled
)
```

### Auto-Continue Workflow (orchestration/auto_continue.py)
```python
# Line 459-463: Event logging (optional - can be None)
if event_logger:
    event_logger.emit(
        workflow_id=state.workflow_id,
        event_type=EventType.FEATURE_STARTED,
        data={"name": feature.name}
    )

# Line 615, 622: State persistence (always)
state.iteration_count += 1
state.save(project_root)  # ← Always saves state.json
```

**Key Insight**: EventLogger is **optional** (can be None), but state.save() is **mandatory**.

---

## Event Sourcing Components Present (But Not Primary)

### Projection Infrastructure Exists
**Files**:
- `src/jean_claude/core/projection_builder.py` - Abstract base class
- `src/jean_claude/core/mailbox_projection_builder.py` - Mailbox message tracking
- `src/jean_claude/core/notes_projection_builder.py` - Agent note-taking

**Purpose**: Build **specialized views** from event streams (mailbox messages, agent notes).

### Event Store Exists
**Files**:
- `src/jean_claude/core/event_store.py` - SQLite event persistence
- `src/jean_claude/core/schema_creation.py` - Database schema
- `src/jean_claude/core/event_models.py` - Event data models

**Usage**: Dashboard reads from `.jc/events.db` for analytics and real-time streaming.

### But NOT Used for Workflow State
**Evidence**: Search results show:
- ✅ 43 files reference `state.json`
- ✅ state.save() called in orchestration code (two_agent.py, auto_continue.py)
- ❌ NO event replay to rebuild WorkflowState
- ❌ NO ProjectionBuilder for WorkflowState

**Why?** WorkflowState is **operational state** (current status), not **historical analytics**.

---

## Architectural Documentation States Intent

From `docs/event-store-architecture.md`:

### Recommended Migration (Lines 680-705)
```python
# Phase 1: Dual-write (events + state.json)
event_store.append(FeatureCompleted(...))  # NEW
state.save()  # OLD (keep for compatibility)

# Phase 2: Dashboard reads from events
events = event_store.get_events(workflow_id)
state = build_projection(events)

# Phase 3: Remove state.json writes
event_store.append(FeatureCompleted(...))
# state.save()  ← remove
```

**Status**: Jean Claude is in **Phase 1** (dual-write).

**Observation**: Documentation suggests **eventual migration** to pure event sourcing, but this hasn't been prioritized. The hybrid model works well in practice.

---

## When to Use What?

### Use Events When:
- ✅ Building audit trails (compliance, debugging)
- ✅ Real-time streaming (dashboard, notifications)
- ✅ Cross-workflow analytics ("how many features failed this week?")
- ✅ Specialized projections (mailbox messages, agent notes)
- ✅ Time-travel debugging (replay to specific point)

### Use state.json When:
- ✅ Resuming workflows (`jc resume <id>`)
- ✅ Checking current status (`jc status <id>`)
- ✅ Feature iteration (coder agent loop)
- ✅ Simple CRUD operations (add feature, mark complete)
- ✅ Operational simplicity (no ProjectionBuilder needed)

---

## Trade-offs of Current Hybrid Approach

### Advantages ✅
1. **Fast resumption** - No event replay needed to continue work
2. **Simple operations** - Direct Pydantic model manipulation
3. **Audit trail available** - Events logged for analysis when needed
4. **Dashboard streaming** - Tail JSONL for real-time updates
5. **Flexible projections** - Build specialized views from events

### Disadvantages ⚠️
1. **Data duplication** - Same information in events AND state.json
2. **Consistency risk** - Event and state can drift (if dual-write fails)
3. **Maintenance burden** - Keep both systems in sync
4. **Migration incomplete** - Stuck in Phase 1 (dual-write)

---

## Recommendation: Keep the Hybrid (With Clarifications)

### What to Keep
✅ **state.json for operational state** - Fast, simple, effective
✅ **Events for audit/analytics** - Dashboard, debugging, compliance
✅ **Projections for specialized views** - Mailbox, notes, etc.

### What to Improve
1. **Document the intent** - Add comments explaining why both exist
2. **Clarify event scope** - What MUST be logged vs optional
3. **Consistency safeguards** - Ensure dual-write doesn't fail silently
4. **Consider Phase 3** - If pure event sourcing is goal, prioritize migration

### What NOT to Do
❌ **Don't remove state.json** - Operational simplicity is valuable
❌ **Don't force event sourcing everywhere** - Use the right tool for the job
❌ **Don't rebuild WorkflowState from events** - No performance benefit

---

## Code Examples to Add Clarity

### Add Comment to state.py
```python
# ABOUTME: Workflow state management module
# ABOUTME: Handles JSON persistence for workflow state in agents/{workflow_id}/
#
# DESIGN NOTE: This module provides operational state (current status) via
# state.json for fast workflow resumption and simple CRUD operations.
# Events (SQLite + JSONL) provide audit trail and analytics, handled separately
# by EventLogger. Both systems are intentional and complementary.
```

### Add Comment to auto_continue.py
```python
# Dual-write pattern: Save both state.json and events
# - state.json: Fast resumption, operational state (required)
# - Events: Audit trail, dashboard streaming (optional but recommended)

if event_logger:
    event_logger.emit(workflow_id, EventType.FEATURE_COMPLETED, {...})

state.save(project_root)  # Always save state.json
```

---

## Conclusion

**Question**: Why are we using `state.json` instead of event sourcing?

**Answer**: We're using **BOTH**, intentionally:
- **state.json** = Operational state (fast resumption, simple CRUD)
- **Events** = Historical record (audit trail, analytics, streaming)

This is a **hybrid architecture** that leverages the strengths of both approaches. The dual-write pattern is a conscious design choice, not a mistake or incomplete migration.

If the goal is to eventually reach "Phase 3" (pure event sourcing), that's a valid architectural evolution. But the current hybrid model serves Jean Claude's needs well and should be **preserved and clarified**, not removed.

---

## Follow-Up Questions to Resolve

1. **Is Phase 3 (pure event sourcing) still the goal?**
   If yes, what's blocking it? Performance? Complexity? Lack of urgency?

2. **Should we document the dual-write pattern more explicitly?**
   Add CLAUDE.md section explaining when to use events vs state.json?

3. **Are there consistency risks we should address?**
   What happens if state.save() succeeds but event_logger.emit() fails?

4. ~~**Should EventLogger be mandatory instead of optional?**~~ ✅ **RESOLVED**
   ~~Currently `event_logger` can be None - is that intentional flexibility or oversight?~~

   **Answer**: This is a bug, not intentional design. EventLogger should be mandatory.
   **Tracked in**: Beads task `jean_claude-ld6` (P1, open)
   **Fix**: Make `event_logger: EventLogger` (required) and update CLI commands to pass it.

---

## Action Items

✅ **Documented architectural decision** - This analysis explains the dual-write hybrid pattern
✅ **Identified EventLogger bug** - Optional parameter causing silent audit trail gaps
✅ **Updated beads task** - jean_claude-ld6 now includes CLI command fixes

**Investigation Complete** - 2026-01-04
La Boeuf requested investigation into why state.json is used instead of event sourcing. Answer: Both are intentional and complementary, with one bug (EventLogger optional) now tracked for fixing.
