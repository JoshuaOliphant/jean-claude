#!/usr/bin/env python3
"""Test the coordinator pattern with a real agent workflow.

This script:
1. Creates a workflow with an intentionally ambiguous task
2. Agent encounters the ambiguity and calls ask_user
3. Message appears in INBOX for coordinator to see
4. Coordinator can respond via OUTBOX
5. Agent receives response and continues
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.agent import PromptRequest, ExecutionResult
from jean_claude.core.sdk_executor import execute_prompt_async
from jean_claude.core.state import WorkflowState
from jean_claude.tools.mailbox_tools import jean_claude_mailbox_tools, set_workflow_context
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_reader import read_messages
from jean_claude.core.message_writer import MessageBox

async def test_coordinator_pattern():
    """Test agent → coordinator → human communication."""

    print("=" * 70)
    print("COORDINATOR PATTERN TEST")
    print("=" * 70)
    print()

    # Setup workflow
    project_root = Path.cwd()
    workflow_id = "coordinator-test-001"
    workflow_dir = project_root / "agents" / workflow_id
    workflow_dir.mkdir(parents=True, exist_ok=True)

    print(f"✓ Created workflow directory: {workflow_dir}")
    print()

    # Create workflow state
    state = WorkflowState(
        workflow_id=workflow_id,
        workflow_name="Coordinator Pattern Test",
        workflow_type="test",
    )
    state.save(project_root)

    print(f"✓ Created workflow state: {workflow_id}")
    print()

    # Set mailbox context
    set_workflow_context(workflow_dir, state, project_root)

    print("✓ Mailbox tools configured")
    print()

    # Create a task that SHOULD trigger ask_user
    prompt = """You are testing the mailbox communication system.

Your task: Implement a simple greeting function.

CRITICAL: Before you write any code, you MUST use the ask_user tool to ask:
"Should the greeting function return 'Hello' or 'Hi'? Please advise on the preferred greeting style."

This is a test of the coordinator pattern, so please call ask_user with:
- question: "Should the greeting function return 'Hello' or 'Hi'?"
- context: "Testing coordinator pattern - need guidance on greeting style"
- priority: "normal"

After you get a response, acknowledge it and create the function based on the answer.
"""

    print("=" * 70)
    print("STARTING AGENT")
    print("=" * 70)
    print()
    print("Task: Create greeting function (will ask for help)")
    print()

    # Run agent in background (it will pause waiting for response)
    request = PromptRequest(
        prompt=prompt,
        model="haiku",  # Fast and cheap for testing
        working_dir=project_root,
        output_dir=workflow_dir / "agent_output",
        dangerously_skip_permissions=True,
        mcp_servers={"jean-claude-mailbox": jean_claude_mailbox_tools},
        allowed_tools=[
            "mcp__jean-claude-mailbox__ask_user",
            "mcp__jean-claude-mailbox__notify_user",
        ],
    )

    # Start agent (this will block when it calls ask_user)
    print("⚙️  Agent starting...")
    print()

    # Run agent with a short timeout since we're manually intervening
    try:
        # This will block when agent calls ask_user and waits
        result = await asyncio.wait_for(
            execute_prompt_async(request, max_retries=1),
            timeout=60.0  # 60 second timeout for agent to ask question
        )

        print()
        print("=" * 70)
        print("AGENT COMPLETED")
        print("=" * 70)
        print()

        if result.success:
            print("✓ Agent completed successfully")
            print()
            print("Output:")
            print(result.output[:500])
        else:
            print("✗ Agent failed:")
            print(result.output[:500])

    except asyncio.TimeoutError:
        print()
        print("=" * 70)
        print("AGENT PAUSED (WAITING FOR COORDINATOR)")
        print("=" * 70)
        print()

        # Check INBOX for messages
        mailbox_paths = MailboxPaths(workflow_id=workflow_id)
        inbox_messages = read_messages(MessageBox.INBOX, mailbox_paths)

        print(f"📬 Found {len(inbox_messages)} message(s) in INBOX")
        print()

        if inbox_messages:
            for i, msg in enumerate(inbox_messages, 1):
                print(f"Message {i}:")
                print(f"  From: {msg.from_agent}")
                print(f"  To: {msg.to_agent}")
                print(f"  Type: {msg.type}")
                print(f"  Priority: {msg.priority}")
                print(f"  Awaiting Response: {msg.awaiting_response}")
                print(f"  Subject: {msg.subject}")
                print()
                print(f"  Question:")
                print(f"  {msg.body}")
                print()
                print("-" * 70)
                print()

            print("✓ COORDINATOR PATTERN WORKING!")
            print()
            print("Next steps to complete the test:")
            print()
            print("1. Coordinator (you) responds by writing to OUTBOX:")
            print()
            print(f"""   echo '{{
     "from_agent": "coordinator",
     "to_agent": "coder-agent",
     "type": "response",
     "subject": "Re: Greeting style",
     "body": "Use 'Hello' - it's more formal and professional.",
     "priority": "NORMAL",
     "awaiting_response": false,
     "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
   }}' | jq '.' > agents/{workflow_id}/OUTBOX/response-$(date +%s).json""")
            print()
            print("2. Agent will receive response and continue")
            print()
            print("3. Workflow completes!")

        else:
            print("❌ No messages in INBOX - agent may not have called ask_user")
            print()
            print("Check agent output:")
            print(f"  cat {workflow_dir}/agent_output/transcript.jsonl | jq")

if __name__ == "__main__":
    print()
    print("🧪 Testing Coordinator Pattern")
    print()
    print("This test will:")
    print("1. Start an agent with an ambiguous task")
    print("2. Agent calls ask_user tool")
    print("3. Message appears in INBOX")
    print("4. Coordinator (you) can respond via OUTBOX")
    print("5. Agent receives response and continues")
    print()
    input("Press Enter to start the test...")
    print()

    asyncio.run(test_coordinator_pattern())
