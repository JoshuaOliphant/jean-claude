# ABOUTME: Mailbox Agent SDK tools for agent-user communication
# ABOUTME: Provides ask_user tool for agents to request help and clarification

"""Mailbox Agent SDK tools for agent-user communication.

This module provides MCP tools that agents can use to communicate with users
through the mailbox system (INBOX/OUTBOX). Agents can request help, ask questions,
and receive guidance when they encounter problems or need clarification.

Tools provided:
- ask_user: Ask the user a question and wait for their response
- notify_user: Send an informational message (no response needed)

Example usage in agent execution:
    from jean_claude.tools.mailbox_tools import jean_claude_mailbox_tools

    result = await execute_agent(
        prompt="Implement feature...",
        options=ClaudeAgentOptions(
            mcp_servers={"mailbox": jean_claude_mailbox_tools},
            allowed_tools=["mcp__jean-claude-mailbox__ask_user"]
        )
    )
"""

import os
import platform
import subprocess
import urllib.request
import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

try:
    from claude_agent_sdk import tool, create_sdk_mcp_server
except ImportError:
    # Fallback for testing without Agent SDK installed
    def tool(name, description, schema):
        def decorator(func):
            func.__tool_name__ = name
            func.__tool_description__ = description
            func.__tool_schema__ = schema
            return func
        return decorator

    def create_sdk_mcp_server(name, version, tools):
        return {"name": name, "version": version, "tools": tools}

from jean_claude.core.inbox_writer import InboxWriter
from jean_claude.core.mailbox_paths import MailboxPaths
from jean_claude.core.message_writer import MessageBox, write_message
from jean_claude.core.outbox_monitor import OutboxMonitor
from jean_claude.core.workflow_pause_handler import WorkflowPauseHandler
from jean_claude.core.message import Message, MessagePriority


# Global state (will be injected by workflow)
_workflow_context = {
    "workflow_dir": None,
    "workflow_state": None,
    "project_root": None
}


def set_workflow_context(workflow_dir: Path, workflow_state: Any, project_root: Path):
    """Set the current workflow context for mailbox tools.

    This must be called before agents can use mailbox tools.

    Args:
        workflow_dir: Path to the workflow directory (e.g., agents/workflow-123)
        workflow_state: Current WorkflowState object
        project_root: Path to the project root directory
    """
    _workflow_context["workflow_dir"] = workflow_dir
    _workflow_context["workflow_state"] = workflow_state
    _workflow_context["project_root"] = project_root


def _send_ntfy_notification(
    title: str,
    message: str,
    priority: int = 3,
    tags: Optional[list[str]] = None,
    debug: bool = False
) -> None:
    """Send push notification via ntfy.sh.

    NOTE: This is for COORDINATOR ESCALATION only, not for agent-initiated notifications.
    The coordinator (main Claude Code instance) should call this when human input is
    truly needed, after triaging agent requests.

    Publishes to ntfy.sh topic configured via JEAN_CLAUDE_NTFY_TOPIC env var.
    Works on any device with ntfy.sh app installed (iOS, Android, Web).

    Args:
        title: Notification title
        message: Notification message body
        priority: Priority level 1-5 (1=min, 3=default, 5=max)
        tags: Optional list of tags (e.g., ["warning", "robot"])
        debug: If True, print debug info (default: False)

    Environment Variables:
        JEAN_CLAUDE_NTFY_TOPIC: Your private ntfy.sh topic name
                                (e.g., "jean-claude-la-boeuf-secret-123")
    """
    try:
        # Get topic from environment variable
        topic = os.environ.get("JEAN_CLAUDE_NTFY_TOPIC")
        if not topic:
            # No topic configured, skip silently
            if debug:
                print(f"[ntfy] No JEAN_CLAUDE_NTFY_TOPIC configured, skipping")
            return

        # Prepare headers
        headers = {
            "Title": title,
            "Priority": str(priority),
        }

        if tags:
            headers["Tags"] = ",".join(tags)

        # Create request
        url = f"https://ntfy.sh/{topic}"
        data = message.encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        if debug:
            print(f"[ntfy] Sending to {url}")
            print(f"[ntfy] Headers: {headers}")
            print(f"[ntfy] Message: {message[:100]}...")

        # Send notification (with timeout)
        with urllib.request.urlopen(req, timeout=5) as response:
            response_data = response.read().decode('utf-8')
            if debug:
                print(f"[ntfy] Response: {response_data}")

    except Exception as e:
        # Silently fail - notifications are nice-to-have, not critical
        if debug:
            print(f"[ntfy] Error: {e}")
        pass


