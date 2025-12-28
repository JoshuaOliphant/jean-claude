#!/usr/bin/env python3
"""Quick test runner for beads data model."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the models to test
from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, BeadsConfig
from datetime import datetime

def test_basic_creation():
    """Test basic BeadsTask creation."""
    print("Testing basic BeadsTask creation...")
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description="A test task",
        status=BeadsTaskStatus.TODO
    )
    assert task.id == "test-1"
    assert task.title == "Test Task"
    assert task.description == "A test task"
    assert task.status == BeadsTaskStatus.TODO
    print("✓ Basic creation works")

def test_beads_config():
    """Test BeadsConfig creation."""
    print("Testing BeadsConfig creation...")
    config = BeadsConfig()
    assert config.cli_path == "bd"
    assert config.config_options == {}
    print("✓ BeadsConfig creation works")

def main():
    """Run quick tests."""
    try:
        test_basic_creation()
        test_beads_config()
        print("\n✓ All quick tests passed!")
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
