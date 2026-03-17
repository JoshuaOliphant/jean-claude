# ABOUTME: Comprehensive tests for all event type handlers in ProjectionBuilder
# ABOUTME: Tests all event types specified in ARCHITECTURE.md with proper data validation and state transformation

"""Tests for event type handlers in ProjectionBuilder.

Tests all event type handlers defined in the ProjectionBuilder class,
covering workflow, worktree, feature, phase, test, and commit event types.
"""

import pytest
from datetime import datetime

from jean_claude.core.event_models import Event
from jean_claude.core.projection_builder import ProjectionBuilder


class ComprehensiveProjectionBuilder(ProjectionBuilder):
    """Comprehensive implementation of ProjectionBuilder for testing all event types."""

    def get_initial_state(self):
        return {
            'workflow_id': None, 'phase': 'unknown', 'status': 'unknown',
            'features': [], 'worktree_path': None, 'worktree_branch': None,
            'base_commit': None, 'merge_commit': None, 'worktree_merged': False,
            'test_results': {}, 'commits': [], 'errors': []
        }

    def apply_workflow_started(self, state, event):
        new_state = state.copy()
        new_state.update({
            'workflow_id': event.workflow_id, 'phase': 'planning', 'status': 'active',
            'description': event.event_data.get('description'),
            'beads_task_id': event.event_data.get('beads_task_id'),
            'started_at': event.timestamp
        })
        return new_state

    def apply_workflow_completed(self, state, event):
        new_state = state.copy()
        new_state.update({
            'phase': 'complete', 'status': 'completed',
            'completed_at': event.timestamp,
            'duration_ms': event.event_data.get('duration_ms'),
            'total_cost': event.event_data.get('total_cost')
        })
        return new_state

    def apply_workflow_failed(self, state, event):
        new_state = state.copy()
        new_state.update({
            'status': 'failed', 'error': event.event_data.get('error'),
            'failed_phase': event.event_data.get('phase'),
            'failed_at': event.timestamp
        })
        return new_state

    def apply_worktree_created(self, state, event):
        new_state = state.copy()
        new_state.update({
            'worktree_path': event.event_data.get('path'),
            'worktree_branch': event.event_data.get('branch'),
            'base_commit': event.event_data.get('base_commit'),
            'worktree_created_at': event.timestamp
        })
        return new_state

    def apply_worktree_active(self, state, event):
        new_state = state.copy()
        new_state.update({
            'worktree_last_active': event.timestamp,
            'worktree_active_path': event.event_data.get('path')
        })
        return new_state

    def apply_worktree_merged(self, state, event):
        new_state = state.copy()
        new_state.update({
            'merge_commit': event.event_data.get('commit_sha'),
            'worktree_merged': True,
            'merge_conflicts': event.event_data.get('conflicts', []),
            'merged_at': event.timestamp
        })
        return new_state

    def apply_worktree_deleted(self, state, event):
        new_state = state.copy()
        new_state.update({
            'worktree_deleted': True,
            'deletion_reason': event.event_data.get('reason'),
            'deleted_at': event.timestamp
        })
        return new_state

    def apply_feature_planned(self, state, event):
        new_state = state.copy()
        features = new_state.get('features', []).copy()
        features.append({
            'name': event.event_data['name'],
            'description': event.event_data['description'],
            'test_file': event.event_data.get('test_file'),
            'status': 'planned', 'tests_passing': False,
            'planned_at': event.timestamp
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
                feature['duration_ms'] = event.event_data.get('duration_ms')
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

    def apply_tests_started(self, state, event):
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()
        test_key = f"{event.event_data.get('test_file', 'unknown')}-{event.timestamp}"
        test_results[test_key] = {
            'test_file': event.event_data.get('test_file'),
            'feature': event.event_data.get('feature'),
            'status': 'running', 'started_at': event.timestamp
        }
        new_state['test_results'] = test_results
        return new_state

    def apply_tests_passed(self, state, event):
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()
        test_file = event.event_data.get('test_file')
        for key, result in test_results.items():
            if result.get('test_file') == test_file and result.get('status') == 'running':
                result.update({
                    'status': 'passed', 'count': event.event_data.get('count'),
                    'duration_ms': event.event_data.get('duration_ms'),
                    'completed_at': event.timestamp
                })
                break
        new_state['test_results'] = test_results
        return new_state

    def apply_tests_failed(self, state, event):
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()
        test_file = event.event_data.get('test_file')
        for key, result in test_results.items():
            if result.get('test_file') == test_file and result.get('status') == 'running':
                result.update({
                    'status': 'failed',
                    'failures': event.event_data.get('failures', []),
                    'completed_at': event.timestamp
                })
                break
        new_state['test_results'] = test_results
        return new_state

    def apply_commit_created(self, state, event):
        new_state = state.copy()
        commits = new_state.get('commits', []).copy()
        commits.append({
            'commit_sha': event.event_data.get('commit_sha'),
            'message': event.event_data.get('message'),
            'files': event.event_data.get('files', []),
            'created_at': event.timestamp
        })
        new_state['commits'] = commits
        return new_state

    def apply_commit_failed(self, state, event):
        new_state = state.copy()
        errors = new_state.get('errors', []).copy()
        errors.append({
            'type': 'commit_failed',
            'error': event.event_data.get('error'),
            'files': event.event_data.get('files', []),
            'failed_at': event.timestamp
        })
        new_state['errors'] = errors
        return new_state


class TestEventTypeHandlers:
    """Test all event type handlers comprehensively."""

    @pytest.fixture
    def builder(self):
        return ComprehensiveProjectionBuilder()

    @pytest.fixture
    def initial_state(self, builder):
        return builder.get_initial_state()

    def test_workflow_lifecycle_events(self, builder, initial_state):
        """Test workflow started, completed, and failed event handlers."""
        # Started
        started = Event(workflow_id="w-123", event_type="workflow.started",
                        event_data={'description': 'Implement auth', 'beads_task_id': 'beads-456'})
        result = builder.apply_event(initial_state, started)
        assert result['workflow_id'] == "w-123"
        assert result['phase'] == 'planning'
        assert result['status'] == 'active'
        assert result['description'] == 'Implement auth'
        assert result['beads_task_id'] == 'beads-456'

        # Completed
        completed = Event(workflow_id="w-123", event_type="workflow.completed",
                          event_data={'duration_ms': 180000, 'total_cost': 89.45})
        result2 = builder.apply_event(result, completed)
        assert result2['phase'] == 'complete'
        assert result2['status'] == 'completed'
        assert result2['duration_ms'] == 180000
        assert result2['total_cost'] == 89.45

        # Failed
        state = {'workflow_id': 'w-123', 'status': 'active', 'phase': 'implementing'}
        failed = Event(workflow_id="w-123", event_type="workflow.failed",
                       event_data={'error': 'Syntax errors', 'phase': 'implementing'})
        result3 = builder.apply_event(state, failed)
        assert result3['status'] == 'failed'
        assert result3['error'] == 'Syntax errors'
        assert result3['failed_phase'] == 'implementing'

    def test_worktree_lifecycle_events(self, builder, initial_state):
        """Test worktree created, active, merged (with/without conflicts), and deleted."""
        # Created
        created = Event(workflow_id="w-123", event_type="worktree.created",
                        event_data={'path': '/repo/trees/w-123', 'branch': 'beads/w-123', 'base_commit': 'abc123'})
        s1 = builder.apply_event(initial_state, created)
        assert s1['worktree_path'] == '/repo/trees/w-123'
        assert s1['worktree_branch'] == 'beads/w-123'
        assert s1['base_commit'] == 'abc123'

        # Active (heartbeat)
        active = Event(workflow_id="w-123", event_type="worktree.active",
                       event_data={'path': '/repo/trees/w-123'})
        s2 = builder.apply_event(s1, active)
        assert s2['worktree_last_active'] == active.timestamp

        # Merged without conflicts
        merged = Event(workflow_id="w-123", event_type="worktree.merged",
                       event_data={'commit_sha': 'def456', 'conflicts': []})
        s3 = builder.apply_event(s2, merged)
        assert s3['merge_commit'] == 'def456'
        assert s3['worktree_merged'] is True
        assert s3['merge_conflicts'] == []

        # Merged with conflicts
        merged2 = Event(workflow_id="w-123", event_type="worktree.merged",
                        event_data={'commit_sha': 'ghi789', 'conflicts': ['src/main.py', 'tests/test_auth.py']})
        s3b = builder.apply_event(s2, merged2)
        assert s3b['merge_conflicts'] == ['src/main.py', 'tests/test_auth.py']

        # Deleted
        deleted = Event(workflow_id="w-123", event_type="worktree.deleted",
                        event_data={'reason': 'merged'})
        s4 = builder.apply_event(s3, deleted)
        assert s4['worktree_deleted'] is True
        assert s4['deletion_reason'] == 'merged'

    def test_feature_lifecycle_complete_flow(self, builder, initial_state):
        """Test complete feature lifecycle: planned -> started -> completed, and failed path."""
        # Planned
        planned = Event(workflow_id="w-123", event_type="feature.planned",
                        event_data={'name': 'api-endpoints', 'description': 'REST API', 'test_file': 'tests/test_api.py'})
        s1 = builder.apply_event(initial_state, planned)
        assert len(s1['features']) == 1
        f = s1['features'][0]
        assert f['name'] == 'api-endpoints'
        assert f['status'] == 'planned'
        assert f['tests_passing'] is False

        # Started
        started = Event(workflow_id="w-123", event_type="feature.started",
                        event_data={'name': 'api-endpoints'})
        s2 = builder.apply_event(s1, started)
        assert s2['features'][0]['status'] == 'in_progress'

        # Completed
        completed = Event(workflow_id="w-123", event_type="feature.completed",
                          event_data={'name': 'api-endpoints', 'tests_passing': True, 'duration_ms': 60000})
        s3 = builder.apply_event(s2, completed)
        f3 = s3['features'][0]
        assert f3['status'] == 'completed'
        assert f3['tests_passing'] is True
        assert f3['duration_ms'] == 60000
        assert 'planned_at' in f3
        assert 'started_at' in f3
        assert 'completed_at' in f3

        # Failed path
        s2b = builder.apply_event(s1, started)
        failed = Event(workflow_id="w-123", event_type="feature.failed",
                       event_data={'name': 'api-endpoints', 'error': 'DB timeout'})
        s3b = builder.apply_event(s2b, failed)
        assert s3b['features'][0]['status'] == 'failed'
        assert s3b['features'][0]['error'] == 'DB timeout'

    def test_phase_changed_event(self, builder):
        """Test phase transition tracking."""
        state = {'phase': 'planning'}
        event = Event(workflow_id="w-123", event_type="phase.changed",
                      event_data={'from_phase': 'planning', 'to_phase': 'implementing'})
        result = builder.apply_event(state, event)
        assert result['previous_phase'] == 'planning'
        assert result['phase'] == 'implementing'

    def test_test_lifecycle_events(self, builder, initial_state):
        """Test tests.started, tests.passed, and tests.failed handlers."""
        # Started
        started = Event(workflow_id="w-123", event_type="tests.started",
                        event_data={'test_file': 'tests/test_auth.py', 'feature': 'auth'})
        s1 = builder.apply_event(initial_state, started)
        assert len(s1['test_results']) == 1
        tr = list(s1['test_results'].values())[0]
        assert tr['status'] == 'running'
        assert tr['test_file'] == 'tests/test_auth.py'

        # Passed
        passed = Event(workflow_id="w-123", event_type="tests.passed",
                       event_data={'test_file': 'tests/test_auth.py', 'count': 15, 'duration_ms': 3500})
        s2 = builder.apply_event(s1, passed)
        tr2 = list(s2['test_results'].values())[0]
        assert tr2['status'] == 'passed'
        assert tr2['count'] == 15
        assert tr2['duration_ms'] == 3500

        # Failed (start fresh)
        s1b = builder.apply_event(initial_state, started)
        failed = Event(workflow_id="w-123", event_type="tests.failed",
                       event_data={'test_file': 'tests/test_auth.py', 'failures': ['test_login', 'test_expiry']})
        s2b = builder.apply_event(s1b, failed)
        tr2b = list(s2b['test_results'].values())[0]
        assert tr2b['status'] == 'failed'
        assert tr2b['failures'] == ['test_login', 'test_expiry']

    def test_commit_events(self, builder, initial_state):
        """Test commit.created and commit.failed, including multiple commits."""
        # Created
        created = Event(workflow_id="w-123", event_type="commit.created",
                        event_data={'commit_sha': 'abc123', 'message': 'Add auth', 'files': ['src/auth.py']})
        s1 = builder.apply_event(initial_state, created)
        assert len(s1['commits']) == 1
        assert s1['commits'][0]['commit_sha'] == 'abc123'

        # Second commit
        created2 = Event(workflow_id="w-123", event_type="commit.created",
                         event_data={'commit_sha': 'def456', 'message': 'Add tests', 'files': ['tests/test.py']})
        s2 = builder.apply_event(s1, created2)
        assert len(s2['commits']) == 2
        assert s2['commits'][1]['commit_sha'] == 'def456'

        # Failed
        failed = Event(workflow_id="w-123", event_type="commit.failed",
                       event_data={'error': 'Linting errors', 'files': ['src/auth.py']})
        s3 = builder.apply_event(initial_state, failed)
        assert len(s3['errors']) == 1
        assert s3['errors'][0]['type'] == 'commit_failed'
        assert s3['errors'][0]['error'] == 'Linting errors'

    def test_unknown_event_type_raises_error(self, builder, initial_state):
        """Test that unknown event types raise ValueError."""
        event = Event(workflow_id="w-123", event_type="unknown.event.type", event_data={})
        with pytest.raises(ValueError, match="Unknown event type: unknown.event.type"):
            builder.apply_event(initial_state, event)

    def test_state_immutability(self, builder):
        """Test that original state is not modified by apply_event."""
        original = {
            'workflow_id': 'test-123',
            'features': [{'name': 'existing', 'status': 'completed'}],
            'commits': [{'commit_sha': 'existing123', 'message': 'existing'}]
        }
        expected = {
            'workflow_id': 'test-123',
            'features': [{'name': 'existing', 'status': 'completed'}],
            'commits': [{'commit_sha': 'existing123', 'message': 'existing'}]
        }
        event = Event(workflow_id="w-123", event_type="feature.planned",
                      event_data={'name': 'new-feature', 'description': 'A new feature'})
        result = builder.apply_event(original, event)
        assert original == expected
        assert len(result['features']) == 2
