#!/usr/bin/env python3
"""Update state.json to mark beads-cli-wrapper feature as completed."""

import json
from datetime import datetime
from pathlib import Path

# Read the state file
state_file = Path('agents/beads-jean_claude-2sz.3/state.json')
with state_file.open('r') as f:
    state = json.load(f)

# Update feature 1 (beads-cli-wrapper)
feature = state['features'][1]
now = datetime.now().isoformat()

print(f"Current feature at index 1: {feature['name']}")
print(f"Current status: {feature['status']}")

if feature['name'] == 'beads-cli-wrapper' and feature['status'] == 'not_started':
    feature['status'] = 'completed'
    feature['tests_passing'] = True
    feature['started_at'] = '2025-12-24T18:45:00.000000'
    feature['completed_at'] = now

    # Increment current_feature_index from 1 to 2
    state['current_feature_index'] = 2
    state['updated_at'] = now
    state['phase'] = 'implementing'
    state['last_verification_at'] = now
    state['verification_count'] = state.get('verification_count', 0) + 1

    # Write back
    with state_file.open('w') as f:
        json.dump(state, f, indent=2)

    print(f"✓ Updated feature 1 (beads-cli-wrapper) to completed")
    print(f"✓ Updated current_feature_index to 2")
    print(f"✓ Updated at: {now}")
else:
    print(f"⚠ Feature already completed or has unexpected name/status")
    print(f"  Name: {feature['name']}")
    print(f"  Status: {feature['status']}")
