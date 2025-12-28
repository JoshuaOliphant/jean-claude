#!/usr/bin/env python3
"""Verify BeadsTrailerFormatter implementation."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.beads_trailer_formatter import BeadsTrailerFormatter


def test_basic_functionality():
    """Test basic BeadsTrailerFormatter functionality."""
    print("Testing BeadsTrailerFormatter initialization...")

    # Test basic initialization
    formatter = BeadsTrailerFormatter(
        task_id="jean_claude-2sz.8",
        feature_number=1,
        total_features=10
    )
    assert formatter.task_id == "jean_claude-2sz.8"
    assert formatter.feature_number == 1
    assert formatter.total_features == 10
    print("✓ Initialization works")

    # Test format output
    result = formatter.format()
    assert isinstance(result, str)
    assert "Beads: jean_claude-2sz.8" in result
    assert "Feature: 1/10" in result
    print("✓ Basic formatting works")
    print(f"  Output:\n{result}")

    # Test format structure
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert lines[0] == "Beads: jean_claude-2sz.8"
    assert lines[1] == "Feature: 1/10"
    print("✓ Format structure is correct")

    print("\n✅ Basic functionality tests passed!")
    return True


def test_validation():
    """Test input validation."""
    print("\nTesting input validation...")

    # Test empty task_id
    try:
        BeadsTrailerFormatter(task_id="", feature_number=1, total_features=5)
        assert False, "Should raise ValueError for empty task_id"
    except ValueError as e:
        assert "task_id cannot be empty" in str(e)
        print("✓ Empty task_id validation works")

    # Test invalid task_id format (no period)
    try:
        BeadsTrailerFormatter(task_id="no-period", feature_number=1, total_features=5)
        assert False, "Should raise ValueError for invalid task_id format"
    except ValueError as e:
        assert "Invalid task_id format" in str(e)
        print("✓ Invalid task_id format validation works")

    # Test invalid task_id format (no number after period)
    try:
        BeadsTrailerFormatter(task_id="abc.xyz", feature_number=1, total_features=5)
        assert False, "Should raise ValueError for invalid task_id format"
    except ValueError as e:
        assert "Invalid task_id format" in str(e)
        print("✓ Task_id number validation works")

    # Test zero feature_number
    try:
        BeadsTrailerFormatter(task_id="test.1", feature_number=0, total_features=5)
        assert False, "Should raise ValueError for zero feature_number"
    except ValueError as e:
        assert "feature_number must be positive" in str(e)
        print("✓ Zero feature_number validation works")

    # Test negative feature_number
    try:
        BeadsTrailerFormatter(task_id="test.1", feature_number=-1, total_features=5)
        assert False, "Should raise ValueError for negative feature_number"
    except ValueError as e:
        assert "feature_number must be positive" in str(e)
        print("✓ Negative feature_number validation works")

    # Test zero total_features
    try:
        BeadsTrailerFormatter(task_id="test.1", feature_number=1, total_features=0)
        assert False, "Should raise ValueError for zero total_features"
    except ValueError as e:
        assert "total_features must be positive" in str(e)
        print("✓ Zero total_features validation works")

    # Test feature_number > total_features
    try:
        BeadsTrailerFormatter(task_id="test.1", feature_number=6, total_features=5)
        assert False, "Should raise ValueError for feature_number > total_features"
    except ValueError as e:
        assert "cannot exceed total_features" in str(e)
        print("✓ Feature_number bounds validation works")

    print("\n✅ Validation tests passed!")
    return True


def test_from_task_metadata():
    """Test from_task_metadata factory method."""
    print("\nTesting from_task_metadata factory method...")

    # Test basic metadata extraction
    metadata = {
        "beads_task_id": "jean_claude-2sz.8",
        "current_feature_index": 5,
        "features": [None] * 10
    }

    formatter = BeadsTrailerFormatter.from_task_metadata(metadata)
    assert formatter.task_id == "jean_claude-2sz.8"
    assert formatter.feature_number == 6  # 0-indexed to 1-indexed
    assert formatter.total_features == 10
    print("✓ Metadata extraction works")

    result = formatter.format()
    assert "Beads: jean_claude-2sz.8" in result
    assert "Feature: 6/10" in result
    print("✓ Metadata-based formatting works")
    print(f"  Output:\n{result}")

    # Test with first feature (index 0)
    metadata2 = {
        "beads_task_id": "test.1",
        "current_feature_index": 0,
        "features": [None] * 5
    }
    formatter2 = BeadsTrailerFormatter.from_task_metadata(metadata2)
    assert formatter2.feature_number == 1
    print("✓ First feature (index 0) conversion works")

    # Test missing beads_task_id
    try:
        BeadsTrailerFormatter.from_task_metadata({
            "current_feature_index": 0,
            "features": [None] * 5
        })
        assert False, "Should raise ValueError for missing beads_task_id"
    except ValueError as e:
        assert "beads_task_id is required" in str(e)
        print("✓ Missing beads_task_id validation works")

    # Test missing current_feature_index
    try:
        BeadsTrailerFormatter.from_task_metadata({
            "beads_task_id": "test.1",
            "features": [None] * 5
        })
        assert False, "Should raise ValueError for missing current_feature_index"
    except ValueError as e:
        assert "current_feature_index is required" in str(e)
        print("✓ Missing current_feature_index validation works")

    # Test missing features
    try:
        BeadsTrailerFormatter.from_task_metadata({
            "beads_task_id": "test.1",
            "current_feature_index": 0
        })
        assert False, "Should raise ValueError for missing features"
    except ValueError as e:
        assert "features is required" in str(e)
        print("✓ Missing features validation works")

    # Test features not a list
    try:
        BeadsTrailerFormatter.from_task_metadata({
            "beads_task_id": "test.1",
            "current_feature_index": 0,
            "features": "not a list"
        })
        assert False, "Should raise ValueError for non-list features"
    except ValueError as e:
        assert "features must be a list" in str(e)
        print("✓ Non-list features validation works")

    # Test empty features list
    try:
        BeadsTrailerFormatter.from_task_metadata({
            "beads_task_id": "test.1",
            "current_feature_index": 0,
            "features": []
        })
        assert False, "Should raise ValueError for empty features"
    except ValueError as e:
        assert "features cannot be empty" in str(e)
        print("✓ Empty features validation works")

    print("\n✅ from_task_metadata tests passed!")
    return True


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")

    # Test single feature workflow
    formatter = BeadsTrailerFormatter(
        task_id="simple.1",
        feature_number=1,
        total_features=1
    )
    result = formatter.format()
    assert "Feature: 1/1" in result
    print("✓ Single feature workflow works")

    # Test large feature numbers
    formatter = BeadsTrailerFormatter(
        task_id="large.10",
        feature_number=99,
        total_features=100
    )
    result = formatter.format()
    assert "Feature: 99/100" in result
    print("✓ Large feature numbers work")

    # Test complex task ID formats
    complex_ids = [
        "beads-jean_claude-2sz.8",
        "my_long_project_name-v2.15",
        "proj_123-abc_xyz.99"
    ]
    for task_id in complex_ids:
        formatter = BeadsTrailerFormatter(
            task_id=task_id,
            feature_number=1,
            total_features=5
        )
        result = formatter.format()
        assert f"Beads: {task_id}" in result
    print("✓ Complex task ID formats work")

    # Test no trailing whitespace
    formatter = BeadsTrailerFormatter(
        task_id="test.1",
        feature_number=1,
        total_features=5
    )
    result = formatter.format()
    for line in result.split("\n"):
        assert line == line.rstrip()
    print("✓ No trailing whitespace")

    print("\n✅ Edge case tests passed!")
    return True


def test_git_trailer_format():
    """Test that output matches git trailer format specification."""
    print("\nTesting git trailer format compliance...")

    formatter = BeadsTrailerFormatter(
        task_id="test.1",
        feature_number=1,
        total_features=5
    )

    result = formatter.format()
    lines = result.split("\n")

    # Each line should follow "Key: Value" format
    for line in lines:
        if line.strip():
            assert ": " in line, f"Line '{line}' doesn't match 'Key: Value' format"
            key, value = line.split(": ", 1)
            assert key.strip() == key, "Key has leading/trailing whitespace"
            assert value.strip() == value, "Value has leading/trailing whitespace"
            assert len(key) > 0, "Key is empty"
            assert len(value) > 0, "Value is empty"

    print("✓ Git trailer format compliance verified")
    print("\n✅ Git trailer format tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_validation()
        test_from_task_metadata()
        test_edge_cases()
        test_git_trailer_format()
        print("\n" + "="*60)
        print("✅ ALL VERIFICATION TESTS PASSED!")
        print("="*60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