def _send_desktop_notification(title: str, message: str, sound: bool = True) -> None:
    """Send a desktop notification to alert the user (macOS only).

    NOTE: This is for COORDINATOR ESCALATION only, not for agent-initiated notifications.

    Uses osascript to trigger native macOS notifications with sound.
    Silently fails if not on macOS or if notification fails.

    Args:
        title: Notification title
        message: Notification message body
        sound: Whether to play notification sound (default: True)
    """
    try:
        system = platform.system()

        if system == "Darwin":  # macOS
            # Use osascript to trigger macOS notification with sound
            # Sound name can be: "default", "Glass", "Funk", "Blow", etc.
            sound_param = ' sound name "Glass"' if sound else ""
            script = f'display notification "{message}" with title "{title}"{sound_param}'
            subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                timeout=5,
                check=False
            )
        # Non-macOS systems: silently skip
        # Future contributors can add Linux/Windows support

    except Exception:
        # Silently fail - notifications are nice-to-have, not critical
        pass


def escalate_to_human(
    title: str,
    message: str,
    priority: int = 5,
    tags: Optional[list[str]] = None,
    project_name: Optional[str] = None
) -> None:
    """Escalate a message to the human via ntfy.sh and desktop notifications.

    This function should be called by the coordinator (main Claude Code instance)
    when human input is truly needed. It sends both desktop and push notifications.

    Args:
        title: Notification title (no emojis - they break latin-1 encoding)
        message: The message to send to the human
        priority: Priority level 1-5 (default: 5 for max urgency)
        tags: Optional list of emoji shortcodes for ntfy (e.g., ["robot", "warning"])
        project_name: Optional project name to identify which project is asking
                     (auto-detected from current directory if not provided)

    Example:
        >>> escalate_to_human(
        ...     title="Architecture Decision Needed",
        ...     message="Should we use Redis or in-memory cache?",
        ...     project_name="my-api-server"
        ... )
        # Sends notification with title: "[my-api-server] Architecture Decision Needed"
    """
    # Auto-detect project name from current directory if not provided
    if not project_name:
        from pathlib import Path
        project_name = Path.cwd().name

    # Prepend project name to title for multi-project clarity
    full_title = f"[{project_name}] {title}"

    # Send desktop notification (macOS)
    _send_desktop_notification(title=full_title, message=message[:80])

    # Send push notification (ntfy.sh)
    _send_ntfy_notification(
        title=full_title,
        message=message,
        priority=priority,
        tags=tags or ["robot", "warning"],
        debug=False
    )


