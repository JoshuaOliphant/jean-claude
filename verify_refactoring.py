#!/usr/bin/env python3
"""Quick verification script for message_reader refactoring."""

import sys
import json
from pathlib import Path
from datetime import datetime
import tempfile

from src.jean_claude.core.message_reader import read_messages
from src.jean_claude.core.message_writer import MessageBox
from src.jean_claude.core.mailbox_paths import MailboxPaths

def verify_refactoring():
    """Verify the refactored message_reader works correctly."""

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Test 1: Basic functionality
        print("Test 1: Basic functionality...")
        paths = MailboxPaths(workflow_id="test-workflow", base_dir=tmp_path)
        paths.inbox_path.parent.mkdir(parents=True, exist_ok=True)

        message_data = {
            "id": "msg-1",
            "from_agent": "agent-a",
            "to_agent": "agent-b",
            "type": "request",
            "subject": "Test message",
            "body": "This is a test",
            "priority": "normal",
            "created_at": datetime.now().isoformat(),
            "awaiting_response": False
        }

        with open(paths.inbox_path, 'w') as f:
            f.write(json.dumps(message_data) + '\n')

        messages = read_messages(MessageBox.INBOX, paths)
        assert len(messages) == 1
        assert messages[0].id == "msg-1"
        print("✓ Basic functionality works")

        # Test 2: Missing file
        print("\nTest 2: Missing file...")
        paths2 = MailboxPaths(workflow_id="test-workflow-2", base_dir=tmp_path)
        messages2 = read_messages(MessageBox.INBOX, paths2)
        assert messages2 == []
        print("✓ Missing file handled correctly")

        # Test 3: Invalid mailbox type
        print("\nTest 3: Invalid mailbox type...")
        try:
            read_messages("invalid", paths)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "mailbox must be a MessageBox enum value" in str(e)
            print("✓ Invalid mailbox type raises ValueError")

        # Test 4: None paths
        print("\nTest 4: None paths...")
        try:
            read_messages(MessageBox.INBOX, None)
            assert False, "Should have raised TypeError"
        except TypeError as e:
            assert "paths cannot be None" in str(e)
            print("✓ None paths raises TypeError")

        # Test 5: Verify resolve_mailbox_path is used
        print("\nTest 5: Verify resolve_mailbox_path is used...")
        from src.jean_claude.core import message_reader
        import inspect
        source = inspect.getsource(message_reader.read_messages)
        assert "resolve_mailbox_path" in source
        assert "resolve_mailbox_path(mailbox, paths)" in source
        print("✓ resolve_mailbox_path is being used")

        print("\n" + "="*50)
        print("All verification tests passed! ✓")
        print("="*50)
        return True

if __name__ == "__main__":
    try:
        verify_refactoring()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
