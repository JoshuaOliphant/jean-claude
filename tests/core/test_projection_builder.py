# ABOUTME: Tests for ProjectionBuilder base class with apply_event() method for handling different event types
# ABOUTME: Comprehensive tests for base projection building functionality with abstract methods

"""Tests for ProjectionBuilder base class.

This module tests the base ProjectionBuilder class which provides the foundation
for building projections from event streams. The ProjectionBuilder handles different
event types through the apply_event() method and manages state transformations.

Key Features Tested:
- Event application to state
- Abstract method definitions
- Event type handling
- State management
- Error handling for invalid events
"""

import pytest
from abc import ABC, abstractmethod
from datetime import datetime

from jean_claude.core.event_models import Event
from jean_claude.core.projection_builder import ProjectionBuilder


class TestProjectionBuilderBase:
    """Test the base ProjectionBuilder class functionality."""

    def test_projection_builder_is_abstract(self):
        """Test that ProjectionBuilder is abstract and cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProjectionBuilder()

    def test_projection_builder_has_abstract_methods(self):
        """Test that ProjectionBuilder defines required abstract methods."""
        # Check that the abstract methods are defined
        abstract_methods = ProjectionBuilder.__abstractmethods__
        expected_methods = {'get_initial_state', 'apply_workflow_started', 'apply_workflow_completed',
                          'apply_workflow_failed', 'apply_worktree_created', 'apply_worktree_active',
                          'apply_worktree_merged', 'apply_worktree_deleted', 'apply_feature_planned',
                          'apply_feature_started', 'apply_feature_completed', 'apply_feature_failed',
                          'apply_phase_changed', 'apply_tests_started', 'apply_tests_passed',
                          'apply_tests_failed', 'apply_commit_created', 'apply_commit_failed'}

        assert abstract_methods == expected_methods

    def test_concrete_implementation_can_be_instantiated(self):
        """Test that a concrete implementation of ProjectionBuilder can be instantiated."""

        class ConcreteProjectionBuilder(ProjectionBuilder):
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

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
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

        builder = ConcreteProjectionBuilder()
        assert isinstance(builder, ProjectionBuilder)


class TestProjectionBuilderEventApplication:
    """Test apply_event() method functionality."""

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
                    'status': 'unknown'
                }

            def apply_workflow_started(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'workflow_id': event.workflow_id,
                    'phase': 'planning',
                    'status': 'active',
                    'description': event.event_data.get('description'),
                    'beads_task_id': event.event_data.get('beads_task_id'),
                    'started_at': event.timestamp
                })
                return new_state

            def apply_workflow_completed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'phase': 'complete',
                    'status': 'completed',
                    'completed_at': event.timestamp,
                    'duration_ms': event.event_data.get('duration_ms'),
                    'total_cost': event.event_data.get('total_cost')
                })
                return new_state

            def apply_workflow_failed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'status': 'failed',
                    'error': event.event_data.get('error'),
                    'failed_phase': event.event_data.get('phase'),
                    'failed_at': event.timestamp
                })
                return new_state

            def apply_worktree_created(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'worktree_path': event.event_data.get('path'),
                    'worktree_branch': event.event_data.get('branch'),
                    'base_commit': event.event_data.get('base_commit')
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
                return new_state

            def apply_phase_changed(self, state, event):
                new_state = state.copy()
                new_state.update({
                    'previous_phase': event.event_data.get('from_phase'),
                    'phase': event.event_data.get('to_phase'),
                    'phase_changed_at': event.timestamp
                })
                return new_state

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

        return TestProjectionBuilder()

    def test_apply_event_workflow_started(self, concrete_builder):
        """Test applying WorkflowStarted event."""
        initial_state = concrete_builder.get_initial_state()

        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            event_data={
                'description': 'Test workflow for feature development',
                'beads_task_id': 'beads-task-456'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert result_state['workflow_id'] == "test-workflow-123"
        assert result_state['phase'] == 'planning'
        assert result_state['status'] == 'active'
        assert result_state['description'] == 'Test workflow for feature development'
        assert result_state['beads_task_id'] == 'beads-task-456'
        assert result_state['started_at'] == event.timestamp

    def test_apply_event_workflow_completed(self, concrete_builder):
        """Test applying WorkflowCompleted event."""
        initial_state = {
            'workflow_id': 'test-workflow-123',
            'phase': 'implementing',
            'status': 'active'
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.completed",
            event_data={
                'duration_ms': 120000,
                'total_cost': 45.67
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert result_state['phase'] == 'complete'
        assert result_state['status'] == 'completed'
        assert result_state['duration_ms'] == 120000
        assert result_state['total_cost'] == 45.67
        assert result_state['completed_at'] == event.timestamp

    def test_apply_event_workflow_failed(self, concrete_builder):
        """Test applying WorkflowFailed event."""
        initial_state = {
            'workflow_id': 'test-workflow-123',
            'phase': 'implementing',
            'status': 'active'
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.failed",
            event_data={
                'error': 'Failed to compile source code',
                'phase': 'implementing'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert result_state['status'] == 'failed'
        assert result_state['error'] == 'Failed to compile source code'
        assert result_state['failed_phase'] == 'implementing'
        assert result_state['failed_at'] == event.timestamp

    def test_apply_event_worktree_created(self, concrete_builder):
        """Test applying WorktreeCreated event."""
        initial_state = concrete_builder.get_initial_state()

        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.created",
            event_data={
                'path': '/repo/trees/beads-workflow-123',
                'branch': 'beads/workflow-123',
                'base_commit': 'abc123def456'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert result_state['worktree_path'] == '/repo/trees/beads-workflow-123'
        assert result_state['worktree_branch'] == 'beads/workflow-123'
        assert result_state['base_commit'] == 'abc123def456'

    def test_apply_event_feature_planned(self, concrete_builder):
        """Test applying FeaturePlanned event."""
        initial_state = {'features': []}

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.planned",
            event_data={
                'name': 'user-authentication',
                'description': 'Implement user login and registration',
                'test_file': 'tests/core/test_auth.py'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert len(result_state['features']) == 1
        feature = result_state['features'][0]
        assert feature['name'] == 'user-authentication'
        assert feature['description'] == 'Implement user login and registration'
        assert feature['test_file'] == 'tests/core/test_auth.py'
        assert feature['status'] == 'planned'
        assert feature['tests_passing'] == False

    def test_apply_event_feature_started(self, concrete_builder):
        """Test applying FeatureStarted event."""
        initial_state = {
            'features': [{
                'name': 'user-authentication',
                'description': 'Implement user login and registration',
                'status': 'planned',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.started",
            event_data={'name': 'user-authentication'}
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        feature = result_state['features'][0]
        assert feature['status'] == 'in_progress'
        assert feature['started_at'] == event.timestamp

    def test_apply_event_feature_completed(self, concrete_builder):
        """Test applying FeatureCompleted event."""
        initial_state = {
            'features': [{
                'name': 'user-authentication',
                'description': 'Implement user login and registration',
                'status': 'in_progress',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.completed",
            event_data={
                'name': 'user-authentication',
                'tests_passing': True
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        feature = result_state['features'][0]
        assert feature['status'] == 'completed'
        assert feature['tests_passing'] == True
        assert feature['completed_at'] == event.timestamp

    def test_apply_event_feature_failed(self, concrete_builder):
        """Test applying FeatureFailed event."""
        initial_state = {
            'features': [{
                'name': 'user-authentication',
                'description': 'Implement user login and registration',
                'status': 'in_progress',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.failed",
            event_data={
                'name': 'user-authentication',
                'error': 'Database connection failed'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        feature = result_state['features'][0]
        assert feature['status'] == 'failed'
        assert feature['error'] == 'Database connection failed'
        assert feature['failed_at'] == event.timestamp

    def test_apply_event_phase_changed(self, concrete_builder):
        """Test applying PhaseChanged event."""
        initial_state = {
            'phase': 'planning'
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="phase.changed",
            event_data={
                'from_phase': 'planning',
                'to_phase': 'implementing'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        assert result_state['previous_phase'] == 'planning'
        assert result_state['phase'] == 'implementing'
        assert result_state['phase_changed_at'] == event.timestamp

    def test_apply_event_unknown_event_type(self, concrete_builder):
        """Test that unknown event types raise appropriate error."""
        initial_state = concrete_builder.get_initial_state()

        event = Event(
            workflow_id="test-workflow-123",
            event_type="unknown.event",
            event_data={}
        )

        with pytest.raises(ValueError, match="Unknown event type: unknown.event"):
            concrete_builder.apply_event(initial_state, event)

    def test_apply_event_preserves_state_immutability(self, concrete_builder):
        """Test that apply_event doesn't mutate the original state."""
        initial_state = {
            'workflow_id': 'test-workflow-123',
            'phase': 'planning',
            'features': [{'name': 'feature1', 'status': 'planned'}]
        }
        original_state = initial_state.copy()

        event = Event(
            workflow_id="test-workflow-123",
            event_type="phase.changed",
            event_data={
                'from_phase': 'planning',
                'to_phase': 'implementing'
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        # Original state should be unchanged
        assert initial_state == original_state
        # Result should be different
        assert result_state != initial_state
        assert result_state['phase'] == 'implementing'

    def test_apply_event_handles_multiple_features(self, concrete_builder):
        """Test feature updates work correctly with multiple features."""
        initial_state = {
            'features': [
                {'name': 'feature1', 'status': 'planned'},
                {'name': 'feature2', 'status': 'planned'},
                {'name': 'feature3', 'status': 'in_progress'}
            ]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.completed",
            event_data={
                'name': 'feature2',
                'tests_passing': True
            }
        )

        result_state = concrete_builder.apply_event(initial_state, event)

        # Check that only feature2 was updated
        assert result_state['features'][0]['status'] == 'planned'  # feature1 unchanged
        assert result_state['features'][1]['status'] == 'completed'  # feature2 updated
        assert result_state['features'][1]['tests_passing'] == True
        assert result_state['features'][2]['status'] == 'in_progress'  # feature3 unchanged


class TestProjectionBuilderInputValidation:
    """Test input validation for ProjectionBuilder methods."""

    @pytest.fixture
    def concrete_builder(self):
        """Minimal concrete builder for validation testing."""

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

            def apply_worktree_active(self, state, event):
                return state

            def apply_worktree_merged(self, state, event):
                return state

            def apply_worktree_deleted(self, state, event):
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

    def test_apply_event_requires_event_parameter(self, concrete_builder):
        """Test that apply_event requires an event parameter."""
        state = {}

        with pytest.raises(TypeError):
            concrete_builder.apply_event(state)

    def test_apply_event_requires_state_parameter(self, concrete_builder):
        """Test that apply_event requires a state parameter."""
        event = Event(
            workflow_id="test",
            event_type="workflow.started",
            event_data={}
        )

        with pytest.raises(TypeError):
            concrete_builder.apply_event(event=event)

    def test_apply_event_validates_event_type(self, concrete_builder):
        """Test that apply_event validates event parameter type."""
        state = {}

        # Should raise error for non-Event parameter
        with pytest.raises(TypeError, match="Event parameter must be an Event instance"):
            concrete_builder.apply_event(state, "not-an-event")

    def test_apply_event_validates_state_type(self, concrete_builder):
        """Test that apply_event validates state parameter type."""
        event = Event(
            workflow_id="test",
            event_type="workflow.started",
            event_data={}
        )

        # Should raise error for non-dict state
        with pytest.raises(TypeError, match="State parameter must be a dict"):
            concrete_builder.apply_event("not-a-dict", event)