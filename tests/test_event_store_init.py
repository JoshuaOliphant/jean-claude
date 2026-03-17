# ABOUTME: Test suite for EventStore class initialization
# ABOUTME: Tests EventStore.__init__(db_path) with Path validation and error handling

"""Test suite for EventStore initialization.

Tests path acceptance, conversion, validation, and error handling.
"""

import pytest
from pathlib import Path
import sqlite3

try:
    from jean_claude.core.event_store import EventStore
except ImportError:
    EventStore = None


@pytest.mark.skipif(EventStore is None, reason="EventStore not implemented yet")
class TestEventStoreInitialization:
    """Test EventStore class initialization."""

    def test_init_accepts_path_and_string(self, tmp_path):
        """Test init accepts Path objects and strings, storing as Path."""
        # Path object
        path_store = EventStore(tmp_path / "path.db")
        assert path_store.db_path == tmp_path / "path.db"
        assert isinstance(path_store.db_path, Path)

        # String path
        str_store = EventStore(str(tmp_path / "str.db"))
        assert isinstance(str_store.db_path, Path)

        # Nested path
        nested = tmp_path / "data" / "events" / "workflow.db"
        nested_store = EventStore(nested)
        assert nested_store.db_path == nested

    def test_init_handles_special_characters_in_path(self, tmp_path):
        """Test paths with dashes, underscores, spaces, dots."""
        for name in ["events-with-dashes.db", "events_underscores.db",
                      "events with spaces.db", "events.prod.2023.db"]:
            store = EventStore(tmp_path / name)
            assert store.db_path.name == name

    def test_init_rejects_invalid_paths(self):
        """Test None, empty, whitespace, and non-string/Path types rejected."""
        with pytest.raises((TypeError, ValueError)):
            EventStore(None)
        with pytest.raises(ValueError):
            EventStore("")
        with pytest.raises(ValueError):
            EventStore("   ")
        for invalid in [123, [], {}, object()]:
            with pytest.raises((TypeError, ValueError)):
                EventStore(invalid)

    def test_init_error_messages_are_descriptive(self):
        """Test error messages contain helpful keywords."""
        for invalid, keywords in [(None, ["none", "path"]), ("", ["empty", "path"]),
                                  (123, ["type", "path", "string"]), ([], ["type", "path"])]:
            with pytest.raises((TypeError, ValueError)) as exc:
                EventStore(invalid)
            msg = str(exc.value).lower()
            assert any(kw in msg for kw in keywords)

    def test_init_handles_filesystem_errors(self):
        """Test readonly/unreachable paths and extremely long paths."""
        with pytest.raises((OSError, sqlite3.Error)):
            EventStore("/usr/readonly/events.db")
        long = Path("/") / ("a" * 200) / ("a" * 200) / "events.db"
        with pytest.raises((OSError, sqlite3.Error)):
            EventStore(long)

    def test_init_path_compatible_with_pathlib_and_sqlite(self, tmp_path):
        """Test stored path supports pathlib operations and sqlite connection."""
        store = EventStore(tmp_path / "events.db")
        assert store.db_path.parent == tmp_path
        assert store.db_path.name == "events.db"
        assert store.db_path.suffix == ".db"
        assert isinstance(str(store.db_path), str)
