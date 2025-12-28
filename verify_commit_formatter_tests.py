#!/usr/bin/env python3
"""Verify CommitMessageFormatter tests manually."""

import sys
from jean_claude.core.commit_message_formatter import CommitMessageFormatter

def test_basic_feat_commit():
    """Test generating a basic feat commit message."""
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="auth",
        summary="add login functionality",
        body_items=["Implement JWT authentication", "Add password hashing"],
        beads_task_id="task-123.1",
        feature_number=1
    )
    message = formatter.format()
    assert message.startswith("feat(auth): add login functionality")
    assert "- Implement JWT authentication" in message
    assert "- Add password hashing" in message
    assert "Beads-Task-Id: task-123.1" in message
    assert "Feature-Number: 1" in message
    print("✓ test_basic_feat_commit passed")

def test_fix_commit_with_scope():
    """Test generating a fix commit message with scope."""
    formatter = CommitMessageFormatter(
        commit_type="fix",
        scope="api",
        summary="resolve timeout in user endpoint",
        body_items=["Increase connection timeout to 30s"],
        beads_task_id="task-456.2",
        feature_number=3
    )
    message = formatter.format()
    assert message.startswith("fix(api): resolve timeout in user endpoint")
    assert "- Increase connection timeout to 30s" in message
    assert "Beads-Task-Id: task-456.2" in message
    assert "Feature-Number: 3" in message
    print("✓ test_fix_commit_with_scope passed")

def test_commit_without_scope():
    """Test generating a commit message without scope."""
    formatter = CommitMessageFormatter(
        commit_type="docs",
        scope=None,
        summary="update README with installation instructions",
        body_items=["Add pip install command", "Add usage examples"],
        beads_task_id="task-789.1",
        feature_number=5
    )
    message = formatter.format()
    assert message.startswith("docs: update README with installation instructions")
    assert "- Add pip install command" in message
    assert "- Add usage examples" in message
    print("✓ test_commit_without_scope passed")

def test_commit_with_empty_body_items():
    """Test generating a commit message with no body items."""
    formatter = CommitMessageFormatter(
        commit_type="refactor",
        scope="database",
        summary="simplify query builder",
        body_items=[],
        beads_task_id="task-111.1",
        feature_number=2
    )
    message = formatter.format()
    assert message.startswith("refactor(database): simplify query builder")
    assert "Beads-Task-Id: task-111.1" in message
    assert "Feature-Number: 2" in message
    print("✓ test_commit_with_empty_body_items passed")

def test_all_valid_commit_types():
    """Test all valid conventional commit types."""
    valid_types = ["feat", "fix", "refactor", "test", "docs"]
    for commit_type in valid_types:
        formatter = CommitMessageFormatter(
            commit_type=commit_type,
            scope="test",
            summary="test message",
            body_items=["Test item"],
            beads_task_id="test.1",
            feature_number=1
        )
        message = formatter.format()
        assert message.startswith(f"{commit_type}(test): test message")
    print("✓ test_all_valid_commit_types passed")

def test_invalid_commit_type():
    """Test that invalid commit types raise ValueError."""
    try:
        CommitMessageFormatter(
            commit_type="invalid",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id="test.1",
            feature_number=1
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid commit_type" in str(e)
    print("✓ test_invalid_commit_type passed")

def test_empty_summary_raises_error():
    """Test that empty summary raises ValueError."""
    try:
        CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="",
            body_items=[],
            beads_task_id="test.1",
            feature_number=1
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "summary cannot be empty" in str(e)
    print("✓ test_empty_summary_raises_error passed")

def test_multiple_body_items():
    """Test commit with multiple body items."""
    body_items = [
        "Add user registration endpoint",
        "Add email verification",
        "Add password reset functionality",
        "Update user model schema"
    ]
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="users",
        summary="implement complete user management",
        body_items=body_items,
        beads_task_id="task-999.5",
        feature_number=7
    )
    message = formatter.format()
    for item in body_items:
        assert f"- {item}" in message
    print("✓ test_multiple_body_items passed")

