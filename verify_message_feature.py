#!/usr/bin/env python
"""Verification script to ensure Message model feature is complete."""

import sys
from datetime import datetime

print("="*60)
print("VERIFYING MESSAGE MODEL FEATURE")
print("="*60)

# Test 1: Import the module
print("\n[1/6] Testing module imports...")
try:
    from jean_claude.core.message import Message, MessagePriority
    from jean_claude.core import Message as Message2, MessagePriority as MessagePriority2
    print("✓ Direct import works")
    print("✓ Import from core package works")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Verify MessagePriority enum
print("\n[2/6] Testing MessagePriority enum...")
try:
    assert hasattr(MessagePriority, 'URGENT')
    assert hasattr(MessagePriority, 'NORMAL')
    assert hasattr(MessagePriority, 'LOW')
    assert MessagePriority.URGENT.value == 'urgent'
    assert MessagePriority.NORMAL.value == 'normal'
    assert MessagePriority.LOW.value == 'low'
    print("✓ MessagePriority enum has all required values")
except AssertionError as e:
    print(f"✗ Enum validation failed: {e}")
    sys.exit(1)

# Test 3: Create message with all fields
print("\n[3/6] Testing Message creation with all fields...")
try:
    msg = Message(
        id="test-msg-001",
        from_agent="coordinator",
        to_agent="worker-1",
        type="help_request",
        subject="Need help with task",
        body="I need assistance understanding this requirement",
        priority=MessagePriority.URGENT,
        created_at=datetime(2025, 12, 26, 12, 0, 0),
        awaiting_response=True
    )

    assert msg.id == "test-msg-001"
    assert msg.from_agent == "coordinator"
    assert msg.to_agent == "worker-1"
    assert msg.type == "help_request"
    assert msg.subject == "Need help with task"
    assert msg.body == "I need assistance understanding this requirement"
    assert msg.priority == MessagePriority.URGENT
    assert msg.awaiting_response is True

    print("✓ Message creation with all fields works")
    print(f"  ID: {msg.id}")
    print(f"  From: {msg.from_agent} → To: {msg.to_agent}")
    print(f"  Priority: {msg.priority.value}")
    print(f"  Awaiting response: {msg.awaiting_response}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 4: Create message with defaults
print("\n[4/6] Testing Message creation with defaults...")
try:
    msg = Message(
        from_agent="agent-1",
        to_agent="agent-2",
        type="notification",
        subject="Status update",
        body="Task completed successfully"
    )

    # Check required fields
    assert msg.from_agent == "agent-1"
    assert msg.to_agent == "agent-2"

    # Check defaults
    assert msg.id is not None
    assert len(msg.id) > 0
    assert msg.priority == MessagePriority.NORMAL
    assert msg.awaiting_response is False
    assert msg.created_at is not None
    assert isinstance(msg.created_at, datetime)

    print("✓ Message creation with defaults works")
    print(f"  Auto-generated ID: {msg.id}")
    print(f"  Default priority: {msg.priority.value}")
    print(f"  Default awaiting_response: {msg.awaiting_response}")
    print(f"  Auto-generated created_at: {msg.created_at}")
except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

# Test 5: Validate required fields
print("\n[5/6] Testing required field validation...")
try:
    # Test empty from_agent
    try:
        msg = Message(
            from_agent="",
            to_agent="agent-2",
            type="test",
            subject="Test",
            body="Test"
        )
        print("✗ Should have raised validation error for empty from_agent")
        sys.exit(1)
    except Exception as e:
        if "from_agent cannot be empty" in str(e):
            print("✓ Validation for empty from_agent works")
        else:
            print(f"✗ Wrong error message: {e}")
            sys.exit(1)

    # Test empty subject
    try:
        msg = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="",
            body="Test"
        )
        print("✗ Should have raised validation error for empty subject")
        sys.exit(1)
    except Exception as e:
        if "subject cannot be empty" in str(e):
            print("✓ Validation for empty subject works")
        else:
            print(f"✗ Wrong error message: {e}")
            sys.exit(1)

    # Test empty body
    try:
        msg = Message(
            from_agent="agent-1",
            to_agent="agent-2",
            type="test",
            subject="Test",
            body=""
        )
        print("✗ Should have raised validation error for empty body")
        sys.exit(1)
    except Exception as e:
        if "body cannot be empty" in str(e):
            print("✓ Validation for empty body works")
        else:
            print(f"✗ Wrong error message: {e}")
            sys.exit(1)

except Exception as e:
    print(f"✗ Validation test failed unexpectedly: {e}")
    sys.exit(1)

# Test 6: JSON serialization roundtrip
print("\n[6/6] Testing JSON serialization roundtrip...")
try:
    original = Message(
        from_agent="sender",
        to_agent="receiver",
        type="notification",
        subject="Important message",
        body="This is an important notification",
        priority=MessagePriority.URGENT,
        awaiting_response=True
    )

    # Serialize
    json_str = original.model_dump_json()

    # Deserialize
    parsed = Message.model_validate_json(json_str)

    # Verify
    assert parsed.from_agent == original.from_agent
    assert parsed.to_agent == original.to_agent
    assert parsed.type == original.type
    assert parsed.subject == original.subject
    assert parsed.body == original.body
    assert parsed.priority == original.priority
    assert parsed.awaiting_response == original.awaiting_response

    print("✓ JSON serialization roundtrip works")
    print(f"  Original ID: {original.id}")
    print(f"  Parsed ID: {parsed.id}")
    print(f"  Priority preserved: {parsed.priority.value}")

except Exception as e:
    print(f"✗ Failed: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL VERIFICATION TESTS PASSED ✓")
print("="*60)
print("\nMessage model feature is complete and ready for use!")
print("\nFeature includes:")
print("  • Message Pydantic model with all required fields")
print("  • MessagePriority enum (urgent/normal/low)")
print("  • Auto-generation of id and created_at")
print("  • Field validation for required strings")
print("  • JSON serialization/deserialization support")
print("  • Default values for priority and awaiting_response")
