#!/usr/bin/env python3
"""Manual test script for query methods."""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.events import EventLogger, EventType

def main():
    """Test get_workflow_events and get_recent_events."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        logger = EventLogger(tmp_path)

        # Test 1: get_workflow_events
        print("Test 1: get_workflow_events")
        logger.emit("workflow-1", EventType.WORKFLOW_STARTED, {"id": 1})
        logger.emit("workflow-2", EventType.WORKFLOW_STARTED, {"id": 2})
        logger.emit("workflow-1", EventType.FEATURE_STARTED, {"id": 3})

        events = logger.get_workflow_events("workflow-1")
        assert len(events) == 2, f"Expected 2 events, got {len(events)}"
        assert all(e.workflow_id == "workflow-1" for e in events), "Wrong workflow_id"
        print("  ✓ get_workflow_events returns correct events")

        # Test 2: get_workflow_events with filter
        print("\nTest 2: get_workflow_events with filter")
        logger.emit("workflow-1", EventType.FEATURE_COMPLETED, {"id": 4})
        events = logger.get_workflow_events("workflow-1", event_types=["feature.started", "feature.completed"])
        assert len(events) == 2, f"Expected 2 events, got {len(events)}"
        assert all(e.event_type in [EventType.FEATURE_STARTED, EventType.FEATURE_COMPLETED] for e in events), "Wrong event types"
        print("  ✓ get_workflow_events filters by event_type")

        # Test 3: get_recent_events
        print("\nTest 3: get_recent_events")
        logger.emit("workflow-3", EventType.WORKFLOW_STARTED, {"id": 5})
        events = logger.get_recent_events()
        assert len(events) == 5, f"Expected 5 events, got {len(events)}"
        # Most recent should be first (descending order)
        assert events[0].data["id"] == 5, f"Expected most recent event first, got {events[0].data}"
        print("  ✓ get_recent_events returns all events in descending order")

        # Test 4: get_recent_events with limit
        print("\nTest 4: get_recent_events with limit")
        events = logger.get_recent_events(limit=3)
        assert len(events) == 3, f"Expected 3 events, got {len(events)}"
        print("  ✓ get_recent_events respects limit")

        # Test 5: get_recent_events with filter
        print("\nTest 5: get_recent_events with filter")
        events = logger.get_recent_events(event_types=["workflow.started"])
        assert len(events) == 3, f"Expected 3 workflow.started events, got {len(events)}"
        assert all(e.event_type == EventType.WORKFLOW_STARTED for e in events), "Wrong event types"
        print("  ✓ get_recent_events filters by event_type")

        print("\n✅ All tests passed!")

if __name__ == "__main__":
    main()
