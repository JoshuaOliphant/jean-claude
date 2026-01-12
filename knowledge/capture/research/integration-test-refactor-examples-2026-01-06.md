# Integration Test Refactoring Examples

**Date**: January 6, 2026
**Scope**: Specific code examples of test improvements

---

## Example 1: Redundant SQLite Query Pattern

### Current Code (Repeated in 15+ tests)

**File**: tests/core/test_notes_api.py (lines 49-68)
```python
def test_add_note_writes_to_sqlite(self, tmp_path):
    """Verify note is written as event to SQLite."""
    # Setup
    workflow_id = "test-workflow"
    event_logger = EventLogger(tmp_path)
    notes = Notes(
        workflow_id=workflow_id,
        project_root=tmp_path,
        event_logger=event_logger
    )

    # Execute
    note = notes.add(
        agent_id="test-agent",
        title="Test Observation",
        content="Test content",
        category=NoteCategory.OBSERVATION,
        tags=["test-tag"],
        related_file="test.py",
        related_feature="test-feature",
    )

    # Verify note was created
    assert note.agent_id == "test-agent"

    # REDUNDANT PATTERN - Repeated in 15+ tests:
    import sqlite3
    import json

    events_db = tmp_path / ".jc" / "events.db"
    assert events_db.exists()

    conn = sqlite3.connect(events_db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT event_type, data
        FROM events
        WHERE workflow_id = ? AND event_type = ?
    """, (workflow_id, "agent.note.observation"))

    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 1
    event_type, data_json = rows[0]
    data = json.loads(data_json)

    assert data["agent_id"] == "test-agent"
    assert data["title"] == "Test Observation"
    # ... more assertions
```

### Refactored Code

**Add to tests/core/conftest.py**:
```python
import sqlite3
import json
from pathlib import Path

@pytest.fixture
def query_events():
    """Helper to query events from SQLite database.

    Usage:
        def test_something(tmp_path, query_events):
            events = query_events(tmp_path, "workflow-id")
            assert len(events) == 1
    """
    def _query(
        project_root: Path,
        workflow_id: str,
        event_type: str | None = None
    ) -> list[tuple]:
        """Query events from the event store.

        Returns list of (event_type, data_dict) tuples.
        """
        events_db = project_root / ".jc" / "events.db"
        assert events_db.exists(), f"Events database not found at {events_db}"

        conn = sqlite3.connect(events_db)
        cursor = conn.cursor()

        if event_type:
            cursor.execute(
                "SELECT event_type, data FROM events WHERE workflow_id = ? AND event_type = ?",
                (workflow_id, event_type)
            )
        else:
            cursor.execute(
                "SELECT event_type, data FROM events WHERE workflow_id = ?",
                (workflow_id,)
            )

        rows = cursor.fetchall()
        conn.close()

        # Convert data JSON strings to dicts
        return [(etype, json.loads(data_str)) for etype, data_str in rows]

    return _query
```

**Refactored Test** (22 lines instead of 38):
```python
def test_add_note_writes_to_sqlite(self, tmp_path, query_events):
    """Verify note is written as event to SQLite."""
    workflow_id = "test-workflow"
    event_logger = EventLogger(tmp_path)
    notes = Notes(
        workflow_id=workflow_id,
        project_root=tmp_path,
        event_logger=event_logger
    )

    # Execute
    note = notes.add(
        agent_id="test-agent",
        title="Test Observation",
        content="Test content",
        category=NoteCategory.OBSERVATION,
        tags=["test-tag"],
        related_file="test.py",
        related_feature="test-feature",
    )

    # Verify
    assert note.agent_id == "test-agent"

    # Use helper - much cleaner
    events = query_events(tmp_path, workflow_id, "agent.note.observation")
    assert len(events) == 1

    event_type, data = events[0]
    assert event_type == "agent.note.observation"
    assert data["agent_id"] == "test-agent"
    assert data["title"] == "Test Observation"
    assert data["content"] == "Test content"
    assert data["tags"] == ["test-tag"]
    assert data["related_file"] == "test.py"
    assert data["related_feature"] == "test-feature"
```

### Savings

- **Per test**: 16 lines reduced to 2 lines (87% reduction)
- **Across 15 tests**: ~180 lines → ~30 lines
- **Readability**: Intent is clearer (query_events vs raw SQLite)
- **Maintainability**: If database query changes, update once

---

## Example 2: Event Store Setup Pattern

### Current Code (Repeated in 25+ tests)

**Files**: test_notes_api.py, test_notes_integration.py, test_event_store_*.py

