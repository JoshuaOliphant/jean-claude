#!/usr/bin/env python3
"""Verify that message_writer module can be imported."""

try:
    from jean_claude.core.message import Message, MessagePriority
    print("✓ Successfully imported Message and MessagePriority")

    from jean_claude.core.message_writer import write_message, MessageBox
    print("✓ Successfully imported write_message and MessageBox")

    from jean_claude.core.mailbox_paths import MailboxPaths
    print("✓ Successfully imported MailboxPaths")

    # Check that MessageBox enum has the right values
    assert hasattr(MessageBox, 'INBOX'), "MessageBox should have INBOX"
    assert hasattr(MessageBox, 'OUTBOX'), "MessageBox should have OUTBOX"
    print("✓ MessageBox enum has INBOX and OUTBOX")

    # Check that write_message is callable
    assert callable(write_message), "write_message should be callable"
    print("✓ write_message is callable")

    print("\n" + "=" * 80)
    print("✓ All imports successful - message_writer module is ready!")
    print("=" * 80)

except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
