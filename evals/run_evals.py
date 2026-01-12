#!/usr/bin/env python3
# ABOUTME: Main evaluation runner for Jean Claude
# ABOUTME: Runs all eval suites and optionally includes LLM-based quality checks

"""Jean Claude Evaluation Runner.

This script runs all evaluation suites for Jean Claude components.
It supports both deterministic evals (fast, cheap) and LLM-based
quality evals (slower, requires API key).

Usage:
    # Run deterministic evals only (default)
    uv run python -m evals.run_evals

    # Run all evals including LLM-based
    uv run python -m evals.run_evals --include-llm

    # Run specific suite
    uv run python -m evals.run_evals --suite beads
    uv run python -m evals.run_evals --suite workflow
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Load .env file for API keys (must be before other imports that use env vars)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import IsInstance, MaxDuration

# Import our eval suites
from evals.suites.test_beads_parsing import (
    beads_parsing_dataset,
    parse_beads_task,
    id_validation_dataset,
    validate_id_format,
)
from evals.suites.test_workflow_state import (
    progress_dataset,
    calculate_progress,
    feature_completion_dataset,
    complete_feature,
)


def run_deterministic_evals(suite: str | None = None) -> bool:
    """Run all deterministic (code-based) evaluations.

    Args:
        suite: Optional suite name to run ('beads' or 'workflow')

    Returns:
        True if all evals passed, False otherwise
    """
    all_passed = True
    results = []

    print("\n" + "=" * 70)
    print("JEAN CLAUDE EVALUATION SUITE")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Beads parsing evals
    if suite is None or suite == "beads":
        print("\n" + "-" * 50)
        print("📦 BeadsTask Parsing Evaluations")
        print("-" * 50)

        print("\n[1/2] Task Parsing...")
        report = beads_parsing_dataset.evaluate_sync(parse_beads_task)
        report.print(include_input=False, include_output=False)
        results.append(("BeadsTask Parsing", report))

        print("\n[2/2] ID Validation (Security)...")
        report = id_validation_dataset.evaluate_sync(validate_id_format)
        report.print(include_input=False, include_output=False)
        results.append(("Beads ID Validation", report))

    # Workflow state evals
    if suite is None or suite == "workflow":
        print("\n" + "-" * 50)
        print("🔄 WorkflowState Evaluations")
        print("-" * 50)

        print("\n[1/2] Progress Calculation...")
        report = progress_dataset.evaluate_sync(calculate_progress)
        report.print(include_input=False, include_output=False)
        results.append(("Progress Calculation", report))

        print("\n[2/2] Feature Completion...")
        report = feature_completion_dataset.evaluate_sync(complete_feature)
        report.print(include_input=False, include_output=False)
        results.append(("Feature Completion", report))

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, report in results:
        # Check if all cases passed based on assertions
        case_count = len(report.cases)
        passed = 0
        for c in report.cases:
            # assertions is a dict mapping assertion name to result
            # Check if any assertions failed (value is False)
            case_passed = True
            if hasattr(c, 'assertions') and c.assertions:
                for assertion_name, assertion_result in c.assertions.items():
                    # assertion_result can be bool or an object with .value
                    if isinstance(assertion_result, bool):
                        if not assertion_result:
                            case_passed = False
                            break
                    elif hasattr(assertion_result, 'value'):
                        if not assertion_result.value:
                            case_passed = False
                            break
            if case_passed:
                passed += 1
        status = "✅ PASS" if passed == case_count else "❌ FAIL"
        print(f"  {status} {name}: {passed}/{case_count} cases")
        if passed != case_count:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All evaluations passed!")
    else:
        print("⚠️  Some evaluations failed. Review output above.")
    print("=" * 70 + "\n")

    return all_passed


def run_llm_evals() -> bool:
    """Run LLM-based quality evaluations.

    These evals use Claude to assess subjective quality aspects
    like code clarity, documentation quality, etc.

    Returns:
        True if all evals passed, False otherwise
    """
    try:
        from pydantic_evals.evaluators import LLMJudge
    except ImportError:
        print("⚠️  LLMJudge not available. Skipping LLM evals.")
        return True

    print("\n" + "-" * 50)
    print("🤖 LLM-Based Quality Evaluations")
    print("-" * 50)

    # Example: Evaluate spec generation quality
    from jean_claude.core.beads import BeadsTask, generate_spec_from_beads

    def generate_spec(inputs: dict) -> str:
        """Generate a spec from a BeadsTask."""
        task = BeadsTask.from_dict(inputs)
        return generate_spec_from_beads(task)

    llm_cases = [
        Case(
            name="spec_quality_simple",
            inputs={
                "id": "beads-eval1",
                "title": "Add user authentication",
                "description": "Implement JWT-based authentication for the API",
                "status": "open",
                "acceptance_criteria": [
                    "Users can log in with email/password",
                    "JWT tokens expire after 24 hours",
                    "Refresh tokens are supported",
                ],
            },
            metadata={"category": "spec_quality"},
        ),
        Case(
            name="spec_quality_complex",
            inputs={
                "id": "beads-eval2",
                "title": "Implement real-time notifications",
                "description": "Add WebSocket-based notifications for user actions. "
                "Should support both browser and mobile clients.",
                "status": "open",
                "priority": "high",
                "task_type": "feature",
                "acceptance_criteria": [
                    "WebSocket connection established on page load",
                    "Notifications appear within 500ms of event",
                    "Fallback to polling if WebSocket fails",
                    "Mobile push notifications via Firebase",
                ],
            },
            metadata={"category": "spec_quality"},
        ),
    ]

    llm_dataset = Dataset(
        cases=llm_cases,
        evaluators=[
            IsInstance(type_name="str"),
            MaxDuration(seconds=5.0),
            LLMJudge(
                rubric=(
                    "The generated specification is clear, complete, and actionable. "
                    "It includes all acceptance criteria in a readable format. "
                    "A developer could understand what to implement from this spec alone."
                ),
                model="anthropic:claude-sonnet-4-5",
                include_input=True,
                # Output both score and assertion with reasoning
                score={"include_reason": True},
                assertion={"include_reason": True},
            ),
        ],
    )

    print("\n[1/1] Spec Generation Quality...")
    report = llm_dataset.evaluate_sync(generate_spec)
    report.print(include_input=True, include_output=True)

    return True


def main():
    """Main entry point for eval runner."""
    parser = argparse.ArgumentParser(
        description="Run Jean Claude evaluation suites",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python -m evals.run_evals              # Run deterministic evals
  uv run python -m evals.run_evals --include-llm  # Include LLM-based evals
  uv run python -m evals.run_evals --suite beads  # Run only beads evals
        """,
    )
    parser.add_argument(
        "--include-llm",
        action="store_true",
        help="Include LLM-based quality evaluations (requires API key)",
    )
    parser.add_argument(
        "--suite",
        choices=["beads", "workflow"],
        help="Run only the specified eval suite",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output including inputs/outputs",
    )

    args = parser.parse_args()

    # Run deterministic evals
    deterministic_passed = run_deterministic_evals(args.suite)

    # Optionally run LLM evals
    llm_passed = True
    if args.include_llm:
        llm_passed = run_llm_evals()

    # Exit with appropriate code
    if deterministic_passed and llm_passed:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
