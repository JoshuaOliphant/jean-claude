# Add note event types to event store

## Description

## Description

Add event types for agent notes to the event store. This replaces the notes.jsonl file system with event-based note storage, enabling notes to benefit from event sourcing (replay, snapshots, ACID guarantees).

## Event Types to Add

1. `agent.note.observation` - Agent records an observation
2. `agent.note.learning` - Agent records something learned
3. `agent.note.decision` - Agent records a decision made
4. `agent.note.warning` - Agent records a warning
5. `agent.note.accomplishment` - Agent records work completed
6. `agent.note.context` - Agent records background context
7. `agent.note.todo` - Agent records a task for later

## Event Data Schema

```python
# All agent.note.* events
{
  "agent_id": str,           # Agent creating note
  "title": str,              # Brief title
  "content": str,            # Full content
  "tags": list[str],         # Tags for categorization
  "related_file": str | None,     # Optional file path
  "related_feature": str | None   # Optional feature name
}
```

## Files to Modify

- `src/jean_claude/core/event_models.py` - Add note event type constants
- `src/jean_claude/core/projection_builder.py` - Add abstract methods for note events
- Update all ProjectionBuilder test fixtures

## Acceptance Criteria

- [ ] All 7 note event types defined
- [ ] Event data schema validates with Pydantic
- [ ] ProjectionBuilder has methods: apply_agent_note_observation, apply_agent_note_learning, etc. (7 total)
- [ ] All existing tests pass
- [ ] Can write and read note events from event store
- [ ] Tags properly stored and retrieved

## Dependencies

- Depends on: jean_claude-di8 (message event types)

## Agent Work Estimate

2-3 iterations (similar to message events, well-defined)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-nhj
- **Status**: in_progress
- **Created**: 2026-01-02 21:40:56
- **Updated**: 2026-01-03 08:04:49
