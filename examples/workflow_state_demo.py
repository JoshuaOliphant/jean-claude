#!/usr/bin/env python3
# ABOUTME: Demonstration script for enhanced workflow state with feature-based progress tracking
# ABOUTME: Shows how to use WorkflowState for tracking multi-feature workflows

"""Demo script showing workflow state usage."""

from pathlib import Path
from tempfile import TemporaryDirectory

from jean_claude.core.state import WorkflowState


def main():
    """Demonstrate workflow state with feature-based progress tracking."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create a new workflow
        print("=== Creating Workflow ===")
        workflow = WorkflowState(
            workflow_id="demo-workflow-123",
            workflow_name="User Authentication System",
            workflow_type="feature",
        )

        # Add features to implement
        print("\n=== Adding Features ===")
        workflow.add_feature(
            "User model",
            "Create SQLAlchemy User model with email and password",
            test_file="tests/test_models.py",
        )
        workflow.add_feature(
            "Password hashing",
            "Implement bcrypt password hashing utilities",
            test_file="tests/test_auth_utils.py",
        )
        workflow.add_feature(
            "Login endpoint",
            "Create POST /api/login endpoint with JWT token generation",
            test_file="tests/test_auth_api.py",
        )
        workflow.add_feature(
            "Registration endpoint",
            "Create POST /api/register endpoint with validation",
            test_file="tests/test_auth_api.py",
        )

        print(f"Added {len(workflow.features)} features")
        print(f"Progress: {workflow.progress_percentage:.1f}%")

        # Save initial state
        workflow.save(project_root)
        print(f"\n✓ Saved state to {project_root / 'agents' / workflow.workflow_id / 'state.json'}")

        # Simulate working through features
        print("\n=== Working Through Features ===")
        for i in range(len(workflow.features)):
            current = workflow.current_feature
            if current:
                print(f"\nFeature {i+1}/{len(workflow.features)}: {current.name}")
                print(f"  Description: {current.description}")
                print(f"  Test file: {current.test_file}")

                # Start the feature
                workflow.start_feature()
                print(f"  Status: {current.status}")

                # Simulate implementation and testing
                workflow.iteration_count += 1
                current.tests_passing = True

                # Mark complete
                workflow.mark_feature_complete()
                print("  ✓ Completed!")
                print(f"  Overall progress: {workflow.progress_percentage:.1f}%")

                # Save after each feature
                workflow.save(project_root)

        # Final summary
        print("\n=== Workflow Complete ===")
        summary = workflow.get_summary()
        print(f"Workflow ID: {summary['workflow_id']}")
        print(f"Type: {summary['workflow_type']}")
        print(f"Total features: {summary['total_features']}")
        print(f"Completed: {summary['completed_features']}")
        print(f"Failed: {summary['failed_features']}")
        print(f"Progress: {summary['progress_percentage']:.1f}%")
        print(f"Complete: {summary['is_complete']}")
        print(f"Iterations: {summary['iteration_count']}")

        # Load and verify
        print("\n=== Loading from Disk ===")
        loaded = WorkflowState.load(workflow.workflow_id, project_root)
        print(f"Loaded workflow: {loaded.workflow_name}")
        print(f"Features loaded: {len(loaded.features)}")
        print(f"All tests passing: {all(f.tests_passing for f in loaded.features)}")
        print(f"All completed: {loaded.is_complete()}")


if __name__ == "__main__":
    main()
