#!/usr/bin/env python3
"""Quick import test to verify BeadsTask is importable."""

try:
    from jean_claude.core.beads import BeadsTask, BeadsTaskStatus

    # Quick smoke test
    task = BeadsTask(
        id="test",
        title="Test",
        description="Test",
        status=BeadsTaskStatus.TODO
    )

    # Test to_dict
    d = task.to_dict()

    # Test from_dict
    task2 = BeadsTask.from_dict(d)

    print("SUCCESS: BeadsTask model is working correctly")
    print(f"- Fields: id={task.id}, title={task.title}, description={task.description}")
    print(f"- to_dict() returns: {type(d).__name__}")
    print(f"- from_dict() creates: {type(task2).__name__}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
