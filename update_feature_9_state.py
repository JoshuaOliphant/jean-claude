#!/usr/bin/env python
"""Update state.json to mark feature 9 (interactive-prompt-handler) as complete."""

import json
from datetime import datetime, timezone

STATE_FILE = "agents/beads-jean_claude-2sz.7/state.json"

# Read current state
with open(STATE_FILE, 'r') as f:
    state = json.load(f)

# Get current timestamp
now = datetime.now(timezone.utc).isoformat()

# Update feature 9 (index 8)
feature = state['features'][8]
feature['status'] = 'completed'
feature['tests_passing'] = True
if feature['started_at'] is None:
    feature['started_at'] = now
feature['completed_at'] = now

# Update state metadata
state['updated_at'] = now
state['current_feature_index'] = 9  # Move to next feature
state['iteration_count'] = state.get('iteration_count', 8) + 1

# Save updated state
with open(STATE_FILE, 'w') as f:
    json.dump(state, f, indent=2)

print(f"✓ Updated state.json")
print(f"  - Feature 'interactive-prompt-handler' marked as completed")
print(f"  - Tests marked as passing")
print(f"  - Completed at: {now}")
print(f"  - Current feature index: {state['current_feature_index']}")
print(f"  - Iteration count: {state['iteration_count']}")
