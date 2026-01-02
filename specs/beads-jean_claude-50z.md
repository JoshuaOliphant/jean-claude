# Epic: Event Store Foundation

## Description

Implement SQLite-based event store with ACID guarantees, event append/query operations, and snapshot-based compaction. This is Phase 1 of the event-sourcing architecture migration.

Reference: docs/ARCHITECTURE.md sections 'Core Architecture' and 'Event Store Design'.

Deliverables:
- SQLite database with events and snapshots tables
- Event store API (append, query, subscribe)
- Snapshot creation every 100 events
- Event replay with projection builder
- Comprehensive test suite

Estimated Duration: 3 days
Dependencies: None (foundation work)

## Acceptance Criteria

- EventStore.append() writes events to SQLite with ACID transactions
- EventStore.get_events() queries events with workflow_id filtering
- EventStore.subscribe() notifies callbacks when events appended
- EventStore.save_snapshot() creates snapshots in snapshots table
- EventStore.get_snapshot() retrieves latest snapshot for workflow
- EventStore.rebuild_projection() replays events from snapshot
- Auto-snapshot creation every 100 events verified
- Comprehensive test suite in tests/core/test_event_store_operations.py passes
- All event types from ARCHITECTURE.md supported in apply_event()
- Code follows existing EventStore patterns and style

---

## Task Metadata

- **Task ID**: jean_claude-50z
- **Status**: in_progress
- **Created**: 2025-12-29 08:58:58
- **Updated**: 2026-01-01 20:59:43
