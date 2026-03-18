# ABOUTME: Test suite for EventStore subscription system functionality
# ABOUTME: Tests subscribe() method, callback notifications, multiple subscribers, and error handling

"""Test suite for EventStore subscription system functionality.

Tests subscribe/unsubscribe, callback notifications on append,
callback error isolation, and integration with event store transactions.
"""

import pytest

from jean_claude.core.event_store import EventStore
from jean_claude.core.event_models import Event


class TestEventStoreSubscription:
    """Test subscription registration and validation."""

    def test_subscribe_returns_unique_ids_and_validates(self, tmp_path):
        """Test subscribe returns unique IDs, validates callbacks, and stores multiple."""
        event_store = EventStore(tmp_path / "test.db")

        # Valid callbacks return unique IDs
        sub1 = event_store.subscribe(lambda e: None)
        sub2 = event_store.subscribe(lambda e: None)
        sub3 = event_store.subscribe(lambda e: None)
        assert isinstance(sub1, str) and len(sub1) > 0
        assert sub1 != sub2 != sub3

        # Invalid callbacks rejected
        with pytest.raises(ValueError, match="Callback cannot be None"):
            event_store.subscribe(None)
        for invalid in ["not_a_function", 42, {"not": "callable"}]:
            with pytest.raises(ValueError, match="Callback must be callable"):
                event_store.subscribe(invalid)


class TestEventNotificationOnAppend:
    """Test callback notification when events are appended."""

    def test_append_notifies_subscribers(self, tmp_path):
        """Test single, multiple subscribers are notified; no subscribers works; multiple appends tracked."""
        event_store = EventStore(tmp_path / "test.db")

        # No subscribers - append still works
        event_no_sub = Event(workflow_id="no-sub", event_type="test", event_data={})
        assert event_store.append(event_no_sub) is True

        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("no-sub",))
            assert cursor.fetchone()[0] == 1

        # Multiple subscribers
        calls1, calls2 = [], []
        event_store.subscribe(lambda e: calls1.append(e.event_type))
        event_store.subscribe(lambda e: calls2.append(e.event_type))

        for i, etype in enumerate(["first", "second", "third"]):
            event = Event(workflow_id=f"multi-{i}", event_type=etype, event_data={"seq": i})
            assert event_store.append(event) is True

        assert calls1 == ["first", "second", "third"]
        assert calls2 == ["first", "second", "third"]


class TestSubscriptionErrorHandling:
    """Test callback error handling in subscription system."""

    def test_callback_errors_dont_prevent_storage_or_other_callbacks(self, tmp_path):
        """Test failing callbacks don't prevent storage and don't affect other callbacks."""
        event_store = EventStore(tmp_path / "test.db")

        successful_calls = []

        def fail1(event):
            raise ValueError("First callback error")

        def fail2(event):
            raise TypeError("Second callback error")

        event_store.subscribe(lambda e: successful_calls.append(f"cb1-{e.event_type}"))
        event_store.subscribe(fail1)
        event_store.subscribe(lambda e: successful_calls.append(f"cb2-{e.event_type}"))
        event_store.subscribe(fail2)

        event = Event(workflow_id="error-test", event_type="test_event", event_data={})
        assert event_store.append(event) is True

        # Successful callbacks ran
        assert "cb1-test_event" in successful_calls
        assert "cb2-test_event" in successful_calls

        # Event was stored
        with event_store as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", ("error-test",))
            assert cursor.fetchone()[0] == 1


class TestSubscriptionManagement:
    """Test subscription management and lifecycle."""

    def test_unsubscribe_and_selective_unsubscribe(self, tmp_path):
        """Test unsubscribe removes callback, handles invalid IDs, doesn't affect others."""
        event_store = EventStore(tmp_path / "test.db")

        calls1, calls2, calls3 = [], [], []
        sub1 = event_store.subscribe(lambda e: calls1.append(e.event_type))
        sub2 = event_store.subscribe(lambda e: calls2.append(e.event_type))
        sub3 = event_store.subscribe(lambda e: calls3.append(e.event_type))

        # All notified initially
        event_store.append(Event(workflow_id="t", event_type="before", event_data={}))
        assert len(calls1) == len(calls2) == len(calls3) == 1

        # Unsubscribe callback2
        assert event_store.unsubscribe(sub2) is True

        event_store.append(Event(workflow_id="t", event_type="after", event_data={}))
        assert len(calls1) == 2
        assert len(calls2) == 1  # Not called again
        assert len(calls3) == 2

        # Invalid unsubscribe
        assert event_store.unsubscribe("non-existent") is False
        assert event_store.unsubscribe(None) is False
        assert event_store.unsubscribe("") is False


class TestSubscriptionIntegration:
    """Test integration of subscription system with EventStore."""

    def test_failed_append_does_not_trigger_callbacks(self, tmp_path):
        """Test callbacks not called on failed append; called on successful append."""
        event_store = EventStore(tmp_path / "test.db")
        calls = []
        event_store.subscribe(lambda e: calls.append(e))

        # Failed append
        assert event_store.append(None) is False
        assert len(calls) == 0

        # Successful append
        event = Event(workflow_id="int-test", event_type="valid", event_data={})
        assert event_store.append(event) is True
        assert len(calls) == 1
        assert calls[0] is event

    def test_callback_can_query_database(self, tmp_path):
        """Test callback can query database (event already committed when callback runs)."""
        event_store = EventStore(tmp_path / "test.db")
        db_counts = []

        def callback(event):
            with event_store as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM events WHERE workflow_id = ?", (event.workflow_id,))
                db_counts.append(cursor.fetchone()[0])

        event_store.subscribe(callback)
        event_store.append(Event(workflow_id="tx-test", event_type="test", event_data={}))
        assert len(db_counts) == 1
        assert db_counts[0] >= 1
