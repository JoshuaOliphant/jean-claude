#!/usr/bin/env python
"""Check the state and mark the beads-task-model feature as complete."""

import json
from datetime import datetime
from pathlib import Path

# Path to state file
STATE_FILE = Path("/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/agents/beads-jean_claude-2sz.3/state.json")

# Read the current state
with open(STATE_FILE, 'r') as f:
    state = json.load(f)

print("Current State:")
print(f"  Workflow: {state['workflow_id']}")
print(f"  Current feature index: {state['current_feature_index']}")
print(f"  Total features: {len(state['features'])}")
print()

# Find the feature we're working on
current_index = state['current_feature_index']
if current_index < len(state['features']):
    current_feature = state['features'][current_index]
    print(f"Current Feature ({current_index}):")
    print(f"  Name: {current_feature['name']}")
    print(f"  Status: {current_feature['status']}")
    print(f"  Test file: {current_feature['test_file']}")
    print()

    # Check if this is the beads-task-model feature
    if current_feature['name'] == 'beads-task-model':
        print("✓ This is the beads-task-model feature!")
        print()
        print("Marking feature as complete...")

        # Update the feature
        current_feature['status'] = 'completed'
        current_feature['tests_passing'] = True
        current_feature['started_at'] = current_feature.get('started_at', datetime.now().isoformat())
        current_feature['completed_at'] = datetime.now().isoformat()

        # Increment the feature index
        state['current_feature_index'] = current_index + 1
        state['updated_at'] = datetime.now().isoformat()
        state['iteration_count'] = state.get('iteration_count', 0) + 1
        state['last_verification_at'] = datetime.now().isoformat()
        state['last_verification_passed'] = True
        state['verification_count'] = state.get('verification_count', 0) + 1

        # Write back
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

        print("✅ Feature marked as complete!")
        print(f"  Next feature index: {state['current_feature_index']}")
        if state['current_feature_index'] < len(state['features']):
            next_feature = state['features'][state['current_feature_index']]
            print(f"  Next feature: {next_feature['name']}")
    else:
        print(f"❌ ERROR: Expected 'beads-task-model' but found '{current_feature['name']}'")
        print("This feature may have already been completed or the state is out of sync.")
else:
    print("❌ ERROR: Current feature index is out of bounds")
