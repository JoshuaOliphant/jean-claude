#!/usr/bin/env python3
"""Update state.json to mark feature 11 (post-tool-use-hook) as complete."""

import json
from pathlib import Path
from datetime import datetime, timezone

def main():
    """Update the state file."""
    state_path = Path("agents/beads-jean_claude-29n/state.json")

    # Read current state
    with open(state_path, 'r') as f:
        state = json.load(f)

    # Find the post-tool-use-hook feature (index 10)
    feature_index = 10
    feature = state["features"][feature_index]

    # Verify it's the right feature
    assert feature["name"] == "post-tool-use-hook", f"Wrong feature at index {feature_index}"

    # Update the feature
    now = datetime.now(timezone.utc).isoformat()
    feature["status"] = "completed"
    feature["tests_passing"] = True
    if feature["started_at"] is None:
        feature["started_at"] = now
    feature["completed_at"] = now

    # Update workflow metadata
    state["updated_at"] = now
    state["current_feature_index"] = 11  # Move to next feature
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["last_verification_at"] = now
    state["last_verification_passed"] = True
    state["verification_count"] = state.get("verification_count", 0) + 1

    # Write updated state
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)

    print("✅ State file updated successfully!")
    print(f"\nFeature 11 Status:")
    print(f"  Name: {feature['name']}")
    print(f"  Status: {feature['status']}")
    print(f"  Tests Passing: {feature['tests_passing']}")
    print(f"  Started: {feature['started_at']}")
    print(f"  Completed: {feature['completed_at']}")
    print(f"\nCurrent feature index: {state['current_feature_index']}")
    print(f"Iteration count: {state['iteration_count']}")

if __name__ == "__main__":
    main()