```python
def test_multiple_notes_emit_multiple_events(self, tmp_path):
    """Test: Multiple notes emit multiple events to database."""
    workflow_id = "test-workflow"
    project_root = tmp_path

    # REPEATED SETUP PATTERN (25+ times):
    event_logger = EventLogger(project_root)
    notes = Notes(
        workflow_id=workflow_id,
        project_root=project_root,
        event_logger=event_logger
    )

    # Write multiple notes
    notes.add(
        agent_id="agent-1",
        title="First Note",
        content="Content 1",
        category=NoteCategory.OBSERVATION,
        tags=["tag1"],
    )
    # ... more notes ...
```

### Refactored Code

**Add to tests/core/conftest.py**:
```python
@pytest.fixture
def notes_api_with_logger(tmp_path):
    """Fixture providing initialized Notes API with event logger.

    Returns: (notes, event_logger, events_db_path)

    Usage:
        def test_something(notes_api_with_logger):
            notes, logger, db = notes_api_with_logger("workflow-1")
    """
    def _create_notes(workflow_id: str):
        logger = EventLogger(tmp_path)
        notes = Notes(
            workflow_id=workflow_id,
            project_root=tmp_path,
            event_logger=logger
        )
        db_path = tmp_path / ".jc" / "events.db"
        return notes, logger, db_path

    return _create_notes
```

**Refactored Test** (20 lines instead of 35):
```python
def test_multiple_notes_emit_multiple_events(self, notes_api_with_logger):
    """Test: Multiple notes emit multiple events to database."""
    notes, event_logger, events_db = notes_api_with_logger("test-workflow")

    # Write multiple notes
    notes.add(
        agent_id="agent-1",
        title="First Note",
        content="Content 1",
        category=NoteCategory.OBSERVATION,
        tags=["tag1"],
    )

    notes.add(
        agent_id="agent-2",
        title="Second Note",
        content="Content 2",
        category=NoteCategory.LEARNING,
        tags=["tag2"],
    )

    # Direct SQLite verification (or use query_events helper)
    events = query_events(events_db.parent.parent, "test-workflow")
    assert len(events) == 2
```

### Savings

- **Per test**: 8 lines of setup → 1 line
- **Across 25 tests**: ~200 lines → ~25 lines
- **Consistency**: All tests initialize identically
- **Flexibility**: Can parameterize workflow_id easily

---

## Example 3: Complex Workflow Test - Before & After

### Current Code (test_workflow_with_failure_recovery)

**File**: tests/orchestration/test_auto_continue_integration.py (lines 122-206)

**Issues**:
1. Tests 3 concerns in one 84-line test
2. Hard to tell which part fails
3. Difficult to reuse failure detection logic

```python
@pytest.mark.asyncio
async def test_workflow_with_failure_recovery(mock_project_root):
    """Test workflow that fails, gets fixed, and resumes."""
    # CONCERN 1: Initialize workflow
    features = [
        ("Feature 1", "First feature", None),
        ("Feature 2", "Second feature - will fail", None),
        ("Feature 3", "Third feature", None),
    ]

    state = await initialize_workflow(
        workflow_id="failure-recovery",
        workflow_name="Failure Recovery Test",
        workflow_type="chore",
        features=features,
        project_root=mock_project_root,
        max_iterations=5,
    )

    # CONCERN 2: Execute with failure
    call_count = 0

    async def mock_execute_with_failure(request, max_retries):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ExecutionResult(output="Success", success=True, cost_usd=0.05)
        elif call_count == 2:
            return ExecutionResult(output="Failed!", success=False, cost_usd=0.03)
        else:
            return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(...), patch(...):
        first_run_state = await run_auto_continue(...)

    # CONCERN 3: Verify failure
    assert not first_run_state.is_complete()
    assert first_run_state.is_failed()
    assert first_run_state.features[0].status == "completed"
    assert first_run_state.features[1].status == "failed"

    # CONCERN 4: Simulate fix and resume
    first_run_state.features[1].status = "not_started"
    first_run_state.save(mock_project_root)

    # CONCERN 5: Resume workflow
    resumed_state = WorkflowState.load("failure-recovery", mock_project_root)
    resumed_state.current_feature_index = 1

    call_count = 0

    async def mock_execute_success(request, max_retries):
        return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(...), patch(...):
        final_state = await run_auto_continue(...)

    # CONCERN 6: Verify completion
    assert final_state.is_complete()
    assert all(f.status == "completed" for f in final_state.features)
```

### Refactored Code - Split into 3 Tests