def test_message_structure():
    """Test that the commit message has proper structure."""
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="core",
        summary="add new feature",
        body_items=["First change", "Second change"],
        beads_task_id="task-abc.1",
        feature_number=4
    )
    message = formatter.format()
    lines = message.split("\n")
    assert lines[0] == "feat(core): add new feature"
    assert lines[1] == ""
    assert "- First change" in message
    assert "- Second change" in message
    assert message.strip().endswith("Feature-Number: 4")
    print("✓ test_message_structure passed")

def test_scope_with_special_characters():
    """Test scope with hyphens and underscores."""
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="user-auth",
        summary="add OAuth support",
        body_items=["Integrate OAuth provider"],
        beads_task_id="task-123.1",
        feature_number=1
    )
    message = formatter.format()
    assert message.startswith("feat(user-auth): add OAuth support")
    print("✓ test_scope_with_special_characters passed")

def test_test_commit_type():
    """Test generating a test commit message."""
    formatter = CommitMessageFormatter(
        commit_type="test",
        scope="api",
        summary="add integration tests for auth endpoints",
        body_items=["Test login endpoint", "Test logout endpoint", "Test token refresh"],
        beads_task_id="task-test.1",
        feature_number=6
    )
    message = formatter.format()
    assert message.startswith("test(api): add integration tests for auth endpoints")
    assert "- Test login endpoint" in message
    assert "- Test logout endpoint" in message
    assert "- Test token refresh" in message
    print("✓ test_test_commit_type passed")

def test_beads_task_id_format():
    """Test various beads task ID formats."""
    task_ids = ["task-123.1", "feature-456.2", "bug-789.3", "simple.4"]
    for task_id in task_ids:
        formatter = CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id=task_id,
            feature_number=1
        )
        message = formatter.format()
        assert f"Beads-Task-Id: {task_id}" in message
    print("✓ test_beads_task_id_format passed")

def test_feature_number_must_be_positive():
    """Test that feature number must be positive."""
    try:
        CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id="test.1",
            feature_number=0
        )
        assert False, "Should have raised ValueError for feature_number=0"
    except ValueError as e:
        assert "feature_number must be positive" in str(e)

    try:
        CommitMessageFormatter(
            commit_type="feat",
            scope="test",
            summary="test message",
            body_items=[],
            beads_task_id="test.1",
            feature_number=-1
        )
        assert False, "Should have raised ValueError for feature_number=-1"
    except ValueError as e:
        assert "feature_number must be positive" in str(e)
    print("✓ test_feature_number_must_be_positive passed")

def test_complete_realistic_commit():
    """Test a complete realistic commit message."""
    formatter = CommitMessageFormatter(
        commit_type="feat",
        scope="commit-workflow",
        summary="create CommitMessageFormatter class",
        body_items=[
            "Accept commit_type, scope, summary, body_items parameters",
            "Generate conventional commit format",
            "Include Beads-Task-Id and Feature-Number trailers",
            "Validate commit_type against allowed values",
            "Handle optional scope parameter"
        ],
        beads_task_id="beads-jean_claude-2sz.8.1",
        feature_number=1
    )
    message = formatter.format()
    assert message.startswith("feat(commit-workflow): create CommitMessageFormatter class")
    assert "\n\n" in message
    assert "- Accept commit_type, scope, summary, body_items parameters" in message
    assert "- Generate conventional commit format" in message
    assert "Beads-Task-Id: beads-jean_claude-2sz.8.1" in message
    assert "Feature-Number: 1" in message
    for line in message.split("\n"):
        assert line == line.rstrip(), f"Line has trailing whitespace: {repr(line)}"
    print("✓ test_complete_realistic_commit passed")

if __name__ == "__main__":
    try:
        test_basic_feat_commit()
        test_fix_commit_with_scope()
        test_commit_without_scope()
        test_commit_with_empty_body_items()
        test_all_valid_commit_types()
        test_invalid_commit_type()
        test_empty_summary_raises_error()
        test_multiple_body_items()
        test_message_structure()
        test_scope_with_special_characters()
        test_test_commit_type()
        test_beads_task_id_format()
        test_feature_number_must_be_positive()
        test_complete_realistic_commit()

        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
