# ABOUTME: Comprehensive tests for all event type handlers in ProjectionBuilder
# ABOUTME: Tests all event types specified in ARCHITECTURE.md with proper data validation and state transformation

"""Tests for event type handlers in ProjectionBuilder.

This module tests all event type handlers defined in the ProjectionBuilder class,
ensuring that each event type is properly processed and transforms state correctly.
The tests cover all event types specified in ARCHITECTURE.md including:

- Workflow lifecycle events (started, completed, failed)
- Worktree lifecycle events (created, active, merged, deleted)
- Feature lifecycle events (planned, started, completed, failed)
- Phase transition events
- Test events (started, passed, failed)
- Commit events (created, failed)

Each test verifies proper event data validation and state transformation logic.
"""

import pytest
from datetime import datetime

from jean_claude.core.event_models import Event
from jean_claude.core.projection_builder import ProjectionBuilder


class ComprehensiveProjectionBuilder(ProjectionBuilder):
    """Comprehensive implementation of ProjectionBuilder for testing all event types."""

    def get_initial_state(self):
        return {
            'workflow_id': None,
            'phase': 'unknown',
            'status': 'unknown',
            'features': [],
            'worktree_path': None,
            'worktree_branch': None,
            'base_commit': None,
            'merge_commit': None,
            'worktree_merged': False,
            'test_results': {},
            'commits': [],
            'errors': []
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
            'base_commit': event.event_data.get('base_commit'),
            'worktree_created_at': event.timestamp
        })
        return new_state

    def apply_worktree_active(self, state, event):
        """Apply WorktreeActive event (heartbeat)."""
        new_state = state.copy()
        new_state.update({
            'worktree_last_active': event.timestamp,
            'worktree_active_path': event.event_data.get('path')
        })
        return new_state

    def apply_worktree_merged(self, state, event):
        """Apply WorktreeMerged event."""
        new_state = state.copy()
        new_state.update({
            'merge_commit': event.event_data.get('commit_sha'),
            'worktree_merged': True,
            'merge_conflicts': event.event_data.get('conflicts', []),
            'merged_at': event.timestamp
        })
        return new_state

    def apply_worktree_deleted(self, state, event):
        """Apply WorktreeDeleted event."""
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
            'status': 'planned',
            'tests_passing': False,
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
        """Apply TestsStarted event."""
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()
        test_key = f"{event.event_data.get('test_file', 'unknown')}-{event.timestamp}"
        test_results[test_key] = {
            'test_file': event.event_data.get('test_file'),
            'feature': event.event_data.get('feature'),
            'status': 'running',
            'started_at': event.timestamp
        }
        new_state['test_results'] = test_results
        return new_state

    def apply_tests_passed(self, state, event):
        """Apply TestsPassed event."""
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()

        # Find the most recent test run for this test file
        test_file = event.event_data.get('test_file')
        for key, result in test_results.items():
            if result.get('test_file') == test_file and result.get('status') == 'running':
                result.update({
                    'status': 'passed',
                    'count': event.event_data.get('count'),
                    'duration_ms': event.event_data.get('duration_ms'),
                    'completed_at': event.timestamp
                })
                break

        new_state['test_results'] = test_results
        return new_state

    def apply_tests_failed(self, state, event):
        """Apply TestsFailed event."""
        new_state = state.copy()
        test_results = new_state.get('test_results', {}).copy()

        # Find the most recent test run for this test file
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
        """Apply CommitCreated event."""
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
        """Apply CommitFailed event."""
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
        """Provide the comprehensive projection builder."""
        return ComprehensiveProjectionBuilder()

    @pytest.fixture
    def initial_state(self, builder):
        """Provide initial state."""
        return builder.get_initial_state()

    # Workflow lifecycle event tests
    def test_workflow_started_event_handler(self, builder, initial_state):
        """Test workflow.started event handler with all data fields."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.started",
            event_data={
                'description': 'Implement user authentication system',
                'beads_task_id': 'beads-auth-456'
            }
        )

        result = builder.apply_event(initial_state, event)

        assert result['workflow_id'] == "test-workflow-123"
        assert result['phase'] == 'planning'
        assert result['status'] == 'active'
        assert result['description'] == 'Implement user authentication system'
        assert result['beads_task_id'] == 'beads-auth-456'
        assert result['started_at'] == event.timestamp

    def test_workflow_completed_event_handler(self, builder):
        """Test workflow.completed event handler with duration and cost."""
        state = {
            'workflow_id': 'test-workflow-123',
            'status': 'active',
            'phase': 'implementing'
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.completed",
            event_data={
                'duration_ms': 180000,
                'total_cost': 89.45
            }
        )

        result = builder.apply_event(state, event)

        assert result['phase'] == 'complete'
        assert result['status'] == 'completed'
        assert result['duration_ms'] == 180000
        assert result['total_cost'] == 89.45
        assert result['completed_at'] == event.timestamp

    def test_workflow_failed_event_handler(self, builder):
        """Test workflow.failed event handler with error details."""
        state = {
            'workflow_id': 'test-workflow-123',
            'status': 'active',
            'phase': 'implementing'
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="workflow.failed",
            event_data={
                'error': 'Compilation failed due to syntax errors',
                'phase': 'implementing'
            }
        )

        result = builder.apply_event(state, event)

        assert result['status'] == 'failed'
        assert result['error'] == 'Compilation failed due to syntax errors'
        assert result['failed_phase'] == 'implementing'
        assert result['failed_at'] == event.timestamp

    # Worktree lifecycle event tests
    def test_worktree_created_event_handler(self, builder, initial_state):
        """Test worktree.created event handler with path and branch info."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.created",
            event_data={
                'path': '/repo/trees/beads-workflow-123',
                'branch': 'beads/workflow-123',
                'base_commit': 'abc123def456789'
            }
        )

        result = builder.apply_event(initial_state, event)

        assert result['worktree_path'] == '/repo/trees/beads-workflow-123'
        assert result['worktree_branch'] == 'beads/workflow-123'
        assert result['base_commit'] == 'abc123def456789'
        assert result['worktree_created_at'] == event.timestamp

    def test_worktree_active_event_handler(self, builder):
        """Test worktree.active event handler (heartbeat)."""
        state = {'worktree_path': '/repo/trees/beads-workflow-123'}

        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.active",
            event_data={'path': '/repo/trees/beads-workflow-123'}
        )

        result = builder.apply_event(state, event)

        assert result['worktree_last_active'] == event.timestamp
        assert result['worktree_active_path'] == '/repo/trees/beads-workflow-123'

    def test_worktree_merged_event_handler(self, builder):
        """Test worktree.merged event handler with merge details."""
        state = {
            'worktree_path': '/repo/trees/beads-workflow-123',
            'worktree_merged': False
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.merged",
            event_data={
                'commit_sha': 'def456abc789123',
                'conflicts': []
            }
        )

        result = builder.apply_event(state, event)

        assert result['merge_commit'] == 'def456abc789123'
        assert result['worktree_merged'] == True
        assert result['merge_conflicts'] == []
        assert result['merged_at'] == event.timestamp

    def test_worktree_merged_with_conflicts(self, builder):
        """Test worktree.merged event handler with merge conflicts."""
        state = {'worktree_merged': False}

        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.merged",
            event_data={
                'commit_sha': 'def456abc789123',
                'conflicts': ['src/main.py', 'tests/test_auth.py']
            }
        )

        result = builder.apply_event(state, event)

        assert result['merge_conflicts'] == ['src/main.py', 'tests/test_auth.py']

    def test_worktree_deleted_event_handler(self, builder):
        """Test worktree.deleted event handler with deletion reason."""
        state = {'worktree_path': '/repo/trees/beads-workflow-123'}

        event = Event(
            workflow_id="test-workflow-123",
            event_type="worktree.deleted",
            event_data={'reason': 'merged'}
        )

        result = builder.apply_event(state, event)

        assert result['worktree_deleted'] == True
        assert result['deletion_reason'] == 'merged'
        assert result['deleted_at'] == event.timestamp

    # Feature lifecycle event tests
    def test_feature_planned_event_handler(self, builder, initial_state):
        """Test feature.planned event handler with complete feature details."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.planned",
            event_data={
                'name': 'user-authentication',
                'description': 'Implement JWT-based user authentication',
                'test_file': 'tests/core/test_auth.py'
            }
        )

        result = builder.apply_event(initial_state, event)

        assert len(result['features']) == 1
        feature = result['features'][0]
        assert feature['name'] == 'user-authentication'
        assert feature['description'] == 'Implement JWT-based user authentication'
        assert feature['test_file'] == 'tests/core/test_auth.py'
        assert feature['status'] == 'planned'
        assert feature['tests_passing'] == False
        assert feature['planned_at'] == event.timestamp

    def test_feature_started_event_handler(self, builder):
        """Test feature.started event handler updates feature status."""
        state = {
            'features': [{
                'name': 'user-authentication',
                'description': 'Implement JWT-based user authentication',
                'status': 'planned',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.started",
            event_data={'name': 'user-authentication'}
        )

        result = builder.apply_event(state, event)

        feature = result['features'][0]
        assert feature['status'] == 'in_progress'
        assert feature['started_at'] == event.timestamp

    def test_feature_completed_event_handler(self, builder):
        """Test feature.completed event handler with test results and timing."""
        state = {
            'features': [{
                'name': 'user-authentication',
                'status': 'in_progress',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.completed",
            event_data={
                'name': 'user-authentication',
                'tests_passing': True,
                'duration_ms': 45000
            }
        )

        result = builder.apply_event(state, event)

        feature = result['features'][0]
        assert feature['status'] == 'completed'
        assert feature['tests_passing'] == True
        assert feature['duration_ms'] == 45000
        assert feature['completed_at'] == event.timestamp

    def test_feature_failed_event_handler(self, builder):
        """Test feature.failed event handler with error information."""
        state = {
            'features': [{
                'name': 'user-authentication',
                'status': 'in_progress',
                'tests_passing': False
            }]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.failed",
            event_data={
                'name': 'user-authentication',
                'error': 'Database connection timeout during tests'
            }
        )

        result = builder.apply_event(state, event)

        feature = result['features'][0]
        assert feature['status'] == 'failed'
        assert feature['error'] == 'Database connection timeout during tests'
        assert feature['failed_at'] == event.timestamp

    # Phase transition event tests
    def test_phase_changed_event_handler(self, builder):
        """Test phase.changed event handler with phase transition tracking."""
        state = {'phase': 'planning'}

        event = Event(
            workflow_id="test-workflow-123",
            event_type="phase.changed",
            event_data={
                'from_phase': 'planning',
                'to_phase': 'implementing'
            }
        )

        result = builder.apply_event(state, event)

        assert result['previous_phase'] == 'planning'
        assert result['phase'] == 'implementing'
        assert result['phase_changed_at'] == event.timestamp

    # Test event tests
    def test_tests_started_event_handler(self, builder, initial_state):
        """Test tests.started event handler tracks test execution start."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="tests.started",
            event_data={
                'test_file': 'tests/core/test_auth.py',
                'feature': 'user-authentication'
            }
        )

        result = builder.apply_event(initial_state, event)

        test_results = result['test_results']
        assert len(test_results) == 1

        # Get the test result (key includes timestamp)
        test_key = list(test_results.keys())[0]
        test_result = test_results[test_key]

        assert test_result['test_file'] == 'tests/core/test_auth.py'
        assert test_result['feature'] == 'user-authentication'
        assert test_result['status'] == 'running'
        assert test_result['started_at'] == event.timestamp

    def test_tests_passed_event_handler(self, builder):
        """Test tests.passed event handler updates test results with success metrics."""
        state = {
            'test_results': {
                'tests/core/test_auth.py-2025-01-02T10:00:00': {
                    'test_file': 'tests/core/test_auth.py',
                    'feature': 'user-authentication',
                    'status': 'running',
                    'started_at': datetime(2025, 1, 2, 10, 0, 0)
                }
            }
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="tests.passed",
            event_data={
                'test_file': 'tests/core/test_auth.py',
                'feature': 'user-authentication',
                'count': 15,
                'duration_ms': 3500
            }
        )

        result = builder.apply_event(state, event)

        test_key = 'tests/core/test_auth.py-2025-01-02T10:00:00'
        test_result = result['test_results'][test_key]

        assert test_result['status'] == 'passed'
        assert test_result['count'] == 15
        assert test_result['duration_ms'] == 3500
        assert test_result['completed_at'] == event.timestamp

    def test_tests_failed_event_handler(self, builder):
        """Test tests.failed event handler tracks test failures."""
        state = {
            'test_results': {
                'tests/core/test_auth.py-2025-01-02T10:00:00': {
                    'test_file': 'tests/core/test_auth.py',
                    'feature': 'user-authentication',
                    'status': 'running',
                    'started_at': datetime(2025, 1, 2, 10, 0, 0)
                }
            }
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="tests.failed",
            event_data={
                'test_file': 'tests/core/test_auth.py',
                'feature': 'user-authentication',
                'failures': [
                    'test_login_with_invalid_credentials',
                    'test_token_expiration'
                ]
            }
        )

        result = builder.apply_event(state, event)

        test_key = 'tests/core/test_auth.py-2025-01-02T10:00:00'
        test_result = result['test_results'][test_key]

        assert test_result['status'] == 'failed'
        assert test_result['failures'] == [
            'test_login_with_invalid_credentials',
            'test_token_expiration'
        ]
        assert test_result['completed_at'] == event.timestamp

    # Commit event tests
    def test_commit_created_event_handler(self, builder, initial_state):
        """Test commit.created event handler tracks successful commits."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="commit.created",
            event_data={
                'commit_sha': 'abc123def456789',
                'message': 'Implement user authentication endpoints',
                'files': ['src/auth.py', 'tests/test_auth.py', 'src/routes.py']
            }
        )

        result = builder.apply_event(initial_state, event)

        assert len(result['commits']) == 1
        commit = result['commits'][0]

        assert commit['commit_sha'] == 'abc123def456789'
        assert commit['message'] == 'Implement user authentication endpoints'
        assert commit['files'] == ['src/auth.py', 'tests/test_auth.py', 'src/routes.py']
        assert commit['created_at'] == event.timestamp

    def test_commit_failed_event_handler(self, builder, initial_state):
        """Test commit.failed event handler tracks commit failures."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="commit.failed",
            event_data={
                'error': 'Pre-commit hook failed: linting errors found',
                'files': ['src/auth.py', 'tests/test_auth.py']
            }
        )

        result = builder.apply_event(initial_state, event)

        assert len(result['errors']) == 1
        error = result['errors'][0]

        assert error['type'] == 'commit_failed'
        assert error['error'] == 'Pre-commit hook failed: linting errors found'
        assert error['files'] == ['src/auth.py', 'tests/test_auth.py']
        assert error['failed_at'] == event.timestamp

    # Multiple events integration tests
    def test_multiple_commits_tracking(self, builder, initial_state):
        """Test that multiple commits are tracked correctly."""
        # First commit
        event1 = Event(
            workflow_id="test-workflow-123",
            event_type="commit.created",
            event_data={
                'commit_sha': 'abc123',
                'message': 'Add auth model',
                'files': ['src/models/auth.py']
            }
        )

        state1 = builder.apply_event(initial_state, event1)

        # Second commit
        event2 = Event(
            workflow_id="test-workflow-123",
            event_type="commit.created",
            event_data={
                'commit_sha': 'def456',
                'message': 'Add auth tests',
                'files': ['tests/test_auth.py']
            }
        )

        final_state = builder.apply_event(state1, event2)

        assert len(final_state['commits']) == 2
        assert final_state['commits'][0]['commit_sha'] == 'abc123'
        assert final_state['commits'][1]['commit_sha'] == 'def456'

    def test_feature_lifecycle_complete_flow(self, builder, initial_state):
        """Test complete feature lifecycle from planned to completed."""
        # Feature planned
        planned_event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.planned",
            event_data={
                'name': 'api-endpoints',
                'description': 'REST API endpoints for user management',
                'test_file': 'tests/api/test_users.py'
            }
        )

        state1 = builder.apply_event(initial_state, planned_event)

        # Feature started
        started_event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.started",
            event_data={'name': 'api-endpoints'}
        )

        state2 = builder.apply_event(state1, started_event)

        # Feature completed
        completed_event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.completed",
            event_data={
                'name': 'api-endpoints',
                'tests_passing': True,
                'duration_ms': 60000
            }
        )

        final_state = builder.apply_event(state2, completed_event)

        feature = final_state['features'][0]
        assert feature['name'] == 'api-endpoints'
        assert feature['status'] == 'completed'
        assert feature['tests_passing'] == True
        assert feature['duration_ms'] == 60000
        assert 'planned_at' in feature
        assert 'started_at' in feature
        assert 'completed_at' in feature

    def test_unknown_event_type_handling(self, builder, initial_state):
        """Test that unknown event types raise appropriate errors."""
        event = Event(
            workflow_id="test-workflow-123",
            event_type="unknown.event.type",
            event_data={}
        )

        with pytest.raises(ValueError, match="Unknown event type: unknown.event.type"):
            builder.apply_event(initial_state, event)

    def test_state_immutability_across_all_events(self, builder):
        """Test that state immutability is preserved across all event types."""
        original_state = {
            'workflow_id': 'test-123',
            'features': [{'name': 'existing-feature', 'status': 'completed'}],
            'commits': [{'commit_sha': 'existing123', 'message': 'existing commit'}]
        }

        # Create a deep copy to compare against
        expected_unchanged_state = {
            'workflow_id': 'test-123',
            'features': [{'name': 'existing-feature', 'status': 'completed'}],
            'commits': [{'commit_sha': 'existing123', 'message': 'existing commit'}]
        }

        event = Event(
            workflow_id="test-workflow-123",
            event_type="feature.planned",
            event_data={
                'name': 'new-feature',
                'description': 'A new feature'
            }
        )

        result_state = builder.apply_event(original_state, event)

        # Original state should be unchanged
        assert original_state == expected_unchanged_state

        # Result should be different and contain new feature
        assert len(result_state['features']) == 2
        assert result_state['features'][1]['name'] == 'new-feature'