def poll_ntfy_responses(since_timestamp: Optional[str] = None) -> list[dict[str, str]]:
    """Poll ntfy.sh response topic for human responses.

    This function checks the response topic for messages from the human.
    Messages should be in format: "{workflow_id}: {response_text}"

    Args:
        since_timestamp: Optional timestamp to fetch messages since (RFC3339 format)
                        If None, fetches all recent messages

    Returns:
        List of dicts with keys:
            - workflow_id: The workflow this response is for
            - response: The response text
            - timestamp: When the message was sent

    Environment Variables:
        JEAN_CLAUDE_NTFY_RESPONSE_TOPIC: Your private response topic name

    Example:
        >>> responses = poll_ntfy_responses()
        >>> for resp in responses:
        ...     print(f"Workflow {resp['workflow_id']}: {resp['response']}")
    """
    try:
        # Get response topic from environment
        topic = os.environ.get("JEAN_CLAUDE_NTFY_RESPONSE_TOPIC")
        if not topic:
            # No response topic configured
            return []

        # Build URL for JSON polling
        url = f"https://ntfy.sh/{topic}/json?poll=1"
        if since_timestamp:
            url += f"&since={since_timestamp}"
        else:
            # Get messages from last hour
            url += "&since=1h"

        # Create request
        req = urllib.request.Request(url, method="GET")

        # Fetch messages (with timeout)
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode('utf-8')

        # Parse NDJSON (newline-delimited JSON)
        responses = []
        for line in content.strip().split('\n'):
            if not line:
                continue

            try:
                msg = json.loads(line)
                # Extract message text
                message_text = msg.get('message', '')

                # Parse format: "{workflow_id}: {response}"
                if ':' in message_text:
                    workflow_id, response = message_text.split(':', 1)
                    responses.append({
                        'workflow_id': workflow_id.strip(),
                        'response': response.strip(),
                        'timestamp': msg.get('time', 0)
                    })
            except (json.JSONDecodeError, ValueError):
                # Skip malformed messages
                continue

        return responses

    except Exception:
        # Silently fail - response polling is nice-to-have
        return []


def process_ntfy_responses(project_root: Path) -> int:
    """Poll ntfy response topic and write responses to workflow OUTBOX directories.

    This function:
    1. Polls the JEAN_CLAUDE_NTFY_RESPONSE_TOPIC for new messages
    2. Parses each message to extract workflow_id and response text
    3. Writes response messages to the appropriate workflow's OUTBOX
    4. Returns count of responses processed

    Args:
        project_root: Project root directory containing agents/

    Returns:
        Number of responses processed

    Example:
        >>> count = process_ntfy_responses(Path.cwd())
        >>> print(f"Processed {count} responses from ntfy")
    """
    responses = poll_ntfy_responses()

    if not responses:
        return 0

    processed = 0

    for resp in responses:
        try:
            workflow_id = resp['workflow_id']
            response_text = resp['response']

            # Create response message
            message = Message(
                from_agent="user",
                to_agent="coder-agent",
                type="response",
                subject="Response from mobile",
                body=response_text,
                priority=MessagePriority.NORMAL,
                awaiting_response=False
            )

            # Write to workflow's OUTBOX
            mailbox_paths = MailboxPaths(workflow_id=workflow_id, base_dir=project_root / "agents")
            mailbox_paths.ensure_mailbox_dir()
            write_message(message, MessageBox.OUTBOX, mailbox_paths)

            processed += 1

        except Exception:
            # Skip responses that can't be processed
            continue

    return processed


