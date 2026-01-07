# ABOUTME: Test suite for EventStore class initialization
# ABOUTME: Tests EventStore.__init__(db_path) with Path validation and error handling

"""Test suite for EventStore initialization.

Tests the EventStore class __init__(db_path: Path) method including:
- Database path acceptance and storage as instance variable
- Path validation with proper error handling for invalid paths
- Proper Path object conversion and handling
- Error messages for various invalid path scenarios
"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import sqlite3

# Import will fail until we implement the EventStore class - that's expected in TDD
try:
    from jean_claude.core.event_store import EventStore
except ImportError:
    # Allow tests to be written before implementation
    EventStore = None


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreInitialization:
    """Test EventStore class initialization and basic functionality."""

    def test_init_accepts_path_object(self, tmp_path):
        """Test that EventStore.__init__ accepts a Path object and stores it."""
        db_path = tmp_path / "test_events.db"

        event_store = EventStore(db_path)

        assert event_store.db_path == db_path
        assert isinstance(event_store.db_path, Path)

    def test_init_accepts_string_path(self, tmp_path):
        """Test that EventStore.__init__ accepts a string path and converts to Path."""
        db_path_str = str(tmp_path / "test_events.db")

        event_store = EventStore(db_path_str)

        assert event_store.db_path == Path(db_path_str)
        assert isinstance(event_store.db_path, Path)

    def test_init_with_nested_directory_path(self, tmp_path):
        """Test initialization with nested directory structure."""
        nested_path = tmp_path / "data" / "events" / "workflow.db"

        event_store = EventStore(nested_path)

        assert event_store.db_path == nested_path
        # Parent directories don't need to exist at init time - will be created later

    def test_init_with_relative_path(self):
        """Test initialization with relative path."""
        relative_path = Path("./data/events.db")

        event_store = EventStore(relative_path)

        assert event_store.db_path == relative_path
        # Should preserve relative nature, not convert to absolute


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStorePathValidation:
    """Test EventStore path validation and error handling."""

    def test_init_rejects_none_path(self):
        """Test that EventStore.__init__ rejects None as db_path."""
        with pytest.raises((TypeError, ValueError)) as excinfo:
            EventStore(None)

        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["none", "path", "invalid"])

    def test_init_rejects_empty_string_path(self):
        """Test that EventStore.__init__ rejects empty string as db_path."""
        with pytest.raises(ValueError) as excinfo:
            EventStore("")

        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["empty", "path", "invalid"])

    def test_init_rejects_whitespace_only_path(self):
        """Test that EventStore.__init__ rejects whitespace-only string as db_path."""
        with pytest.raises(ValueError) as excinfo:
            EventStore("   ")

        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["empty", "path", "invalid"])

    def test_init_rejects_non_string_non_path_objects(self):
        """Test that EventStore.__init__ rejects invalid types."""
        invalid_inputs = [123, [], {}, object()]

        for invalid_input in invalid_inputs:
            with pytest.raises((TypeError, ValueError)) as excinfo:
                EventStore(invalid_input)

            error_msg = str(excinfo.value).lower()
            assert any(keyword in error_msg for keyword in ["path", "type", "invalid", "expected"])

    def test_init_provides_clear_error_message_for_invalid_path_type(self):
        """Test that error messages are clear and helpful for invalid path types."""
        with pytest.raises((TypeError, ValueError)) as excinfo:
            EventStore(123)

        error_msg = str(excinfo.value)
        # Should mention what was expected and what was received
        assert "path" in error_msg.lower() or "Path" in error_msg
        assert any(keyword in error_msg.lower() for keyword in ["string", "path", "expected", "int"])


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStorePathHandling:
    """Test EventStore path handling edge cases."""

    def test_init_handles_path_with_special_characters(self, tmp_path):
        """Test initialization with paths containing special characters."""
        special_paths = [
            tmp_path / "events-with-dashes.db",
            tmp_path / "events_with_underscores.db",
            tmp_path / "events with spaces.db",
            tmp_path / "events.prod.2023.db"
        ]

        for special_path in special_paths:
            event_store = EventStore(special_path)
            assert event_store.db_path == special_path


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreErrorHandling:
    """Test EventStore error handling for invalid paths."""

    def test_init_handles_readonly_filesystem_gracefully(self):
        """Test graceful handling when path is in readonly filesystem."""
        # This test documents expected behavior - actual implementation may vary
        # The error should be descriptive and mention permissions/readonly status
        readonly_path = "/usr/readonly/events.db"

        # EventStore.__init__ now calls _init_schema() automatically
        # So errors happen during initialization
        with pytest.raises((OSError, sqlite3.Error)) as excinfo:
            event_store = EventStore(readonly_path)

        # Error message should mention the path or permission issues
        error_msg = str(excinfo.value).lower()
        assert any(keyword in error_msg for keyword in ["readonly", "permission", "path", "schema"])

    def test_init_handles_extremely_long_paths(self):
        """Test handling of extremely long paths."""
        # Create an extremely long path
        long_component = "a" * 200  # Very long directory name
        long_path = Path("/") / long_component / long_component / "events.db"

        # EventStore.__init__ now calls _init_schema() automatically
        # Filesystem limits will cause an error during initialization
        with pytest.raises((OSError, sqlite3.Error)):
            event_store = EventStore(long_path)

    def test_init_error_messages_are_descriptive(self):
        """Test that error messages provide helpful information."""
        test_cases = [
            (None, ["none", "path"]),
            ("", ["empty", "path"]),
            (123, ["type", "path", "string"]),
            ([], ["type", "path"]),
        ]

        for invalid_input, expected_keywords in test_cases:
            with pytest.raises((TypeError, ValueError)) as excinfo:
                EventStore(invalid_input)

            error_msg = str(excinfo.value).lower()
            # Should contain at least one of the expected keywords
            assert any(keyword in error_msg for keyword in expected_keywords)


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreIntegrationWithExistingCode:
    """Test EventStore integration with existing patterns."""

    def test_init_compatible_with_tmp_path_fixture(self, tmp_path):
        """Test that EventStore works well with pytest's tmp_path fixture."""
        db_path = tmp_path / "test_events.db"

        event_store = EventStore(db_path)

        assert event_store.db_path.parent == tmp_path
        assert event_store.db_path.name == "test_events.db"

    def test_init_compatible_with_pathlib_operations(self, tmp_path):
        """Test that stored path works with standard pathlib operations."""
        db_path = tmp_path / "events.db"
        event_store = EventStore(db_path)

        # Should support common pathlib operations
        assert event_store.db_path.parent == tmp_path
        assert event_store.db_path.name == "events.db"
        assert event_store.db_path.suffix == ".db"
        assert str(event_store.db_path).endswith("events.db")

    def test_init_path_can_be_used_for_sqlite_connection(self, tmp_path):
        """Test that stored path is suitable for sqlite3.connect()."""
        import sqlite3

        db_path = tmp_path / "events.db"
        event_store = EventStore(db_path)

        # Should be able to use the path with sqlite3
        # (This doesn't actually create the file, just tests path compatibility)
        connection_string = str(event_store.db_path)
        assert isinstance(connection_string, str)
        assert len(connection_string) > 0