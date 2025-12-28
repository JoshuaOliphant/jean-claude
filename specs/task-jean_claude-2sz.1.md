# Add Event Logging Infrastructure

**Beads Task**: jean_claude-2sz.1
**Priority**: P0
**Type**: task

## Description

Create the foundational event logging system that powers all monitoring. Events should be written to both SQLite (.jc/events.db) and JSONL (agents/{id}/events.jsonl) for different query patterns.

## Events to Support

- workflow.started, workflow.phase_changed, workflow.completed
- feature.planned, feature.started, feature.completed, feature.failed
- agent.tool_use, agent.test_result, agent.error

## Technical Approach

- Create EventLogger class in src/jean_claude/core/events.py
- Use SQLite with simple schema: id, timestamp, workflow_id, event_type, data (JSON)
- Write JSONL in parallel for streaming/tailing
- Provide async and sync interfaces

## Context

- .jc/ directory already created by jc init
- Events should be queryable for metrics and dashboards
- JSONL format enables 'tail -f' style monitoring

## Acceptance Criteria

- [ ] EventLogger class with emit() method
- [ ] Events written to .jc/events.db SQLite
- [ ] Events written to agents/{workflow_id}/events.jsonl
- [ ] Query methods: get_workflow_events(), get_recent_events()
- [ ] Unit tests for event emission and querying

## Existing Code Patterns

Follow the patterns in:
- `src/jean_claude/core/state.py` - For Pydantic models and file I/O
- `src/jean_claude/core/agent.py` - For async/sync wrapper patterns

## File Structure

```
src/jean_claude/core/events.py   # New file - EventLogger implementation
tests/test_events.py             # New file - Unit tests
```
