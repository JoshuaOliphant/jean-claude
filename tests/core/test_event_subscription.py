# ABOUTME: Test suite for EventStore subscription system functionality
# ABOUTME: Tests subscribe() method, callback notifications, multiple subscribers, and error handling

"""Test suite for EventStore subscription system functionality.

This module comprehensively tests the EventStore subscription system, including:

- EventStore.subscribe() method for registering callback functions
- Callback notification when events are appended to the store
- Support for multiple subscribers with proper isolation
- Callback error handling without affecting append operations
- Subscription management and cleanup functionality

The tests follow TDD principles and use existing patterns to ensure consistency
with the overall test suite.
"""

import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, call
import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestEventStoreSubscription:
    """Test basic subscription functionality of EventStore.subscribe() method."""

    def test_subscribe_accepts_callback_function(self, tmp_path):
        """Test that subscribe() accepts a callback function and returns subscription ID."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Define a callback function
        def callback(event):
            pass

        # Subscribe should return a subscription ID
        subscription_id = event_store.subscribe(callback)

        assert subscription_id is not None
        assert isinstance(subscription_id, str)
        assert len(subscription_id) > 0

    def test_subscribe_validates_callback_parameter(self, tmp_path):
        """Test that subscribe() validates the callback parameter."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test None callback
        with pytest.raises(ValueError, match="Callback cannot be None"):
            event_store.subscribe(None)

        # Test non-callable callback
        with pytest.raises(ValueError, match="Callback must be callable"):
            event_store.subscribe("not_a_function")

        with pytest.raises(ValueError, match="Callback must be callable"):
            event_store.subscribe(42)

        with pytest.raises(ValueError, match="Callback must be callable"):
            event_store.subscribe({"not": "callable"})

    def test_subscribe_stores_multiple_callbacks(self, tmp_path):
        """Test that subscribe() can store multiple callback functions."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Define multiple callback functions
        def callback1(event):
            pass

        def callback2(event):
            pass

        def callback3(event):
            pass

        # Subscribe multiple callbacks
        sub_id1 = event_store.subscribe(callback1)
        sub_id2 = event_store.subscribe(callback2)
        sub_id3 = event_store.subscribe(callback3)

        # All should return unique subscription IDs
        assert sub_id1 != sub_id2
        assert sub_id2 != sub_id3
        assert sub_id1 != sub_id3

        # All subscription IDs should be valid strings
        assert isinstance(sub_id1, str) and len(sub_id1) > 0
        assert isinstance(sub_id2, str) and len(sub_id2) > 0
        assert isinstance(sub_id3, str) and len(sub_id3) > 0


class TestEventNotificationOnAppend:
    """Test callback notification when events are appended."""

    def test_append_notifies_single_subscriber(self, tmp_path):
        """Test that append() notifies a single subscribed callback."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Track callback calls
        callback_calls = []

        def callback(event):
            callback_calls.append(event)

        # Subscribe to notifications
        event_store.subscribe(callback)

        # Create and append an event
        event = Event(
            workflow_id="notification-test-1",
            event_type="test_event",
            event_data={"test": "data"}
        )

        result = event_store.append(event)
        assert result is True

        # Verify callback was called with the event
        assert len(callback_calls) == 1
        assert callback_calls[0] is event  # Should be the same Event object

    def test_append_notifies_multiple_subscribers(self, tmp_path):
        """Test that append() notifies all subscribed callbacks."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Track callback calls for each subscriber
        callback1_calls = []
        callback2_calls = []
        callback3_calls = []

        def callback1(event):
            callback1_calls.append(event)

        def callback2(event):
            callback2_calls.append(event)

        def callback3(event):
            callback3_calls.append(event)

        # Subscribe multiple callbacks
        event_store.subscribe(callback1)
        event_store.subscribe(callback2)
        event_store.subscribe(callback3)

        # Create and append an event
        event = Event(
            workflow_id="multi-notification-test",
            event_type="multi_subscriber_event",
            event_data={"subscribers": 3}
        )

        result = event_store.append(event)
        assert result is True

        # Verify all callbacks were called
        assert len(callback1_calls) == 1
        assert len(callback2_calls) == 1
        assert len(callback3_calls) == 1

        # Verify all callbacks received the same event
        assert callback1_calls[0] is event
        assert callback2_calls[0] is event
        assert callback3_calls[0] is event

    def test_append_no_callbacks_registered_works_normally(self, tmp_path):
        """Test that append() works normally when no callbacks are registered."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Create and append an event without any subscribers
        event = Event(
            workflow_id="no-callbacks-test",
            event_type="no_subscribers_event",
            event_data={"callbacks": 0}
        )

        result = event_store.append(event)
        assert result is True

        # Verify event was still stored in database
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("no-callbacks-test",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "no-callbacks-test"
            assert row["event_type"] == "no_subscribers_event"

    def test_multiple_appends_notify_subscribers(self, tmp_path):
        """Test that multiple append() calls notify subscribers for each event."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Track callback calls
        callback_calls = []

        def callback(event):
            callback_calls.append((event.workflow_id, event.event_type))

        # Subscribe to notifications
        event_store.subscribe(callback)

        # Create and append multiple events
        event1 = Event(
            workflow_id="multi-append-1",
            event_type="first_event",
            event_data={"sequence": 1}
        )
        event2 = Event(
            workflow_id="multi-append-2",
            event_type="second_event",
            event_data={"sequence": 2}
        )
        event3 = Event(
            workflow_id="multi-append-1",
            event_type="third_event",
            event_data={"sequence": 3}
        )

        # Append all events
        assert event_store.append(event1) is True
        assert event_store.append(event2) is True
        assert event_store.append(event3) is True

        # Verify callback was called for each event
        assert len(callback_calls) == 3
        assert callback_calls[0] == ("multi-append-1", "first_event")
        assert callback_calls[1] == ("multi-append-2", "second_event")
        assert callback_calls[2] == ("multi-append-1", "third_event")


class TestSubscriptionErrorHandling:
    """Test callback error handling in subscription system."""

    def test_callback_error_does_not_prevent_event_storage(self, tmp_path):
        """Test that callback errors don't prevent event from being stored."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        def failing_callback(event):
            raise ValueError("Callback error for testing")

        # Subscribe a callback that will fail
        event_store.subscribe(failing_callback)

        # Create and append an event
        event = Event(
            workflow_id="error-handling-test",
            event_type="callback_error_event",
            event_data={"should": "still_be_stored"}
        )

        # Append should still succeed despite callback error
        result = event_store.append(event)
        assert result is True

        # Verify event was still stored in database
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM events WHERE workflow_id = ?", ("error-handling-test",))
            row = cursor.fetchone()

            assert row is not None
            assert row["workflow_id"] == "error-handling-test"

    def test_callback_error_does_not_affect_other_callbacks(self, tmp_path):
        """Test that one callback error doesn't prevent other callbacks from running."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        successful_calls = []

        def failing_callback(event):
            raise RuntimeError("This callback always fails")

        def successful_callback1(event):
            successful_calls.append(f"callback1-{event.event_type}")

        def successful_callback2(event):
            successful_calls.append(f"callback2-{event.event_type}")

        # Subscribe callbacks in mixed order
        event_store.subscribe(successful_callback1)
        event_store.subscribe(failing_callback)
        event_store.subscribe(successful_callback2)

        # Create and append an event
        event = Event(
            workflow_id="mixed-callbacks-test",
            event_type="mixed_error_event",
            event_data={"test": "error_isolation"}
        )

        result = event_store.append(event)
        assert result is True

        # Verify successful callbacks were called despite the failing one
        assert len(successful_calls) == 2
        assert "callback1-mixed_error_event" in successful_calls
        assert "callback2-mixed_error_event" in successful_calls

    def test_multiple_callback_errors_handled_gracefully(self, tmp_path):
        """Test that multiple callback errors are handled gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        def failing_callback1(event):
            raise ValueError("First callback error")

        def failing_callback2(event):
            raise TypeError("Second callback error")

        successful_calls = []

        def successful_callback(event):
            successful_calls.append(event.event_type)

        # Subscribe multiple failing callbacks and one successful one
        event_store.subscribe(failing_callback1)
        event_store.subscribe(successful_callback)
        event_store.subscribe(failing_callback2)

        # Create and append an event
        event = Event(
            workflow_id="multiple-errors-test",
            event_type="multiple_error_event",
            event_data={"errors": 2, "success": 1}
        )

        result = event_store.append(event)
        assert result is True

        # Verify successful callback ran and event was stored
        assert len(successful_calls) == 1
        assert successful_calls[0] == "multiple_error_event"

        # Verify event was still stored
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM events WHERE workflow_id = ?", ("multiple-errors-test",))
            count = cursor.fetchone()["count"]
            assert count == 1


class TestSubscriptionManagement:
    """Test subscription management and lifecycle functionality."""

    def test_unsubscribe_removes_callback(self, tmp_path):
        """Test that unsubscribe() removes a callback from notifications."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        callback_calls = []

        def callback(event):
            callback_calls.append(event.event_type)

        # Subscribe and get subscription ID
        subscription_id = event_store.subscribe(callback)

        # Append an event - should trigger callback
        event1 = Event(
            workflow_id="unsubscribe-test",
            event_type="before_unsubscribe",
            event_data={"phase": "before"}
        )
        event_store.append(event1)

        assert len(callback_calls) == 1
        assert callback_calls[0] == "before_unsubscribe"

        # Unsubscribe the callback
        result = event_store.unsubscribe(subscription_id)
        assert result is True

        # Append another event - should NOT trigger callback
        event2 = Event(
            workflow_id="unsubscribe-test",
            event_type="after_unsubscribe",
            event_data={"phase": "after"}
        )
        event_store.append(event2)

        # Callback should not have been called again
        assert len(callback_calls) == 1

    def test_unsubscribe_invalid_subscription_id(self, tmp_path):
        """Test that unsubscribe() handles invalid subscription IDs gracefully."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        # Test unsubscribing non-existent subscription
        result = event_store.unsubscribe("non-existent-id")
        assert result is False

        # Test unsubscribing None
        result = event_store.unsubscribe(None)
        assert result is False

        # Test unsubscribing empty string
        result = event_store.unsubscribe("")
        assert result is False

    def test_unsubscribe_does_not_affect_other_subscriptions(self, tmp_path):
        """Test that unsubscribing one callback doesn't affect others."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        callback1_calls = []
        callback2_calls = []
        callback3_calls = []

        def callback1(event):
            callback1_calls.append(event.event_type)

        def callback2(event):
            callback2_calls.append(event.event_type)

        def callback3(event):
            callback3_calls.append(event.event_type)

        # Subscribe all callbacks
        sub_id1 = event_store.subscribe(callback1)
        sub_id2 = event_store.subscribe(callback2)
        sub_id3 = event_store.subscribe(callback3)

        # Append event - all should be notified
        event1 = Event(
            workflow_id="selective-unsubscribe-test",
            event_type="before_selective_unsubscribe",
            event_data={"phase": "before"}
        )
        event_store.append(event1)

        assert len(callback1_calls) == 1
        assert len(callback2_calls) == 1
        assert len(callback3_calls) == 1

        # Unsubscribe only callback2
        result = event_store.unsubscribe(sub_id2)
        assert result is True

        # Append another event - only callback1 and callback3 should be notified
        event2 = Event(
            workflow_id="selective-unsubscribe-test",
            event_type="after_selective_unsubscribe",
            event_data={"phase": "after"}
        )
        event_store.append(event2)

        # Verify only callback1 and callback3 were called again
        assert len(callback1_calls) == 2
        assert len(callback2_calls) == 1  # Should remain 1
        assert len(callback3_calls) == 2


class TestSubscriptionIntegration:
    """Test integration of subscription system with existing EventStore functionality."""

    def test_subscription_works_with_existing_append_error_handling(self, tmp_path):
        """Test that subscriptions work properly when append() fails."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        callback_calls = []

        def callback(event):
            callback_calls.append(event)

        # Subscribe to notifications
        event_store.subscribe(callback)

        # Try to append invalid event (None) - should fail
        result = event_store.append(None)
        assert result is False

        # Callback should not have been called for failed append
        assert len(callback_calls) == 0

        # Append valid event - should succeed and trigger callback
        valid_event = Event(
            workflow_id="integration-test",
            event_type="valid_event",
            event_data={"valid": True}
        )

        result = event_store.append(valid_event)
        assert result is True

        # Callback should have been called for successful append
        assert len(callback_calls) == 1
        assert callback_calls[0] is valid_event

    def test_subscription_preserves_event_store_transaction_behavior(self, tmp_path):
        """Test that subscription callbacks don't interfere with ACID transactions."""
        db_path = tmp_path / "test_events.db"
        event_store = EventStore(db_path)

        callback_calls = []

        def callback(event):
            callback_calls.append(event)
            # Verify event is already committed to database when callback runs
            # by querying the database within the callback
            with event_store as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM events WHERE workflow_id = ?", (event.workflow_id,))
                count = cursor.fetchone()["count"]
                # The event should already be visible in database when callback runs
                assert count >= 1

        # Subscribe to notifications
        event_store.subscribe(callback)

        # Append event - transaction should complete before callback runs
        event = Event(
            workflow_id="transaction-test",
            event_type="transaction_event",
            event_data={"transaction": "committed"}
        )

        result = event_store.append(event)
        assert result is True
        assert len(callback_calls) == 1

    def test_subscription_system_initializes_properly(self, tmp_path):
        """Test that subscription system initializes properly on EventStore creation."""
        db_path = tmp_path / "test_events.db"

        # Creating EventStore should initialize subscription system
        event_store = EventStore(db_path)

        # Should be able to subscribe immediately
        def callback(event):
            pass

        subscription_id = event_store.subscribe(callback)
        assert subscription_id is not None

        # Should be able to append and trigger notifications
        event = Event(
            workflow_id="initialization-test",
            event_type="init_event",
            event_data={"initialized": True}
        )

        result = event_store.append(event)
        assert result is True