@tool(
    "ask_user",
    "Ask the user a question and wait for their response. Use this when you need help, clarification, approval, or guidance on how to proceed. The workflow will pause until the user responds.",
    {
        "question": str,
        "context": str,
        "priority": str  # "low", "normal", "urgent"
    }
)
async def ask_user(args: dict[str, Any]) -> dict[str, Any]:
    """Ask the user a question and wait for their response.

    This tool allows agents to request help from the user when they encounter
    problems, need clarification, or require approval. The workflow will pause
    until the user provides a response in the OUTBOX.

    Args:
        args: Dictionary containing:
            - question: The question to ask the user
            - context: Additional context about why you're asking
            - priority: Message priority ("low", "normal", "urgent")

    Returns:
        Dictionary with user's response text in content field

    Example:
        Agent encounters test failure:
        >>> result = await ask_user({
        ...     "question": "Test test_auth fails expecting status 401 but gets 403. Should I update the test or fix the auth code?",
        ...     "context": "Implementing JWT authentication feature. Test was written before implementation.",
        ...     "priority": "normal"
        ... })
        >>> print(result)
        {"content": [{"type": "text", "text": "Update the auth code - 403 is wrong..."}]}
    """
    # Get workflow context
    workflow_dir = _workflow_context.get("workflow_dir")
    workflow_state = _workflow_context.get("workflow_state")
    project_root = _workflow_context.get("project_root")

    if not all([workflow_dir, workflow_state, project_root]):
        return {
            "content": [{
                "type": "text",
                "text": "Error: Mailbox tools not initialized. set_workflow_context() must be called first."
            }]
        }

    try:
        # Parse priority
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "urgent": MessagePriority.URGENT
        }
        priority = priority_map.get(args.get("priority", "normal").lower(), MessagePriority.NORMAL)

        # Build message content
        message_body = f"{args['question']}\n\n**Context**: {args['context']}"

        # Create message directly
        message = Message(
            from_agent="coder-agent",
            to_agent="user",
            type="help_request",
            subject=f"Agent needs help: {args['question'][:50]}...",
            body=message_body,
            priority=priority,
            awaiting_response=True  # Agent is waiting for user response
        )

        # Write to INBOX (coordinator will be notified via monitoring)
        inbox_writer = InboxWriter(workflow_dir)
        inbox_writer.write_to_inbox(message)

        # Pause workflow
        pause_handler = WorkflowPauseHandler(project_root)
        pause_handler.pause_workflow(
            workflow_state,
            reason=f"Agent asked user: {args['question'][:50]}..."
        )

        # Wait for response in OUTBOX
        outbox_monitor = OutboxMonitor(workflow_dir)
        response_message = await outbox_monitor.wait_for_response(timeout_seconds=1800)  # 30 min

        if response_message:
            # Return user's response to agent
            return {
                "content": [{
                    "type": "text",
                    "text": response_message.body
                }]
            }
        else:
            # Timeout - no response received
            return {
                "content": [{
                    "type": "text",
                    "text": "No response received from user within 30 minutes. Please proceed with your best judgment."
                }]
            }

    except Exception as e:
        # Handle errors gracefully
        return {
            "content": [{
                "type": "text",
                "text": f"Error communicating with user: {str(e)}. Please proceed with your best judgment."
            }]
        }


@tool(
    "notify_user",
    "Send an informational message to the user without waiting for a response. Use this to keep the user informed of progress, decisions, or interesting findings.",
    {
        "message": str,
        "priority": str  # "low", "normal", "urgent"
    }
)
async def notify_user(args: dict[str, Any]) -> dict[str, Any]:
    """Send an informational message to the user (no response needed).

    This tool allows agents to keep users informed without pausing the workflow.
    Use this for progress updates, decisions made, or interesting findings.

    Args:
        args: Dictionary containing:
            - message: The informational message
            - priority: Message priority ("low", "normal", "urgent")

    Returns:
        Dictionary with confirmation message

    Example:
        >>> result = await notify_user({
        ...     "message": "Successfully implemented 3 of 5 features. Next: database migration.",
        ...     "priority": "low"
        ... })
        >>> print(result)
        {"content": [{"type": "text", "text": "Message sent to user"}]}
    """
    # Get workflow context
    workflow_dir = _workflow_context.get("workflow_dir")

    if not workflow_dir:
        return {
            "content": [{
                "type": "text",
                "text": "Error: Mailbox tools not initialized."
            }]
        }

    try:
        # Parse priority
        priority_map = {
            "low": MessagePriority.LOW,
            "normal": MessagePriority.NORMAL,
            "urgent": MessagePriority.URGENT
        }
        priority = priority_map.get(args.get("priority", "low").lower(), MessagePriority.LOW)

        # Create message directly (no response needed)
        message = Message(
            from_agent="coder-agent",
            to_agent="user",
            type="notification",
            subject=f"Agent notification: {args['message'][:50]}...",
            body=args["message"],
            priority=priority,
            awaiting_response=False  # FYI only, no response needed
        )

        # Write to INBOX (coordinator will be notified via monitoring)
        inbox_writer = InboxWriter(workflow_dir)
        inbox_writer.write_to_inbox(message)

        return {
            "content": [{
                "type": "text",
                "text": "Message sent to user successfully."
            }]
        }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error sending message: {str(e)}"
            }]
        }


# Create MCP server with mailbox tools
jean_claude_mailbox_tools = create_sdk_mcp_server(
    name="jean-claude-mailbox",
    version="1.0.0",
    tools=[ask_user, notify_user]
)
