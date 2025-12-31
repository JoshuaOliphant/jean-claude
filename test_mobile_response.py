#!/usr/bin/env python3
"""Test mobile response flow via ntfy.sh.

This script tests the complete mobile coordinator pattern:
1. Simulates an escalation being sent to your phone
2. You respond via ntfy app
3. Jean Claude polls response topic
4. Response is written to OUTBOX
5. Agent receives the response

SETUP:
1. Set JEAN_CLAUDE_NTFY_TOPIC (escalation topic)
2. Set JEAN_CLAUDE_NTFY_RESPONSE_TOPIC (response topic)
3. Subscribe to both topics in ntfy app
4. Run this test
5. Send a test message from your phone to the response topic
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.tools.mailbox_tools import (
    escalate_to_human,
    poll_ntfy_responses,
    process_ntfy_responses,
)
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_reader import read_messages
from jean_claude.core.message_writer import MessageBox

def main():
    print("=" * 70)
    print("MOBILE RESPONSE FLOW TEST")
    print("=" * 70)
    print()

    # Check environment variables
    escalation_topic = os.environ.get("JEAN_CLAUDE_NTFY_TOPIC")
    response_topic = os.environ.get("JEAN_CLAUDE_NTFY_RESPONSE_TOPIC")

    if not escalation_topic:
        print("❌ ERROR: JEAN_CLAUDE_NTFY_TOPIC not set!")
        print()
        print("Set it with:")
        print('  export JEAN_CLAUDE_NTFY_TOPIC="your-escalation-topic"')
        return

    if not response_topic:
        print("❌ ERROR: JEAN_CLAUDE_NTFY_RESPONSE_TOPIC not set!")
        print()
        print("Set it with:")
        print('  export JEAN_CLAUDE_NTFY_RESPONSE_TOPIC="your-response-topic"')
        return

    print(f"✅ Escalation topic: {escalation_topic}")
    print(f"✅ Response topic: {response_topic}")
    print()

    # Step 1: Send test escalation
    print("=" * 70)
    print("STEP 1: SENDING TEST ESCALATION TO YOUR PHONE")
    print("=" * 70)
    print()

    workflow_id = "mobile-response-test"

    escalate_to_human(
        title="Test: Mobile Response Flow",
        message=f"Workflow: {workflow_id}\n\nQuestion: Should we use Redis or in-memory caching?\n\nTo respond from your phone:\n1. Open ntfy app\n2. Go to topic: {response_topic}\n3. Send message in format:\n   {workflow_id}: Your response here\n\nExample:\n{workflow_id}: Use Redis",
        priority=5,
        tags=["robot", "warning", "test"]
    )

    print(f"✅ Escalation sent to topic: {escalation_topic}")
    print(f"📱 Check your phone for the notification!")
    print()

    # Step 2: Wait for user to respond
    print("=" * 70)
    print("STEP 2: WAITING FOR YOUR RESPONSE")
    print("=" * 70)
    print()
    print(f"Please respond from your phone to topic: {response_topic}")
    print()
    print("Message format:")
    print(f"  {workflow_id}: Your answer here")
    print()
    input("Press Enter after you've sent the message from your phone...")
    print()

    # Step 3: Poll for response
    print("=" * 70)
    print("STEP 3: POLLING RESPONSE TOPIC")
    print("=" * 70)
    print()

    responses = poll_ntfy_responses()

    if not responses:
        print("❌ No responses found in topic")
        print()
        print("Troubleshooting:")
        print(f"1. Did you send to the correct topic? ({response_topic})")
        print(f"2. Did you use the correct format? ({workflow_id}: your response)")
        print("3. Try sending another message and run this test again")
        return

    print(f"✅ Found {len(responses)} response(s)")
    print()

    for i, resp in enumerate(responses, 1):
        print(f"Response {i}:")
        print(f"  Workflow ID: {resp['workflow_id']}")
        print(f"  Response: {resp['response']}")
        print(f"  Timestamp: {resp['timestamp']}")
        print()

    # Step 4: Process responses
    print("=" * 70)
    print("STEP 4: PROCESSING RESPONSES")
    print("=" * 70)
    print()

    project_root = Path.cwd()
    count = process_ntfy_responses(project_root)

    print(f"✅ Processed {count} response(s)")
    print()

    # Step 5: Verify OUTBOX
    print("=" * 70)
    print("STEP 5: VERIFYING OUTBOX")
    print("=" * 70)
    print()

    mailbox_paths = MailboxPaths(
        workflow_id=workflow_id,
        base_dir=project_root / "agents"
    )

    # Check if OUTBOX has the response
    outbox_messages = read_messages(MessageBox.OUTBOX, mailbox_paths)

    if not outbox_messages:
        print("❌ No messages found in OUTBOX")
        print(f"Expected location: {mailbox_paths.outbox_path}")
        return

    print(f"✅ Found {len(outbox_messages)} message(s) in OUTBOX")
    print()

    for i, msg in enumerate(outbox_messages, 1):
        print(f"Message {i}:")
        print(f"  From: {msg.from_agent}")
        print(f"  To: {msg.to_agent}")
        print(f"  Type: {msg.type}")
        print(f"  Subject: {msg.subject}")
        print(f"  Body: {msg.body}")
        print()

    # Success summary
    print("=" * 70)
    print("✅ MOBILE RESPONSE FLOW TEST: SUCCESS!")
    print("=" * 70)
    print()
    print("What worked:")
    print("  1. ✅ Escalation sent to your phone via ntfy")
    print("  2. ✅ You responded from phone to response topic")
    print("  3. ✅ Jean Claude polled and found your response")
    print("  4. ✅ Response written to OUTBOX")
    print("  5. ✅ Agent can now receive and continue!")
    print()
    print("🎉 You can now respond to Jean Claude from anywhere in the world!")
    print()

if __name__ == "__main__":
    main()
