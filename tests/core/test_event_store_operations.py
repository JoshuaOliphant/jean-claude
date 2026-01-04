# ABOUTME: Integration tests for complete EventStore workflows including
# ABOUTME: append, query, snapshot, and replay operations working together

"""Integration tests for complete EventStore operations.

This module tests complete workflows:
- Full event store lifecycle (append → query → snapshot → replay)
- Multi-workflow event handling
- Snapshot-based state recovery
- Event replay with projection builders
- Subscriber notifications across operations
- Transaction boundaries and error recovery
"""

import pytest
import sqlite3
from pathlib import Path
from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event, Snapshot
from jean_claude.core.projection_builder import ProjectionBuilder


class WorkflowProjectionBuilder(ProjectionBuilder):
    """Test projection builder for workflow state reconstruction."""

    def get_initial_state(self):
        """Get initial empty workflow state."""
        return {
            "workflow_id": None,
            "status": "not_started",
            "worktrees": [],
            "features": [],
            "tests_run": 0,
            "commits": 0,
            "phase": None
        }

    def apply_workflow_started(self, state, event):
        """Apply workflow started event."""
        state["workflow_id"] = event.event_data.get("workflow_id")
        state["status"] = "started"
        return state

    def apply_workflow_completed(self, state, event):
        """Apply workflow completed event."""
        state["status"] = "completed"
        return state

    def apply_workflow_failed(self, state, event):
        """Apply workflow failed event."""
        state["status"] = "failed"
        return state

    def apply_worktree_created(self, state, event):
        """Apply worktree created event."""
        worktree_path = event.event_data.get("path")
        if worktree_path:
            state["worktrees"].append({
                "path": worktree_path,
                "status": "created"
            })
        return state

    def apply_worktree_active(self, state, event):
        """Apply worktree active event."""
        worktree_path = event.event_data.get("path")
        for wt in state["worktrees"]:
            if wt["path"] == worktree_path:
                wt["status"] = "active"
        return state

    def apply_worktree_merged(self, state, event):
        """Apply worktree merged event."""
        worktree_path = event.event_data.get("path")
        for wt in state["worktrees"]:
            if wt["path"] == worktree_path:
                wt["status"] = "merged"
        return state

    def apply_worktree_deleted(self, state, event):
        """Apply worktree deleted event."""
        worktree_path = event.event_data.get("path")
        state["worktrees"] = [wt for wt in state["worktrees"] if wt["path"] != worktree_path]
        return state

    def apply_feature_planned(self, state, event):
        """Apply feature planned event."""
        feature_name = event.event_data.get("feature_name")
        if feature_name:
            state["features"].append({
                "name": feature_name,
                "status": "planned"
            })
        return state

    def apply_feature_started(self, state, event):
        """Apply feature started event."""
        feature_name = event.event_data.get("feature_name")
        for feature in state["features"]:
            if feature["name"] == feature_name:
                feature["status"] = "started"
        return state

    def apply_feature_completed(self, state, event):
        """Apply feature completed event."""
        feature_name = event.event_data.get("feature_name")
        for feature in state["features"]:
            if feature["name"] == feature_name:
                feature["status"] = "completed"
        return state

    def apply_feature_failed(self, state, event):
        """Apply feature failed event."""
        feature_name = event.event_data.get("feature_name")
        for feature in state["features"]:
            if feature["name"] == feature_name:
                feature["status"] = "failed"
        return state

    def apply_phase_changed(self, state, event):
        """Apply phase changed event."""
        state["phase"] = event.event_data.get("new_phase")
        return state

    def apply_tests_started(self, state, event):
        """Apply tests started event."""
        return state

    def apply_tests_passed(self, state, event):
        """Apply tests passed event."""
        state["tests_run"] += 1
        return state

    def apply_tests_failed(self, state, event):
        """Apply tests failed event."""
        state["tests_run"] += 1
        return state

    def apply_commit_created(self, state, event):
        """Apply commit created event."""
        state["commits"] += 1
        return state

    def apply_commit_failed(self, state, event):
        """Apply commit failed event."""
        return state


