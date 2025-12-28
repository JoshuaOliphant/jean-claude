#!/usr/bin/env python
"""Inline test for Message model to verify it works."""

from datetime import datetime
from jean_claude.core.message import Message, MessagePriority

print("Testing Message model...")

# Test 1: Create message with all fields
print("\n1. Testing message creation with all fields...")
try:
    msg = Message(
        id="msg-123",
        from_agent="coordinator",
        to_agent="worker-1",
        type="help_request",
        subject="Need help",
        body="Help me",
        priority=MessagePriority.URGENT,
        created_at=datetime(2025, 12, 26, 12, 0, 0),
        awaiting_response=True
    )
    assert msg.id == "msg-123"
    assert msg.from_agent == "coordinator"
    assert msg.to_agent == "worker-1"
    assert msg.priority == MessagePriority.URGENT
    assert msg.awaiting_response is True
    print("✓ Message creation with all fields works")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 2: Create message with minimal fields (defaults)
print("\n2. Testing message creation with minimal fields...")
try:
    msg = Message(
        from_agent="agent-1",
        to_agent="agent-2",
        type="notification",
        subject="Test",
        body="Test body"
    )
    assert msg.id is not None
    assert msg.priority == MessagePriority.NORMAL
    assert msg.awaiting_response is False
    assert msg.created_at is not None
    print("✓ Message creation with minimal fields works")
    print(f"  Auto-generated ID: {msg.id}")
    print(f"  Default priority: {msg.priority}")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 3: Test priority enum
print("\n3. Testing priority enum values...")
try:
    assert MessagePriority.URGENT.value == "urgent"
    assert MessagePriority.NORMAL.value == "normal"
    assert MessagePriority.LOW.value == "low"
    print("✓ Priority enum values correct")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 4: Test string priority conversion
print("\n4. Testing string priority conversion...")
try:
    msg = Message(
        from_agent="a1",
        to_agent="a2",
        type="test",
        subject="S",
        body="B",
        priority="urgent"
    )
    assert msg.priority == MessagePriority.URGENT
    print("✓ String priority conversion works")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 5: Test validation (empty field)
print("\n5. Testing validation for empty fields...")
try:
    msg = Message(
        from_agent="",
        to_agent="a2",
        type="test",
        subject="S",
        body="B"
    )
    print("✗ Failed: Should have raised validation error for empty from_agent")
    exit(1)
except Exception as e:
    if "from_agent cannot be empty" in str(e):
        print("✓ Validation for empty fields works")
    else:
        print(f"✗ Wrong error: {e}")
        exit(1)

# Test 6: Test JSON serialization
print("\n6. Testing JSON serialization...")
try:
    msg = Message(
        id="msg-456",
        from_agent="a1",
        to_agent="a2",
        type="test",
        subject="Test",
        body="Test body",
        priority=MessagePriority.LOW,
        awaiting_response=True
    )
    json_str = msg.model_dump_json()
    assert '"id":"msg-456"' in json_str or '"id": "msg-456"' in json_str
    assert '"priority":"low"' in json_str or '"priority": "low"' in json_str
    assert '"awaiting_response":true' in json_str or '"awaiting_response": true' in json_str
    print("✓ JSON serialization works")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

# Test 7: Test JSON roundtrip
print("\n7. Testing JSON roundtrip...")
try:
    original = Message(
        from_agent="sender",
        to_agent="receiver",
        type="notification",
        subject="Important",
        body="This is important",
        priority=MessagePriority.URGENT
    )
    json_str = original.model_dump_json()
    parsed = Message.model_validate_json(json_str)
    assert parsed.from_agent == original.from_agent
    assert parsed.to_agent == original.to_agent
    assert parsed.subject == original.subject
    assert parsed.body == original.body
    assert parsed.priority == original.priority
    print("✓ JSON roundtrip works")
except Exception as e:
    print(f"✗ Failed: {e}")
    exit(1)

print("\n" + "="*50)
print("All tests passed! ✓")
print("="*50)
