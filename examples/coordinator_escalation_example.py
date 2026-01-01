#!/usr/bin/env python3
"""Example of proper coordinator escalation with easy-to-copy response format."""

from jean_claude.tools.mailbox_tools import escalate_to_human, poll_ntfy_responses
import time

# Example workflow details
workflow_id = "feature-auth-system-abc123"
question = "Should I use JWT tokens or session cookies for authentication?"

# ✅ BEST PRACTICE: Include copyable format in escalation message
escalation_message = f"""Workflow: {workflow_id}

Question: {question}

Context:
- Building new authentication system
- Need to choose between JWT (stateless) vs Sessions (stateful)
- Both approaches are valid

---
To respond from your phone:

1. Open ntfy app
2. Tap on response topic
3. Send this message (tap to copy):

{workflow_id}: Use JWT tokens

Replace "Use JWT tokens" with your actual response.
---
"""

# Send escalation (project name auto-detected from current directory)
escalate_to_human(
    title="Coordinator: Architecture Decision Needed",
    message=escalation_message,
    priority=5,
    tags=["robot", "warning", "thinking"]
    # project_name will be auto-detected from Path.cwd().name
    # Or explicitly set: project_name="my-api-server"
)

# Notification will appear as:
# Title: "[jean-claude] Coordinator: Architecture Decision Needed"
# (or whatever your project directory name is)

print("Escalation sent!")
print("Polling for response...")

# Poll with sleep intervals (as documented in CLAUDE.md)
max_attempts = 30  # 5 minutes
response = None

for attempt in range(max_attempts):
    time.sleep(10)

    responses = poll_ntfy_responses()
    matching = [r for r in responses if r['workflow_id'] == workflow_id]

    if matching:
        response = matching[0]['response']
        print(f"✅ Response received: {response}")
        break

    print(f"  Waiting... ({(attempt + 1) * 10}s / {max_attempts * 10}s)")

if not response:
    print("❌ No response after 5 minutes")
