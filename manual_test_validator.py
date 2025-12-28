#!/usr/bin/env python3
"""Manual test of TestRunnerValidator functionality."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.test_runner_validator import TestRunnerValidator


def test_basic_functionality():
    """Test basic functionality of TestRunnerValidator."""
    print("\n" + "=" * 70)
    print("Testing Basic Functionality")
    print("=" * 70)

    # Test 1: Instantiation
    print("\n1. Testing instantiation...")
    validator = TestRunnerValidator()
    print(f"   ✅ Created validator with command: {validator.test_command}")
    print(f"   ✅ Repo path: {validator.repo_path}")

    # Test 2: Parse success output
    print("\n2. Testing parse_output with success...")
    success_output = "===== 10 passed in 2.34s ====="
    result = validator.parse_output(success_output, exit_code=0)
    assert result["passed"] is True
    assert result["total_tests"] == 10
    assert result["failed_tests"] == 0
    print(f"   ✅ Parsed success: {result['total_tests']} tests passed")

    # Test 3: Parse failure output
    print("\n3. Testing parse_output with failures...")
    failure_output = "===== 3 failed, 7 passed in 3.45s ====="
    result = validator.parse_output(failure_output, exit_code=1)
    assert result["passed"] is False
    assert result["total_tests"] == 10
    assert result["failed_tests"] == 3
    print(f"   ✅ Parsed failure: {result['failed_tests']} failed, {result['total_tests'] - result['failed_tests']} passed")

    # Test 4: Parse failed test names
    print("\n4. Testing extraction of failed test names...")
    detailed_output = """
    FAILED tests/test_auth.py::test_login - AssertionError
    FAILED tests/test_api.py::test_endpoint - ValueError
    ===== 2 failed, 8 passed in 3.00s =====
    """
    result = validator.parse_output(detailed_output, exit_code=1)
    assert len(result["failed_test_names"]) == 2
    print(f"   ✅ Extracted {len(result['failed_test_names'])} failed test names")
    for name in result["failed_test_names"]:
        print(f"      - {name}")

    print("\n" + "=" * 70)
    print("✅ All basic functionality tests passed!")
    print("=" * 70)


def test_mocked_run_tests():
    """Test run_tests with mocked subprocess."""
    print("\n" + "=" * 70)
    print("Testing run_tests with Mock")
    print("=" * 70)

    with patch('subprocess.run') as mock_run:
        # Test 1: Successful test run
        print("\n1. Testing successful test run...")
        mock_run.return_value = Mock(
            returncode=0,
            stdout="===== 15 passed in 3.45s =====",
            stderr=""
        )

        validator = TestRunnerValidator()
        result = validator.run_tests()

        assert result["passed"] is True
        assert result["exit_code"] == 0
        assert "15 passed" in result["output"]
        print("   ✅ Successful test run works correctly")

        # Test 2: Failed test run
        print("\n2. Testing failed test run...")
        mock_run.return_value = Mock(
            returncode=1,
            stdout="===== 2 failed, 8 passed in 3.45s =====",
            stderr=""
        )

        result = validator.run_tests()

        assert result["passed"] is False
        assert result["exit_code"] == 1
        assert "2 failed" in result["output"]
        print("   ✅ Failed test run works correctly")

    print("\n" + "=" * 70)
    print("✅ All mocked run_tests tests passed!")
    print("=" * 70)


def test_validate_method():
    """Test the validate method."""
    print("\n" + "=" * 70)
    print("Testing validate() method")
    print("=" * 70)

    with patch('subprocess.run') as mock_run:
        # Test 1: Validation with passing tests
        print("\n1. Testing validation with passing tests...")
        mock_run.return_value = Mock(
            returncode=0,
            stdout="===== 20 passed in 5.00s =====",
            stderr=""
        )

        validator = TestRunnerValidator()
        result = validator.validate()

        assert result["can_commit"] is True
        assert result["passed"] is True
        assert "pass" in result["message"].lower()
        print(f"   ✅ Can commit: {result['can_commit']}")
        print(f"   ✅ Message: {result['message']}")

        # Test 2: Validation with failing tests
        print("\n2. Testing validation with failing tests...")
        mock_run.return_value = Mock(
            returncode=1,
            stdout="===== 5 failed, 15 passed in 6.00s =====",
            stderr=""
        )

        result = validator.validate()

        assert result["can_commit"] is False
        assert result["passed"] is False
        assert "fail" in result["message"].lower()
        assert result["error_details"] is not None
        print(f"   ✅ Can commit: {result['can_commit']}")
        print(f"   ✅ Message: {result['message']}")
        print(f"   ✅ Failed tests: {result['failed_tests']}")

    print("\n" + "=" * 70)
    print("✅ All validate() tests passed!")
    print("=" * 70)


def main():
    """Run all manual tests."""
    try:
        test_basic_functionality()
        test_mocked_run_tests()
        test_validate_method()

        print("\n" + "=" * 70)
        print("🎉 ALL MANUAL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\nTestRunnerValidator is working correctly!")
        print("Ready to run the full pytest suite.")
        return 0

    except AssertionError as e:
        print(f"\n❌ Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
