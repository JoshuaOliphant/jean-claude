#!/usr/bin/env python3
"""Manual test of AgentCommitGuidance to verify it works."""

from jean_claude.core.agent_commit_guidance import AgentCommitGuidance


def test_basic_functionality():
    """Test basic functionality of AgentCommitGuidance."""
    print("Testing AgentCommitGuidance basic functionality...")

    guidance = AgentCommitGuidance()
    prompt = guidance.generate_guidance()

    # Check that we get content
    assert prompt, "Prompt should not be empty"
    assert len(prompt) > 100, "Prompt should have substantial content"

    # Check key sections
    required_keywords = [
        "when to commit",
        "feature complete",
        "tests pass",
        "feat",
        "fix",
        "refactor",
        "test",
        "docs",
        "scope",
        "files",
        "beads",
        "example",
    ]

    for keyword in required_keywords:
        assert keyword.lower() in prompt.lower(), f"Missing keyword: {keyword}"

    print("✅ Basic functionality test passed")


def test_with_context():
    """Test generating guidance with feature context."""
    print("\nTesting AgentCommitGuidance with context...")

    guidance = AgentCommitGuidance()
    context = {
        "feature_name": "add-authentication",
        "feature_description": "Implement JWT authentication",
        "beads_task_id": "test-123.1",
        "feature_number": 1,
        "total_features": 5,
    }

    prompt = guidance.generate_guidance(context=context)

    # Check that context is included
    assert "add-authentication" in prompt or "authentication" in prompt.lower()
    assert "test-123.1" in prompt
    assert "1" in prompt and "5" in prompt

    print("✅ Context test passed")


def test_markdown_formatting():
    """Test that output is properly formatted as markdown."""
    print("\nTesting markdown formatting...")

    guidance = AgentCommitGuidance()
    prompt = guidance.generate_guidance()

    # Should have markdown headers
    assert "#" in prompt, "Should have markdown headers"

    # Should have some structure
    has_structure = any(marker in prompt for marker in ["-", "*", "```"])
    assert has_structure, "Should have markdown structure (lists, code blocks, etc.)"

    print("✅ Markdown formatting test passed")


def test_examples():
    """Test that examples are included."""
    print("\nTesting examples...")

    guidance = AgentCommitGuidance()
    prompt = guidance.generate_guidance()

    # Should have examples
    assert "example" in prompt.lower()

    # Should have commit type examples
    has_commit_type = any(
        commit_type in prompt for commit_type in ["feat:", "fix:", "refactor:", "test:", "docs:"]
    )
    assert has_commit_type, "Should have commit type examples"

    # Should have trailer examples
    assert "beads-task-id" in prompt.lower()
    assert "feature-number" in prompt.lower()

    print("✅ Examples test passed")


def main():
    """Run all manual tests."""
    print("=" * 60)
    print("Manual Test Suite for AgentCommitGuidance")
    print("=" * 60)

    try:
        test_basic_functionality()
        test_with_context()
        test_markdown_formatting()
        test_examples()

        print("\n" + "=" * 60)
        print("✅ All manual tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
