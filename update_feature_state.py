#!/usr/bin/env python
"""Update state.json to mark feature 0 as complete."""

import json
from datetime import datetime

# Read state file
state_path = '/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/agents/beads-jean_claude-2sz.3/state.json'

with open(state_path, 'r') as f:
    state = json.load(f)

# Update feature 0 (beads-integration-module)
now = datetime.now().isoformat()
state['features'][0]['status'] = 'completed'
state['features'][0]['tests_passing'] = True
state['features'][0]['started_at'] = now
state['features'][0]['completed_at'] = now

# Update state metadata
state['updated_at'] = now
state['current_feature_index'] = 1

# Write updated state
with open(state_path, 'w') as f:
    json.dump(state, f, indent=2)

print('✅ State updated successfully!')
print(f"✅ Feature 0 '{state['features'][0]['name']}' marked as complete")
print(f"✅ Current feature index moved to 1")
print(f"✅ Next feature: {state['features'][1]['name']}")
