#!/usr/bin/env python3
"""Quick inline test for BeadsTrailerFormatter."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Test import
    from jean_claude.core.beads_trailer_formatter import BeadsTrailerFormatter
    print("✓ Import successful")

    # Test basic initialization
    formatter = BeadsTrailerFormatter("test.1", 1, 5)
    print("✓ Initialization works")

    # Test format
    result = formatter.format()
    print("✓ Format works")
    print(f"\nFormatted output:\n{result}")

    # Test validation
    assert "Beads: test.1" in result
    assert "Feature: 1/5" in result
    print("\n✓ Output validation passed")

    # Test from_task_metadata
    metadata = {
        "beads_task_id": "jean_claude-2sz.8",
        "current_feature_index": 5,
        "features": [None] * 10
    }
    formatter2 = BeadsTrailerFormatter.from_task_metadata(metadata)
    result2 = formatter2.format()
    print(f"\nFrom metadata:\n{result2}")
    assert "Beads: jean_claude-2sz.8" in result2
    assert "Feature: 6/10" in result2
    print("✓ from_task_metadata works")

    print("\n✅ ALL QUICK TESTS PASSED!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
