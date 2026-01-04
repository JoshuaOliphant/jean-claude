# Implement NotesProjectionBuilder for note views

## Description

## Description

Create a projection builder that reconstructs note state from note events. This enables the Notes API to be a facade over the event store.

## Projection State Structure

```python
{
  "notes": [                    # All notes
    {
      "event_id": str,
      "agent_id": str,
      "category": str,          # observation, learning, decision, etc.
      "title": str,
      "content": str,
      "tags": list[str],
      "related_file": str | None,
      "related_feature": str | None,
      "created_at": datetime
    }
  ],
  "by_category": {              # Notes grouped by category
    "observation": [...],
    "learning": [...],
    "decision": [...],
    # etc.
  },
  "by_agent": {                 # Notes grouped by agent
    "planner": [...],
    "coder": [...],
    # etc.
  },
  "by_tag": {                   # Inverted index for tag search
    "auth": [...],
    "bug": [...],
    # etc.
  }
}
```

## Implementation

Create `src/jean_claude/core/notes_projection.py`:

- NotesProjectionBuilder class extending ProjectionBuilder
- apply_agent_note_observation() through apply_agent_note_todo() (7 methods)
- Build indexes: by_category, by_agent, by_tag
- Helper methods: search_notes(), filter_notes(), get_summary()

## Files to Create

- `src/jean_claude/core/notes_projection.py`
- `tests/core/test_notes_projection.py`

## Acceptance Criteria

- [ ] NotesProjectionBuilder implements all 7 note event apply methods
- [ ] Notes correctly indexed by category
- [ ] Notes correctly indexed by agent
- [ ] Tag inverted index built correctly
- [ ] Search works across title and content
- [ ] Filtering by category, agent, tags works
- [ ] Summary groups notes by category
- [ ] Tests cover all note types
- [ ] Tests verify tag search functionality
- [ ] Tests verify multi-agent note scenarios

## Dependencies

- Depends on: jean_claude-nhj (note event types)

## Agent Work Estimate

4-5 iterations (similar to mailbox projection, moderate complexity)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-81h
- **Status**: in_progress
- **Created**: 2026-01-02 21:41:33
- **Updated**: 2026-01-03 17:19:36
