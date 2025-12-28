# ABOUTME: Verification-first mode for Jean Claude workflows
# ABOUTME: Runs tests for completed features before starting new work to catch regressions

"""Verification module for testing completed features.

This module implements the verification-first pattern from autonomous agent best practices:
Before starting new work, verify all existing work still passes to prevent regression cascades.
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from jean_claude.core.state import WorkflowState


class VerificationResult(BaseModel):
    """Result of running verification tests."""

    passed: bool
    test_output: str
    failed_tests: list[str] = []
    duration_ms: int
    tests_run: int = 0
    skipped: bool = False
    skip_reason: str = ""


def run_verification(state: WorkflowState, project_root: Path) -> VerificationResult:
    """Run all tests for completed features and return results.

    This implements the verification-first pattern: before starting new work,
    verify that existing completed features still pass their tests.

    Args:
        state: Current workflow state with feature tracking
        project_root: Root directory of the project

    Returns:
        VerificationResult with test outcomes and metadata

    Example:
        >>> state = WorkflowState.load("my-workflow-id", Path.cwd())
        >>> result = run_verification(state, Path.cwd())
        >>> if not result.passed:
        ...     print(f"Fix these tests first: {result.failed_tests}")
    """
    start_time = time.time()

    # Collect test files from completed features
    completed_features = [f for f in state.features if f.status == "completed"]

    if not completed_features:
        # No completed features to verify
        return VerificationResult(
            passed=True,
            test_output="No completed features to verify",
            duration_ms=0,
            skipped=True,
            skip_reason="No completed features",
        )

    test_files = [f.test_file for f in completed_features if f.test_file]

    if not test_files:
        # Completed features but no test files specified
        return VerificationResult(
            passed=True,
            test_output="No test files specified for completed features",
            duration_ms=int((time.time() - start_time) * 1000),
            skipped=True,
            skip_reason="No test files found",
        )

    # Verify test files exist
    existing_test_files = []
    for test_file in test_files:
        test_path = project_root / test_file
        if test_path.exists():
            existing_test_files.append(str(test_path))

    if not existing_test_files:
        # Test files specified but don't exist yet
        return VerificationResult(
            passed=True,
            test_output=f"Test files not found: {', '.join(test_files)}",
            duration_ms=int((time.time() - start_time) * 1000),
            skipped=True,
            skip_reason="Test files not created yet",
        )

    # Run pytest on the collected test files
    # Use 'uv run' to ensure tests run in the project's virtual environment
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-v", "--tb=short", "--no-header", *existing_test_files],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        duration_ms = int((time.time() - start_time) * 1000)
        test_output = result.stdout + result.stderr
        passed = result.returncode == 0

        # Parse failed tests from output if any
        failed_tests = _parse_failed_tests(test_output) if not passed else []

        # Count tests run
        tests_run = len(existing_test_files)

        return VerificationResult(
            passed=passed,
            test_output=test_output,
            failed_tests=failed_tests,
            duration_ms=duration_ms,
            tests_run=tests_run,
        )

    except subprocess.TimeoutExpired:
        duration_ms = int((time.time() - start_time) * 1000)
        return VerificationResult(
            passed=False,
            test_output="Verification timed out after 5 minutes",
            failed_tests=["timeout"],
            duration_ms=duration_ms,
        )

    except FileNotFoundError:
        duration_ms = int((time.time() - start_time) * 1000)
        return VerificationResult(
            passed=False,
            test_output="uv or pytest not found. Ensure uv is installed and pytest is in dev dependencies: uv add --dev pytest",
            failed_tests=["runner_not_found"],
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        return VerificationResult(
            passed=False,
            test_output=f"Verification error: {e}",
            failed_tests=["verification_error"],
            duration_ms=duration_ms,
        )


def _parse_failed_tests(output: str) -> list[str]:
    """Parse failed test names from pytest output.

    Args:
        output: Full pytest output

    Returns:
        List of failed test identifiers (e.g., "tests/test_foo.py::test_bar")
    """
    failed = []
    for line in output.split("\n"):
        # Look for FAILED markers in pytest output
        if line.startswith("FAILED "):
            # Format: "FAILED tests/test_foo.py::test_bar - AssertionError: ..."
            parts = line.split(" - ", 1)
            if parts:
                test_id = parts[0].replace("FAILED ", "").strip()
                failed.append(test_id)
    return failed


def should_verify(state: WorkflowState, last_verified_at: Optional[float] = None) -> bool:
    """Determine if verification should run based on state and timing.

    Verification should run if:
    - There are completed features with tests
    - It's been more than 5 minutes since last verification (if applicable)

    Args:
        state: Current workflow state
        last_verified_at: Unix timestamp of last verification (optional)

    Returns:
        True if verification should run, False otherwise
    """
    # No completed features → no need to verify
    completed_with_tests = [
        f for f in state.features if f.status == "completed" and f.test_file
    ]

    if not completed_with_tests:
        return False

    # If never verified, should verify
    if last_verified_at is None:
        return True

    # If last verified more than 5 minutes ago, verify again
    time_since_last = time.time() - last_verified_at
    return time_since_last > 300  # 5 minutes