**Test 1: Failure Detection** (Focused on execution layer)
```python
@pytest.mark.asyncio
async def test_workflow_detects_feature_failure(mock_project_root):
    """Test: Workflow stops when feature fails."""
    features = [
        ("Feature 1", "First feature", None),
        ("Feature 2", "Will fail", None),
        ("Feature 3", "Third feature", None),
    ]

    state = await initialize_workflow(
        workflow_id="failure-test",
        workflow_name="Failure Test",
        workflow_type="chore",
        features=features,
        project_root=mock_project_root,
        max_iterations=5,
    )

    # Execution: Feature 1 succeeds, Feature 2 fails
    execution_results = [
        ExecutionResult(output="Success", success=True, cost_usd=0.05),
        ExecutionResult(output="Failed!", success=False, cost_usd=0.03),
    ]

    result_index = 0
    async def mock_execute(request, max_retries):
        nonlocal result_index
        result = execution_results[result_index]
        result_index += 1
        return result

    with patch(..., new=mock_execute), patch(...):
        final_state = await run_auto_continue(
            state=state,
            project_root=mock_project_root,
            max_iterations=2,
        )

    # Verify
    assert not final_state.is_complete()
    assert final_state.is_failed()
    assert final_state.features[0].status == "completed"
    assert final_state.features[1].status == "failed"
    assert final_state.features[2].status == "not_started"
```

**Test 2: State Persistence** (Focused on save/load)
```python
def test_workflow_state_persists_after_failure(mock_project_root):
    """Test: Failed workflow state is persisted to disk."""
    workflow_id = "persistence-test"

    # Create a failed workflow state
    state = WorkflowState(workflow_id=workflow_id, ...)
    state.features[0].status = "completed"
    state.features[1].status = "failed"
    state.save(mock_project_root)

    # Load from disk
    loaded = WorkflowState.load(workflow_id, mock_project_root)

    # Verify persistence
    assert loaded.features[0].status == "completed"
    assert loaded.features[1].status == "failed"
```

**Test 3: Workflow Resumption** (Focused on resume logic)
```python
@pytest.mark.asyncio
async def test_workflow_resumes_after_manual_fix(mock_project_root):
    """Test: Workflow resumes correctly after manual fix."""
    workflow_id = "resume-test"

    # Start with failed state from disk
    failed_state = WorkflowState.load(workflow_id, mock_project_root)
    failed_state.features[1].status = "failed"
    failed_state.save(mock_project_root)

    # Manually fix: mark as ready to retry
    resumed_state = WorkflowState.load(workflow_id, mock_project_root)
    resumed_state.features[1].status = "not_started"
    resumed_state.current_feature_index = 1

    # Resume with success
    async def mock_execute_success(request, max_retries):
        return ExecutionResult(output="Success", success=True, cost_usd=0.05)

    with patch(..., new=mock_execute_success), patch(...):
        final_state = await run_auto_continue(
            state=resumed_state,
            project_root=mock_project_root,
            max_iterations=3,
        )

    # Verify
    assert final_state.is_complete()
    assert all(f.status == "completed" for f in final_state.features)
```

### Benefits of Splitting

| Aspect | Before | After |
|--------|--------|-------|
| Lines per test | 84 | 35-45 |
| Time to diagnose failure | Hard | Easy |
| Reusable test components | No | Yes |
| Responsibility per test | 6 concerns | 1 concern |
| Test isolation | Weak | Strong |

---

## Example 4: Consolidation Pattern - Before & After

### Current Code (Too Many Similar Tests)

**What NOT to do** (hypothetical, but common):
```python
class TestMailboxUnreadCount:
    def test_unread_count_initial(self, tmp_path):
        mailbox = Mailbox(workflow_id="test", base_dir=tmp_path)
        assert mailbox.get_unread_count() == 0

    def test_unread_count_after_send(self, tmp_path, message_factory):
        mailbox = Mailbox(workflow_id="test", base_dir=tmp_path)
        msg = message_factory(subject="Test")
        mailbox.send_message(msg, to_inbox=True)
        assert mailbox.get_unread_count() == 1

    def test_unread_count_after_read(self, tmp_path, message_factory):
        mailbox = Mailbox(workflow_id="test", base_dir=tmp_path)
        msg = message_factory(subject="Test")
        mailbox.send_message(msg, to_inbox=True)
        mailbox.mark_as_read(msg.id)
        assert mailbox.get_unread_count() == 0
```

**Issues**:
- 3 tests for one behavior
- Repeated initialization
- Hard to see the full lifecycle

### Refactored Code (Actual Code in Repository)

**File**: tests/core/test_mailbox_api.py (lines 142-164)

