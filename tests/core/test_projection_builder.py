# ABOUTME: Tests for ProjectionBuilder base class with apply_event() method for handling different event types
# ABOUTME: Tests base projection building functionality, abstract methods, and input validation

"""Tests for ProjectionBuilder base class.

Tests abstract class definition, concrete implementation, apply_event
routing, state immutability, input validation, and error handling.
"""

import pytest
from datetime import datetime

from jean_claude.core.event_models import Event
from jean_claude.core.projection_builder import ProjectionBuilder


def _create_minimal_builder():
    """Create a minimal concrete ProjectionBuilder for testing."""

    class MinimalBuilder(ProjectionBuilder):
        def get_initial_state(self):
            return {'workflow_id': None, 'phase': 'unknown', 'features': [], 'status': 'unknown'}

        def apply_workflow_started(self, state, event):
            s = state.copy()
            s.update({'workflow_id': event.workflow_id, 'phase': 'planning', 'status': 'active'})
            return s

        def apply_workflow_completed(self, state, event):
            s = state.copy()
            s.update({'phase': 'complete', 'status': 'completed'})
            return s

        def apply_workflow_failed(self, state, event):
            s = state.copy()
            s.update({'status': 'failed', 'error': event.event_data.get('error')})
            return s

        def apply_worktree_created(self, state, event):
            s = state.copy()
            s['worktree_path'] = event.event_data.get('path')
            return s

        def apply_worktree_active(self, state, event): return state
        def apply_worktree_merged(self, state, event): return state
        def apply_worktree_deleted(self, state, event): return state

        def apply_feature_planned(self, state, event):
            s = state.copy()
            features = s.get('features', []).copy()
            features.append({'name': event.event_data['name'], 'status': 'planned'})
            s['features'] = features
            return s

        def apply_feature_started(self, state, event):
            s = state.copy()
            features = s.get('features', []).copy()
            for f in features:
                if f['name'] == event.event_data['name']:
                    f['status'] = 'in_progress'
            s['features'] = features
            return s

        def apply_feature_completed(self, state, event):
            s = state.copy()
            features = s.get('features', []).copy()
            for f in features:
                if f['name'] == event.event_data['name']:
                    f['status'] = 'completed'
                    f['tests_passing'] = event.event_data.get('tests_passing', False)
            s['features'] = features
            return s

        def apply_feature_failed(self, state, event):
            s = state.copy()
            features = s.get('features', []).copy()
            for f in features:
                if f['name'] == event.event_data['name']:
                    f['status'] = 'failed'
            s['features'] = features
            return s

        def apply_phase_changed(self, state, event):
            s = state.copy()
            s['phase'] = event.event_data.get('to_phase')
            return s

        def apply_tests_started(self, state, event): return state
        def apply_tests_passed(self, state, event): return state
        def apply_tests_failed(self, state, event): return state
        def apply_commit_created(self, state, event): return state
        def apply_commit_failed(self, state, event): return state

    return MinimalBuilder()


class TestProjectionBuilderBase:
    """Test the base ProjectionBuilder class definition."""

    def test_abstract_class_and_concrete_implementation(self):
        """Test ProjectionBuilder is abstract and concrete implementations work."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            ProjectionBuilder()

        abstract_methods = ProjectionBuilder.__abstractmethods__
        assert 'get_initial_state' in abstract_methods
        assert 'apply_workflow_started' in abstract_methods
        assert 'apply_feature_planned' in abstract_methods
        assert len(abstract_methods) == 18

        builder = _create_minimal_builder()
        assert isinstance(builder, ProjectionBuilder)


class TestProjectionBuilderEventApplication:
    """Test apply_event() method functionality."""

    @pytest.fixture
    def builder(self):
        return _create_minimal_builder()

    def test_apply_event_routes_to_correct_handlers(self, builder):
        """Test apply_event routes workflow, worktree, feature, and phase events correctly."""
        state = builder.get_initial_state()

        # Workflow started
        s1 = builder.apply_event(state, Event(
            workflow_id="w-123", event_type="workflow.started",
            event_data={'description': 'Test'}))
        assert s1['workflow_id'] == "w-123"
        assert s1['phase'] == 'planning'
        assert s1['status'] == 'active'

        # Workflow completed
        s2 = builder.apply_event(s1, Event(
            workflow_id="w-123", event_type="workflow.completed",
            event_data={'duration_ms': 120000}))
        assert s2['phase'] == 'complete'
        assert s2['status'] == 'completed'

        # Workflow failed
        s3 = builder.apply_event(s1, Event(
            workflow_id="w-123", event_type="workflow.failed",
            event_data={'error': 'Compile error'}))
        assert s3['status'] == 'failed'

        # Worktree created
        s4 = builder.apply_event(state, Event(
            workflow_id="w-123", event_type="worktree.created",
            event_data={'path': '/repo/trees/w-123'}))
        assert s4['worktree_path'] == '/repo/trees/w-123'

        # Phase changed
        s5 = builder.apply_event({'phase': 'planning'}, Event(
            workflow_id="w-123", event_type="phase.changed",
            event_data={'from_phase': 'planning', 'to_phase': 'implementing'}))
        assert s5['phase'] == 'implementing'

    def test_feature_lifecycle_with_multiple_features(self, builder):
        """Test feature planned/started/completed/failed with multiple features."""
        state = {'features': []}

        # Plan two features
        s1 = builder.apply_event(state, Event(
            workflow_id="w", event_type="feature.planned",
            event_data={'name': 'f1', 'description': 'First'}))
        s2 = builder.apply_event(s1, Event(
            workflow_id="w", event_type="feature.planned",
            event_data={'name': 'f2', 'description': 'Second'}))
        assert len(s2['features']) == 2

        # Complete only f2
        s3 = builder.apply_event(s2, Event(
            workflow_id="w", event_type="feature.completed",
            event_data={'name': 'f2', 'tests_passing': True}))
        assert s3['features'][0]['status'] == 'planned'
        assert s3['features'][1]['status'] == 'completed'
        assert s3['features'][1]['tests_passing'] is True

    def test_state_immutability(self, builder):
        """Test that apply_event doesn't mutate original state."""
        original = {'workflow_id': 'w', 'phase': 'planning', 'features': [{'name': 'f1', 'status': 'planned'}]}
        expected = {'workflow_id': 'w', 'phase': 'planning', 'features': [{'name': 'f1', 'status': 'planned'}]}

        result = builder.apply_event(original, Event(
            workflow_id="w", event_type="phase.changed",
            event_data={'from_phase': 'planning', 'to_phase': 'implementing'}))

        assert original == expected
        assert result['phase'] == 'implementing'

    def test_unknown_event_type_raises_error(self, builder):
        """Test unknown event types raise ValueError."""
        with pytest.raises(ValueError, match="Unknown event type: unknown.event"):
            builder.apply_event({}, Event(workflow_id="w", event_type="unknown.event", event_data={}))


class TestProjectionBuilderInputValidation:
    """Test input validation for apply_event."""

    @pytest.fixture
    def builder(self):
        return _create_minimal_builder()

    def test_apply_event_validates_parameters(self, builder):
        """Test that apply_event validates state and event parameter types."""
        event = Event(workflow_id="test", event_type="workflow.started", event_data={})

        with pytest.raises(TypeError):
            builder.apply_event({})  # missing event

        with pytest.raises(TypeError):
            builder.apply_event(event=event)  # missing state

        with pytest.raises(TypeError, match="Event parameter must be an Event instance"):
            builder.apply_event({}, "not-an-event")

        with pytest.raises(TypeError, match="State parameter must be a dict"):
            builder.apply_event("not-a-dict", event)
