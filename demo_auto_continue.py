#!/usr/bin/env python3
"""Demo script showing auto-continue workflow in action.

This demonstrates the auto-continue pattern with mock features that
immediately succeed, showing the full workflow lifecycle.

Run with:
    uv run python demo_auto_continue.py
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from jean_claude.core.agent import ExecutionResult
from jean_claude.orchestration import initialize_workflow, run_auto_continue


async def main():
    """Run a demo auto-continue workflow."""
    print("🚀 Jean Claude Auto-Continue Demo\n")

    # Setup
    project_root = Path.cwd()

    # Define features for the demo
    features = [
        (
            "Add User Authentication",
            "Implement JWT-based authentication with login/logout endpoints",
            "tests/test_auth.py",
        ),
        (
            "Add User Profile Management",
            "Create endpoints for viewing and updating user profiles",
            "tests/test_profile.py",
        ),
        (
            "Add Email Notifications",
            "Implement email service for password resets and welcome emails",
            "tests/test_email.py",
        ),
        (
            "Add Rate Limiting",
            "Protect API endpoints with rate limiting middleware",
            "tests/test_rate_limit.py",
        ),
    ]

    # Initialize workflow
    print("📝 Initializing workflow with 4 features...")
    state = await initialize_workflow(
        workflow_id="demo-workflow",
        workflow_name="Demo Feature Development",
        workflow_type="feature",
        features=features,
        project_root=project_root,
        max_iterations=10,
    )

    print(f"✓ Created workflow with {len(state.features)} features\n")

    # Mock successful execution for each feature
    feature_index = 0

    async def mock_execute_feature(request, max_retries):
        nonlocal feature_index
        feature = state.features[feature_index]
        print(f"\n⚙️  Executing: {feature.name}")
        print(f"   Description: {feature.description}")

        # Simulate some processing time
        await asyncio.sleep(0.2)

        feature_index += 1

        return ExecutionResult(
            output=f"Successfully implemented {feature.name}",
            success=True,
            session_id=f"demo-session-{feature_index}",
            cost_usd=0.05,
            duration_ms=200,
        )

    # Run the auto-continue workflow
    print("\n🔄 Starting auto-continue loop...\n")

    with patch(
        "jean_claude.orchestration.auto_continue._execute_prompt_sdk_async",
        new=mock_execute_feature,
    ), patch(
        "jean_claude.orchestration.auto_continue.run_verification",
        return_value=MagicMock(
            passed=True, skipped=True, skip_reason="Demo mode - no tests"
        ),
    ):
        final_state = await run_auto_continue(
            state=state,
            project_root=project_root,
            max_iterations=10,
            delay_seconds=0.5,  # Slower delay for demo visibility
            model="sonnet",
        )

    # Show final results
    print("\n" + "=" * 70)
    print("🎉 Workflow Complete!")
    print("=" * 70)

    summary = final_state.get_summary()
    print(f"\n📊 Results:")
    print(f"   • Total Features: {summary['total_features']}")
    print(f"   • Completed: {summary['completed_features']}")
    print(f"   • Failed: {summary['failed_features']}")
    print(f"   • Progress: {summary['progress_percentage']:.1f}%")
    print(f"   • Iterations: {summary['iteration_count']}")
    print(f"   • Total Cost: ${summary['total_cost_usd']:.4f}")
    print(f"   • Duration: {summary['total_duration_ms'] / 1000:.1f}s")

    print(f"\n📁 State saved to: agents/{final_state.workflow_id}/state.json")
    print(f"📝 Outputs saved to: agents/{final_state.workflow_id}/auto_continue/\n")


if __name__ == "__main__":
    asyncio.run(main())