class TestCompleteEventStoreLifecycle:
    """Test complete event store lifecycle from start to finish."""

    def test_full_workflow_lifecycle(self, tmp_path):
        """Test complete workflow: append → query → snapshot → replay."""
        db_path = tmp_path / "integration_test.db"
        event_store = EventStore(db_path)

        workflow_id = "integration-workflow-001"

        # Step 1: Append events
        events = [
            Event(
                workflow_id=workflow_id,
                event_type="workflow.started",
                event_data={"workflow_id": workflow_id}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="worktree.created",
                event_data={"path": "/tmp/worktree-1"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.planned",
                event_data={"feature_name": "authentication"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.started",
                event_data={"feature_name": "authentication"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="tests.passed",
                event_data={"test_count": 5}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="commit.created",
                event_data={"commit_hash": "abc123"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.completed",
                event_data={"feature_name": "authentication"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="workflow.completed",
                event_data={}
            ),
        ]

        for event in events:
            result = event_store.append(event)
            assert result is True

        # Step 2: Query events back
        retrieved_events = event_store.get_events(workflow_id)
        assert len(retrieved_events) == 8
        assert retrieved_events[0].event_type == "workflow.started"
        assert retrieved_events[-1].event_type == "workflow.completed"

        # Step 3: Create snapshot after some events
        builder = WorkflowProjectionBuilder()
        partial_state = event_store.rebuild_projection(workflow_id, builder)

        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data=partial_state,
            event_sequence_number=len(retrieved_events)
        )
        result = event_store.save_snapshot(snapshot)
        assert result is True

        # Step 4: Retrieve snapshot
        retrieved_snapshot = event_store.get_snapshot(workflow_id)
        assert retrieved_snapshot is not None
        assert retrieved_snapshot.workflow_id == workflow_id
        assert retrieved_snapshot.snapshot_data["status"] == "completed"

        # Step 5: Replay from snapshot (should get same state)
        replayed_state = event_store.rebuild_projection(workflow_id, builder)
        assert replayed_state["status"] == "completed"
        assert replayed_state["workflow_id"] == workflow_id
        assert len(replayed_state["features"]) == 1
        assert replayed_state["features"][0]["name"] == "authentication"
        assert replayed_state["features"][0]["status"] == "completed"
        assert replayed_state["tests_run"] == 1
        assert replayed_state["commits"] == 1


class TestMultiWorkflowOperations:
    """Test event store with multiple concurrent workflows."""

    def test_multiple_workflows_isolated(self, tmp_path):
        """Test that multiple workflows are properly isolated."""
        db_path = tmp_path / "multi_workflow.db"
        event_store = EventStore(db_path)

        # Create events for multiple workflows
        workflow_1 = "workflow-001"
        workflow_2 = "workflow-002"
        workflow_3 = "workflow-003"

        for wf_id in [workflow_1, workflow_2, workflow_3]:
            for i in range(5):
                event = Event(
                    workflow_id=wf_id,
                    event_type=f"event.type.{i}",
                    event_data={"index": i, "workflow": wf_id}
                )
                event_store.append(event)

        # Query each workflow separately
        events_1 = event_store.get_events(workflow_1)
        events_2 = event_store.get_events(workflow_2)
        events_3 = event_store.get_events(workflow_3)

        # Verify isolation
        assert len(events_1) == 5
        assert len(events_2) == 5
        assert len(events_3) == 5

        # Verify correct workflow_id in each
        assert all(e.workflow_id == workflow_1 for e in events_1)
        assert all(e.workflow_id == workflow_2 for e in events_2)
        assert all(e.workflow_id == workflow_3 for e in events_3)

        # Verify no cross-contamination
        assert all(e.event_data["workflow"] == workflow_1 for e in events_1)
        assert all(e.event_data["workflow"] == workflow_2 for e in events_2)
        assert all(e.event_data["workflow"] == workflow_3 for e in events_3)

    def test_multiple_workflows_with_snapshots(self, tmp_path):
        """Test snapshot creation and retrieval for multiple workflows."""
        db_path = tmp_path / "multi_snapshot.db"
        event_store = EventStore(db_path)
        builder = WorkflowProjectionBuilder()

        # Create different states for different workflows
        workflows = {
            "wf-alpha": ["workflow.started", "feature.planned", "feature.started"],
            "wf-beta": ["workflow.started", "workflow.completed"],
            "wf-gamma": ["workflow.started", "feature.planned"]
        }

        for wf_id, event_types in workflows.items():
            for event_type in event_types:
                event = Event(
                    workflow_id=wf_id,
                    event_type=event_type,
                    event_data={"workflow_id": wf_id}
                )
                event_store.append(event)

            # Create snapshot for each workflow
            state = event_store.rebuild_projection(wf_id, builder)
            snapshot = Snapshot(
                workflow_id=wf_id,
                snapshot_data=state,
                event_sequence_number=len(event_types)
            )
            event_store.save_snapshot(snapshot)

        # Retrieve and verify each snapshot
        snapshot_alpha = event_store.get_snapshot("wf-alpha")
        snapshot_beta = event_store.get_snapshot("wf-beta")
        snapshot_gamma = event_store.get_snapshot("wf-gamma")

        assert snapshot_alpha.snapshot_data["status"] == "started"
        assert snapshot_beta.snapshot_data["status"] == "completed"
        assert snapshot_gamma.snapshot_data["status"] == "started"


class TestSnapshotBasedRecovery:
    """Test state recovery from snapshots."""

    def test_replay_from_snapshot_with_new_events(self, tmp_path):
        """Test replaying events from snapshot point with new events."""
        db_path = tmp_path / "snapshot_recovery.db"
        event_store = EventStore(db_path)
        builder = WorkflowProjectionBuilder()

        workflow_id = "recovery-workflow"

        # Add initial events
        initial_events = [
            Event(workflow_id=workflow_id, event_type="workflow.started", event_data={"workflow_id": workflow_id}),
            Event(workflow_id=workflow_id, event_type="feature.planned", event_data={"feature_name": "feature-1"}),
            Event(workflow_id=workflow_id, event_type="feature.started", event_data={"feature_name": "feature-1"}),
        ]

        for event in initial_events:
            event_store.append(event)

        # Create snapshot after initial events
        state_at_snapshot = event_store.rebuild_projection(workflow_id, builder)
        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data=state_at_snapshot,
            event_sequence_number=len(initial_events)
        )
        event_store.save_snapshot(snapshot)

        # Add more events after snapshot
        new_events = [
            Event(workflow_id=workflow_id, event_type="tests.passed", event_data={}),
            Event(workflow_id=workflow_id, event_type="commit.created", event_data={}),
            Event(workflow_id=workflow_id, event_type="feature.completed", event_data={"feature_name": "feature-1"}),
        ]

        for event in new_events:
            event_store.append(event)

        # Rebuild state from snapshot + new events
        final_state = event_store.rebuild_projection(workflow_id, builder)

        # Verify state includes both snapshot and new events
        assert final_state["status"] == "started"
        assert len(final_state["features"]) == 1
        assert final_state["features"][0]["status"] == "completed"
        assert final_state["tests_run"] == 1
        assert final_state["commits"] == 1


class TestSubscriberIntegration:
    """Test subscriber notifications across operations."""

    def test_subscribers_notified_on_append(self, tmp_path):
        """Test that subscribers are notified when events are appended."""
        db_path = tmp_path / "subscriber_test.db"
        event_store = EventStore(db_path)

        notifications = []

        def subscriber_callback(event):
            notifications.append(event)

        event_store.subscribe(subscriber_callback)

        workflow_id = "subscriber-workflow"

        # Append events
        events = [
            Event(workflow_id=workflow_id, event_type="event.1", event_data={}),
            Event(workflow_id=workflow_id, event_type="event.2", event_data={}),
            Event(workflow_id=workflow_id, event_type="event.3", event_data={}),
        ]

        for event in events:
            event_store.append(event)

        # Verify subscribers were notified
        assert len(notifications) == 3
        assert notifications[0].event_type == "event.1"
        assert notifications[1].event_type == "event.2"
        assert notifications[2].event_type == "event.3"

    def test_subscribers_notified_on_batch_append(self, tmp_path):
        """Test that subscribers are notified for batch appends."""
        db_path = tmp_path / "batch_subscriber_test.db"
        event_store = EventStore(db_path)

        notifications = []

        def subscriber_callback(event):
            notifications.append(event)

        event_store.subscribe(subscriber_callback)

        workflow_id = "batch-subscriber-workflow"

        # Batch append events
        events = [
            Event(workflow_id=workflow_id, event_type=f"batch.event.{i}", event_data={"index": i})
            for i in range(5)
        ]

        event_store.append_batch(events)

        # Verify all batch events triggered notifications
        assert len(notifications) == 5
        for i, notification in enumerate(notifications):
            assert notification.event_type == f"batch.event.{i}"
            assert notification.event_data["index"] == i


class TestTransactionBoundaries:
    """Test transaction handling and error recovery."""

    def test_batch_append_atomicity(self, tmp_path):
        """Test that batch append is atomic (all-or-nothing)."""
        db_path = tmp_path / "atomicity_test.db"
        event_store = EventStore(db_path)

        workflow_id = "atomic-workflow"

        # First batch - all valid
        valid_events = [
            Event(workflow_id=workflow_id, event_type="valid.1", event_data={}),
            Event(workflow_id=workflow_id, event_type="valid.2", event_data={}),
        ]

        result = event_store.append_batch(valid_events)
        assert result is True

        # Verify valid events were stored
        stored_events = event_store.get_events(workflow_id)
        assert len(stored_events) == 2

        # Second batch - contains invalid event (should rollback all)
        mixed_events = [
            Event(workflow_id=workflow_id, event_type="mixed.1", event_data={}),
            None,  # Invalid event
            Event(workflow_id=workflow_id, event_type="mixed.2", event_data={}),
        ]

        result = event_store.append_batch(mixed_events)
        assert result is False

        # Verify NO events from failed batch were stored
        stored_events = event_store.get_events(workflow_id)
        assert len(stored_events) == 2  # Still only the first 2

    def test_error_recovery_continues_operation(self, tmp_path):
        """Test that event store continues working after errors."""
        db_path = tmp_path / "error_recovery_test.db"
        event_store = EventStore(db_path)

        workflow_id = "recovery-test-workflow"

        # Successful append
        event1 = Event(workflow_id=workflow_id, event_type="event.1", event_data={})
        result = event_store.append(event1)
        assert result is True

        # Failed append (None)
        result = event_store.append(None)
        assert result is False

        # Successful append after failure
        event2 = Event(workflow_id=workflow_id, event_type="event.2", event_data={})
        result = event_store.append(event2)
        assert result is True

        # Verify both successful events were stored
        stored_events = event_store.get_events(workflow_id)
        assert len(stored_events) == 2
        assert stored_events[0].event_type == "event.1"
        assert stored_events[1].event_type == "event.2"


class TestPaginationWithProjections:
    """Test pagination working correctly with projection rebuilding."""

    def test_paginated_replay(self, tmp_path):
        """Test that pagination works correctly when rebuilding projections."""
        db_path = tmp_path / "pagination_replay.db"
        event_store = EventStore(db_path)
        builder = WorkflowProjectionBuilder()

        workflow_id = "pagination-workflow"

        # Add many events
        for i in range(50):
            event = Event(
                workflow_id=workflow_id,
                event_type="feature.planned",
                event_data={"feature_name": f"feature-{i}"}
            )
            event_store.append(event)

        # Rebuild projection from all events
        full_state = event_store.rebuild_projection(workflow_id, builder)
        assert len(full_state["features"]) == 50

        # Query with pagination
        first_10_events = event_store.get_events(workflow_id, limit=10)
        assert len(first_10_events) == 10

        next_10_events = event_store.get_events(workflow_id, limit=10, offset=10)
        assert len(next_10_events) == 10
        assert first_10_events[0].id != next_10_events[0].id
