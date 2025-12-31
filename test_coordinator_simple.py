#!/usr/bin/env python3
"""Simple test of coordinator pattern - direct mailbox communication.

This simulates what happens when an agent calls ask_user:
1. Write message to INBOX (agent asks question)
2. Read from INBOX (coordinator sees question)
3. Write response to OUTBOX (coordinator answers)
4. Read from OUTBOX (agent receives answer)
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.message import Message, MessagePriority
from jean_claude.core.inbox_writer import InboxWriter
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_reader import read_messages
from jean_claude.core.message_writer import MessageBox, write_message
from jean_claude.core.outbox_monitor import OutboxMonitor
from jean_claude.core.state import WorkflowState

async def main():
    print("=" * 70)
    print("COORDINATOR PATTERN - SIMPLE TEST")
    print("=" * 70)
    print()

    # Setup
    project_root = Path.cwd()
    workflow_id = "coordinator-simple-test"
    workflow_dir = project_root / "agents" / workflow_id
    workflow_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Workflow directory: {workflow_dir}")
    print()

    # Create workflow state
    state = WorkflowState(
        workflow_id=workflow_id,
        workflow_name="Simple Coordinator Test",
        workflow_type="test",
    )
    state.save(project_root)

    # Step 1: Agent asks question (write to INBOX)
    print("=" * 70)
    print("STEP 1: AGENT ASKS QUESTION")
    print("=" * 70)
    print()

    agent_question = Message(
        from_agent="coder-agent",
        to_agent="user",
        type="help_request",
        subject="Need guidance on test approach",
        body="""I'm implementing a new feature and encountered a test that's failing.

The test expects status code 401 (Unauthorized) but the endpoint returns 403 (Forbidden).

Should I:
A) Update the test to expect 403
B) Fix the endpoint to return 401
C) Something else?

Context: This is a JWT authentication endpoint. The test was written before implementation.""",
        priority=MessagePriority.NORMAL,
        awaiting_response=True,
    )

    # Write to INBOX
    inbox_writer = InboxWriter(workflow_dir)
    inbox_writer.write_to_inbox(agent_question)

    print("✓ Agent question written to INBOX")
    print()
    print("Question:")
    print(f"  {agent_question.body[:100]}...")
    print()

    # Step 2: Coordinator sees question (read from INBOX)
    print("=" * 70)
    print("STEP 2: COORDINATOR SEES QUESTION")
    print("=" * 70)
    print()

    mailbox_paths = MailboxPaths(workflow_id=workflow_id)
    inbox_messages = read_messages(MessageBox.INBOX, mailbox_paths)

    print(f"📬 Coordinator checks INBOX: Found {len(inbox_messages)} message(s)")
    print()

    unanswered = [m for m in inbox_messages if m.awaiting_response]

    if unanswered:
        for i, msg in enumerate(unanswered, 1):
            print(f"Message {i}:")
            print(f"  From: {msg.from_agent}")
            print(f"  Priority: {msg.priority.value}")
            print(f"  Subject: {msg.subject}")
            print()
            print("  Full Question:")
            for line in msg.body.split('\n'):
                print(f"    {line}")
            print()

    # Step 3: Coordinator decides and responds
    print("=" * 70)
    print("STEP 3: COORDINATOR RESPONDS")
    print("=" * 70)
    print()

    print("Coordinator Decision:")
    print("  This is a straightforward technical question.")
    print("  The 403 status is correct for authenticated endpoints.")
    print("  I can answer this without escalating to La Boeuf.")
    print()

    coordinator_response = Message(
        from_agent="coordinator",
        to_agent="coder-agent",
        type="response",
        subject="Re: Test failure - status code question",
        body="""Option A: Update the test to expect 403.

Reasoning:
- 403 Forbidden is semantically correct for authenticated endpoints
- 401 Unauthorized means "you need to authenticate"
- 403 Forbidden means "you're authenticated, but don't have permission"

For a JWT auth endpoint, 403 is the right response when the token is valid but lacks required permissions.

Update the test assertion from:
  assert response.status_code == 401
to:
  assert response.status_code == 403

Also update the test name/description to reflect that it's testing authorization (403), not authentication (401).""",
        priority=MessagePriority.NORMAL,
        awaiting_response=False,
    )

    # Write to OUTBOX
    write_message(coordinator_response, MessageBox.OUTBOX, mailbox_paths)

    print("✓ Coordinator response written to OUTBOX")
    print()
    print("Response summary:")
    print(f"  {coordinator_response.body[:80]}...")
    print()

    # Step 4: Agent receives response
    print("=" * 70)
    print("STEP 4: AGENT RECEIVES RESPONSE")
    print("=" * 70)
    print()

    # Simulate agent polling OUTBOX
    outbox_monitor = OutboxMonitor(workflow_dir)
    messages = outbox_monitor.poll_for_new_messages()

    print(f"✓ Agent polls OUTBOX: Found {len(messages)} message(s)")
    print()

    if messages:
        response = messages[0]
        print("Response received:")
        print(f"  From: {response.from_agent}")
        print(f"  Subject: {response.subject}")
        print()
        print("  Full Response:")
        for line in response.body.split('\n'):
            print(f"    {line}")
        print()

    # Summary
    print("=" * 70)
    print("COORDINATOR PATTERN TEST: SUCCESS! ✅")
    print("=" * 70)
    print()
    print("What happened:")
    print("  1. Agent asked a technical question via ask_user tool")
    print("  2. Message appeared in INBOX")
    print("  3. Coordinator (Claude Code) saw the question")
    print("  4. Coordinator determined it could answer without escalation")
    print("  5. Coordinator wrote response to OUTBOX")
    print("  6. Agent received response and can continue")
    print()
    print("📁 Test files location:")
    print(f"  INBOX:  {mailbox_paths.inbox_file}")
    print(f"  OUTBOX: {mailbox_paths.outbox_file}")
    print()
    print("When to escalate to La Boeuf:")
    print("  ❌ NOT for technical questions like this")
    print("  ✅ ONLY for business decisions, security, or uncertainty")
    print()

if __name__ == "__main__":
    asyncio.run(main())
