# ABOUTME: Test suite for EventStore event replay system with projection rebuilding
# ABOUTME: Tests EventStore.rebuild_projection() method to replay events from latest snapshot

"""Test suite for EventStore event replay functionality.

This module comprehensively tests the event replay system, including:

- EventStore.rebuild_projection() method functionality
- Loading snapshots and replaying subsequent events
- Integration with ProjectionBuilder to apply events sequentially
- Edge cases: no snapshot, empty events, full replay scenarios
- Multiple workflow isolation and state management
- Error handling and validation during replay

The tests follow TDD principles and use existing fixtures to ensure consistency
with the overall test suite.
"""

import sqlite3
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from datetime import datetime
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event, Snapshot
from jean_claude.core.projection_builder import ProjectionBuilder


class TestEventReplayBasic:
    """Test basic functionality of event replay system."""

    @pytest.fixture
    def concrete_builder(self):
        """Provide a concrete ProjectionBuilder implementation for testing."""

        class TestProjectionBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {
                    'workflow_id': None,
                    'phase': 'unknown',
                    'features': [],
                    'worktree_path': None,
                    'status': 'unknown',
                    'event_count': 0
                }

            def apply_workflow_started(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'workflow_id': event.workflow_id,
                    'phase': 'planning',
                    'status': 'active',
                    'description': event.event_data.get('description'),
                    'beads_task_id': event.event_data.get('beads_task_id'),
                    'started_at': event.timestamp,
                    'event_count': state['event_count'] + 1
                })
                return new_state

            def apply_workflow_completed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'phase': 'complete',
                    'status': 'completed',
                    'completed_at': event.timestamp,
                    'duration_ms': event.event_data.get('duration_ms'),
                    'total_cost': event.event_data.get('total_cost'),
                    'event_count': state['event_count'] + 1
                })
                return new_state

            def apply_workflow_failed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'status': 'failed',
                    'error': event.event_data.get('error'),
                    'failed_phase': event.event_data.get('phase'),
                    'failed_at': event.timestamp,
                    'event_count': state['event_count'] + 1
                })
                return new_state

            def apply_worktree_created(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'worktree_path': event.event_data.get('path'),
                    'worktree_branch': event.event_data.get('branch'),
                    'base_commit': event.event_data.get('base_commit'),
                    'event_count': state['event_count'] + 1
                })
                return new_state

            def apply_feature_planned(self, state, event):
                new_state = state.copy()
                features = new_state.get('features', []).copy()
                features.append({
                    'name': event.event_data['name'],
                    'description': event.event_data['description'],
                    'test_file': event.event_data.get('test_file'),
                    'status': 'planned',
                    'tests_passing': False
                })
                new_state['features'] = features
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_feature_started(self, state, event):
                new_state = state.copy()
                features = new_state.get('features', []).copy()
                for feature in features:
                    if feature['name'] == event.event_data['name']:
                        feature['status'] = 'in_progress'
                        feature['started_at'] = event.timestamp
                        break
                new_state['features'] = features
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_feature_completed(self, state, event):
                new_state = state.copy()
                features = new_state.get('features', []).copy()
                for feature in features:
                    if feature['name'] == event.event_data['name']:
                        feature['status'] = 'completed'
                        feature['tests_passing'] = event.event_data.get('tests_passing', False)
                        feature['completed_at'] = event.timestamp
                        break
                new_state['features'] = features
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_feature_failed(self, state, event):
                new_state = state.copy()
                features = new_state.get('features', []).copy()
                for feature in features:
                    if feature['name'] == event.event_data['name']:
                        feature['status'] = 'failed'
                        feature['error'] = event.event_data.get('error')
                        feature['failed_at'] = event.timestamp
                        break
                new_state['features'] = features
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_phase_changed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'previous_phase': event.event_data.get('from_phase'),
                    'phase': event.event_data.get('to_phase'),
                    'phase_changed_at': event.timestamp,
                    'event_count': state['event_count'] + 1
                })
                return new_state

            def apply_worktree_active(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_worktree_merged(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_worktree_deleted(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_tests_started(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_tests_passed(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_tests_failed(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_commit_created(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

            def apply_commit_failed(self, state, event):
                new_state = state.copy()
                new_state['event_count'] = state['event_count'] + 1
                return new_state

        return TestProjectionBuilder()

    def test_rebuild_projection_no_snapshot_full_replay(self, tmp_path, concrete_builder):
        """Test rebuilding projection when no snapshot exists - should replay all events."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "test-workflow-123"

        # Add several events to the workflow
        events = [
            Event(
                workflow_id=workflow_id,
                event_type="workflow.started",
                event_data={"description": "Test workflow", "beads_task_id": "task-123"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="worktree.created",
                event_data={"path": "/repo/trees/workflow-123", "branch": "feature/workflow-123"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.planned",
                event_data={"name": "auth", "description": "Authentication feature", "test_file": "test_auth.py"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.started",
                event_data={"name": "auth"}
            )
        ]

        # Append all events
        for event in events:
            result = event_store.append(event)
            assert result is True

        # Verify no snapshot exists
        snapshot = event_store.get_snapshot(workflow_id)
        assert snapshot is None

        # Rebuild projection from events
        final_state = event_store.rebuild_projection(workflow_id, concrete_builder)

        # Verify the final state contains all applied events
        assert final_state['workflow_id'] == workflow_id
        assert final_state['phase'] == 'planning'
        assert final_state['status'] == 'active'
        assert final_state['description'] == "Test workflow"
        assert final_state['worktree_path'] == "/repo/trees/workflow-123"
        assert len(final_state['features']) == 1
        assert final_state['features'][0]['name'] == 'auth'
        assert final_state['features'][0]['status'] == 'in_progress'
        assert final_state['event_count'] == 4

    def test_rebuild_projection_with_snapshot_partial_replay(self, tmp_path, concrete_builder):
        """Test rebuilding projection with existing snapshot - should replay only events after snapshot."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "test-workflow-456"

        # Add initial events
        initial_events = [
            Event(
                workflow_id=workflow_id,
                event_type="workflow.started",
                event_data={"description": "Test workflow", "beads_task_id": "task-456"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="worktree.created",
                event_data={"path": "/repo/trees/workflow-456", "branch": "feature/workflow-456"}
            )
        ]

        for event in initial_events:
            event_store.append(event)

        # Create a snapshot representing state after 2 events
        snapshot_state = {
            'workflow_id': workflow_id,
            'phase': 'planning',
            'status': 'active',
            'description': "Test workflow",
            'worktree_path': "/repo/trees/workflow-456",
            'features': [],
            'event_count': 2
        }

        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data=snapshot_state,
            event_sequence_number=2
        )
        event_store.save_snapshot(snapshot)

        # Add events after the snapshot
        post_snapshot_events = [
            Event(
                workflow_id=workflow_id,
                event_type="feature.planned",
                event_data={"name": "database", "description": "Database feature", "test_file": "test_db.py"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.started",
                event_data={"name": "database"}
            ),
            Event(
                workflow_id=workflow_id,
                event_type="feature.completed",
                event_data={"name": "database", "tests_passing": True}
            )
        ]

        for event in post_snapshot_events:
            event_store.append(event)

        # Rebuild projection - should start from snapshot and apply 3 additional events
        final_state = event_store.rebuild_projection(workflow_id, concrete_builder)

        # Verify the final state has snapshot data + additional events applied
        assert final_state['workflow_id'] == workflow_id
        assert final_state['phase'] == 'planning'
        assert final_state['status'] == 'active'
        assert final_state['description'] == "Test workflow"
        assert final_state['worktree_path'] == "/repo/trees/workflow-456"
        assert len(final_state['features']) == 1
        assert final_state['features'][0]['name'] == 'database'
        assert final_state['features'][0]['status'] == 'completed'
        assert final_state['features'][0]['tests_passing'] == True
        assert final_state['event_count'] == 5  # 2 from snapshot + 3 new events

    def test_rebuild_projection_empty_event_stream(self, tmp_path, concrete_builder):
        """Test rebuilding projection when no events exist for workflow."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "empty-workflow"

        # No events added, no snapshot exists
        final_state = event_store.rebuild_projection(workflow_id, concrete_builder)

        # Should return initial state from builder
        expected_initial_state = concrete_builder.get_initial_state()
        assert final_state == expected_initial_state

    def test_rebuild_projection_snapshot_only_no_subsequent_events(self, tmp_path, concrete_builder):
        """Test rebuilding projection when snapshot exists but no events after it."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "snapshot-only-workflow"

        # Create snapshot without any events after it
        snapshot_state = {
            'workflow_id': workflow_id,
            'phase': 'complete',
            'status': 'completed',
            'description': "Completed workflow",
            'features': [{'name': 'feature1', 'status': 'completed', 'tests_passing': True}],
            'event_count': 10
        }

        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data=snapshot_state,
            event_sequence_number=10
        )
        event_store.save_snapshot(snapshot)

        # Rebuild projection - should return snapshot state as-is
        final_state = event_store.rebuild_projection(workflow_id, concrete_builder)

        assert final_state == snapshot_state

    def test_rebuild_projection_multiple_workflows_isolation(self, tmp_path, concrete_builder):
        """Test that rebuilding projection is isolated per workflow."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_1 = "workflow-1"
        workflow_2 = "workflow-2"

        # Add events to workflow 1
        event_1 = Event(
            workflow_id=workflow_1,
            event_type="workflow.started",
            event_data={"description": "Workflow 1"}
        )
        event_store.append(event_1)

        # Add events to workflow 2
        event_2 = Event(
            workflow_id=workflow_2,
            event_type="workflow.started",
            event_data={"description": "Workflow 2"}
        )
        event_store.append(event_2)

        # Rebuild projection for workflow 1
        state_1 = event_store.rebuild_projection(workflow_1, concrete_builder)

        # Rebuild projection for workflow 2
        state_2 = event_store.rebuild_projection(workflow_2, concrete_builder)

        # Verify they have different, isolated states
        assert state_1['workflow_id'] == workflow_1
        assert state_1['description'] == "Workflow 1"
        assert state_2['workflow_id'] == workflow_2
        assert state_2['description'] == "Workflow 2"
        assert state_1 != state_2


class TestEventReplayEdgeCases:
    """Test edge cases and error handling in event replay system."""

    @pytest.fixture
    def concrete_builder(self):
        """Provide a minimal concrete ProjectionBuilder for edge case testing."""

        class MinimalProjectionBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {'status': 'initial'}

            def apply_workflow_started(self, state, event):
                new_state = state.copy()
                new_state['status'] = 'started'
                return new_state

            def apply_workflow_completed(self, state, event):
                new_state = state.copy()
                new_state['status'] = 'completed'
                return new_state

            def apply_workflow_failed(self, state, event):
                new_state = state.copy()
                new_state['status'] = 'failed'
                return new_state

            def apply_worktree_created(self, state, event):
                return state

            def apply_feature_planned(self, state, event):
                return state

            def apply_feature_started(self, state, event):
                return state

            def apply_feature_completed(self, state, event):
                return state

            def apply_feature_failed(self, state, event):
                return state

            def apply_phase_changed(self, state, event):
                return state

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
                return state

            def apply_tests_started(self, state, event):
                return state

            def apply_tests_passed(self, state, event):
                return state

            def apply_tests_failed(self, state, event):
                return state

            def apply_commit_created(self, state, event):
                return state

            def apply_commit_failed(self, state, event):
                return state

        return MinimalProjectionBuilder()

    def test_rebuild_projection_invalid_workflow_id(self, tmp_path, concrete_builder):
        """Test rebuilding projection with invalid workflow ID."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Should raise ValueError for empty workflow IDs
        with pytest.raises(ValueError, match="workflow_id cannot be empty"):
            event_store.rebuild_projection("", concrete_builder)

        # Nonexistent workflows should return initial state
        state = event_store.rebuild_projection("nonexistent-workflow", concrete_builder)
        assert state == concrete_builder.get_initial_state()

    def test_rebuild_projection_preserves_snapshot_immutability(self, tmp_path, concrete_builder):
        """Test that rebuilding projection doesn't mutate the original snapshot data."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "immutability-test"

        # Create snapshot at sequence 0 (no events processed yet)
        snapshot_state = {'status': 'original', 'features': [{'name': 'test'}]}
        snapshot = Snapshot(
            workflow_id=workflow_id,
            snapshot_data=snapshot_state,
            event_sequence_number=0
        )
        event_store.save_snapshot(snapshot)

        # Store original snapshot data
        original_snapshot_data = snapshot_state.copy()

        # Add event after snapshot
        event = Event(
            workflow_id=workflow_id,
            event_type="workflow.started",
            event_data={}
        )
        event_store.append(event)

        # Rebuild projection
        final_state = event_store.rebuild_projection(workflow_id, concrete_builder)

        # Verify original snapshot data wasn't mutated
        assert snapshot_state == original_snapshot_data
        # Verify final state is different (event was applied)
        assert final_state['status'] == 'started'

    def test_rebuild_projection_handles_projection_builder_errors(self, tmp_path):
        """Test that rebuild_projection handles errors in projection builder gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        workflow_id = "error-test"

        # Create a faulty projection builder
        class FaultyProjectionBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {'status': 'initial'}

            def apply_workflow_started(self, state, event):
                raise ValueError("Projection builder error")

            def apply_workflow_completed(self, state, event):
                return state

            def apply_workflow_failed(self, state, event):
                return state

            def apply_worktree_created(self, state, event):
                return state

            def apply_feature_planned(self, state, event):
                return state

            def apply_feature_started(self, state, event):
                return state

            def apply_feature_completed(self, state, event):
                return state

            def apply_feature_failed(self, state, event):
                return state

            def apply_phase_changed(self, state, event):
                return state

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
                return state

            def apply_tests_started(self, state, event):
                return state

            def apply_tests_passed(self, state, event):
                return state

            def apply_tests_failed(self, state, event):
                return state

            def apply_commit_created(self, state, event):
                return state

            def apply_commit_failed(self, state, event):
                return state

        faulty_builder = FaultyProjectionBuilder()

        # Add event that will cause error in projection builder
        event = Event(
            workflow_id=workflow_id,
            event_type="workflow.started",
            event_data={}
        )
        event_store.append(event)

        # Should propagate the projection builder error
        with pytest.raises(ValueError, match="Projection builder error"):
            event_store.rebuild_projection(workflow_id, faulty_builder)


class TestEventReplayInputValidation:
    """Test input validation for rebuild_projection method."""

    @pytest.fixture
    def minimal_builder(self):
        """Minimal projection builder for validation testing."""

        class MinimalProjectionBuilder(ProjectionBuilder):
            def get_initial_state(self):
                return {}

            def apply_workflow_started(self, state, event):
                return state

            def apply_workflow_completed(self, state, event):
                return state

            def apply_workflow_failed(self, state, event):
                return state

            def apply_worktree_created(self, state, event):
                return state

            def apply_feature_planned(self, state, event):
                return state

            def apply_feature_started(self, state, event):
                return state

            def apply_feature_completed(self, state, event):
                return state

            def apply_feature_failed(self, state, event):
                return state

            def apply_phase_changed(self, state, event):
                return state

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
                return state

            def apply_tests_started(self, state, event):
                return state

            def apply_tests_passed(self, state, event):
                return state

            def apply_tests_failed(self, state, event):
                return state

            def apply_commit_created(self, state, event):
                return state

            def apply_commit_failed(self, state, event):
                return state

        return MinimalProjectionBuilder()

    def test_rebuild_projection_requires_workflow_id(self, tmp_path, minimal_builder):
        """Test that rebuild_projection requires workflow_id parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(TypeError):
            event_store.rebuild_projection(builder=minimal_builder)

    def test_rebuild_projection_requires_projection_builder(self, tmp_path):
        """Test that rebuild_projection requires projection_builder parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(TypeError):
            event_store.rebuild_projection("test-workflow")

    def test_rebuild_projection_validates_workflow_id_type(self, tmp_path, minimal_builder):
        """Test that rebuild_projection validates workflow_id parameter type."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Non-string types should raise TypeError
        with pytest.raises(TypeError, match="workflow_id must be a string"):
            event_store.rebuild_projection(123, minimal_builder)

        # None is specifically checked and raises ValueError
        with pytest.raises(ValueError, match="workflow_id cannot be None"):
            event_store.rebuild_projection(None, minimal_builder)

    def test_rebuild_projection_validates_projection_builder_type(self, tmp_path):
        """Test that rebuild_projection validates projection_builder parameter type."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        with pytest.raises(TypeError, match="builder must be a ProjectionBuilder instance"):
            event_store.rebuild_projection("test-workflow", "not-a-builder")

        with pytest.raises(TypeError, match="builder must be a ProjectionBuilder instance"):
            event_store.rebuild_projection("test-workflow", None)