```python
class TestMailboxUnreadCount:
    """Tests for unread count - consolidated from 4 tests to 1."""

    def test_unread_count_behavior(self, tmp_path, message_factory):
        """Test complete unread count behavior in one test."""
        mailbox = Mailbox(workflow_id="test-workflow", base_dir=tmp_path)

        # Initially zero
        assert mailbox.get_unread_count() == 0

        # After first message
        msg1 = message_factory(subject="First")
        mailbox.send_message(msg1, to_inbox=True)
        assert mailbox.get_unread_count() == 1

        # After second message
        msg2 = message_factory(subject="Second")
        mailbox.send_message(msg2, to_inbox=True)
        assert mailbox.get_unread_count() == 2

        # After marking first as read
        mailbox.mark_as_read(msg1.id)
        assert mailbox.get_unread_count() == 1

        # After marking second as read
        mailbox.mark_as_read(msg2.id)
        assert mailbox.get_unread_count() == 0
```

**Benefits**:
- **1 test instead of 3-4** - Clearer flow
- **Less setup duplication** - Single mailbox initialization
- **Full lifecycle visible** - Easy to understand state transitions
- **Easier to maintain** - One change fixes one test

---

## Example 5: Factory Pattern Best Practice

### Current Code (Good Pattern - Keep As-Is)

**File**: tests/conftest.py (lines 407-441)

```python
@pytest.fixture
def message_factory() -> Callable[..., Message]:
    """Factory fixture for creating Message with custom values."""
    def _create_message(
        from_agent: str = "agent-1",
        to_agent: str = "agent-2",
        type: str = "test",
        subject: str = "Test Subject",
        body: str = "Test body content",
        priority: MessagePriority = MessagePriority.NORMAL,
        awaiting_response: bool = False,
        id: str | None = None,
        correlation_id: str | None = None,
    ) -> Message:
        kwargs = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "type": type,
            "subject": subject,
            "body": body,
            "priority": priority,
            "awaiting_response": awaiting_response,
        }
        if id is not None:
            kwargs["id"] = id
        if correlation_id is not None:
            kwargs["correlation_id"] = correlation_id
        return Message(**kwargs)
    return _create_message
```

**Why This Is Excellent**:

1. **Flexible defaults** - 9 parameters with sensible defaults
2. **Optional fields** - Doesn't force all fields to be specified
3. **Reusable** - Used in 20+ tests
4. **Readable** - Clear what each parameter does
5. **Prevents duplication** - Alternative would be 5-10 separate fixtures

**Example Usage**:
```python
# Default message
msg = message_factory()

# Urgent message with correlation
msg = message_factory(
    priority=MessagePriority.URGENT,
    awaiting_response=True,
    correlation_id="workflow-1"
)

# Custom sender/recipient
msg = message_factory(
    from_agent="coder",
    to_agent="coordinator",
    subject="Help needed"
)
```

**DO NOT CHANGE** - This is a best practice pattern.

---

## Summary of Recommended Changes

| Change | Impact | Effort | Priority |
|--------|--------|--------|----------|
| Create `query_events` helper | -150 lines | 30 min | High |
| Create `notes_api_with_logger` fixture | -175 lines | 30 min | High |
| Create `event_store_with_logger` fixture | -100 lines | 20 min | High |
| Split test_workflow_with_failure_recovery | Better diagnostics | 2 hours | Medium |
| Split test_full_workflow_lifecycle | Better diagnostics | 1.5 hours | Medium |
| Document fixture patterns | Maintainability | 30 min | Low |

---

## Validation Checklist Before Implementing

Before making any changes:

- [ ] Run full test suite before making changes
- [ ] Each refactored test still has clear responsibility
- [ ] Fixture helpers have docstrings with usage examples
- [ ] New fixtures follow existing pattern (factory style)
- [ ] Tests still pass with -n 4 (parallel execution)
- [ ] No shared state between tests
- [ ] Integration tests still test multiple layers
- [ ] Unit tests still work with mocks

---

## Files to Modify (In Priority Order)

1. **tests/core/conftest.py** - Add helper fixtures (150 lines)
2. **tests/core/test_notes_api.py** - Use query_events helper (180 line reduction)
3. **tests/core/test_notes_integration.py** - Use notes_api_with_logger (100 line reduction)
4. **tests/orchestration/test_auto_continue_integration.py** - Split failure test (50 line reduction)
5. **tests/orchestration/test_two_agent.py** - Add docstrings (30 line addition)

---

## Estimated Outcomes

- **Total code reduction**: ~425 lines
- **Test clarity**: Significantly improved
- **Maintainability**: Higher (less duplication)
- **Performance**: No change (file I/O is not bottleneck)
- **Coverage**: No change (same tests, better organized)

