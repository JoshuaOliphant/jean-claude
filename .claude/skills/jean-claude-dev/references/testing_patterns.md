# Testing Patterns Reference

Detailed testing examples and fixture catalog for Jean Claude development.

## Fixture Catalog

### Root Fixtures (`tests/conftest.py`)

#### `cli_runner`
```python
@pytest.fixture
def cli_runner():
    """Provides Click CLI test runner."""
    return CliRunner()
```
**Usage:** Testing any CLI command
```python
def test_my_command(cli_runner):
    result = cli_runner.invoke(my_command, ['--arg', 'value'])
    assert result.exit_code == 0
```

#### `mock_beads_task`
```python
@pytest.fixture
def mock_beads_task():
    """Returns a sample BeadsTask instance."""
    return BeadsTask(
        id="beads-test-123",
        title="Test Task",
        status=BeadsStatus.OPEN,
        priority=BeadsPriority.MEDIUM,
        type=BeadsType.TASK
    )
```
**Usage:** Any test that needs a BeadsTask
```python
def test_with_beads(mock_beads_task):
    assert mock_beads_task.id == "beads-test-123"
```

#### `mock_beads_task_factory`
```python
@pytest.fixture
def mock_beads_task_factory():
    """Factory for creating custom BeadsTask instances."""
    def _create(**kwargs):
        defaults = {
            "id": "beads-test-123",
            "title": "Test Task",
            "status": BeadsStatus.OPEN,
        }
        return BeadsTask(**{**defaults, **kwargs})
    return _create
```
**Usage:** When you need custom BeadsTask configurations
```python
def test_high_priority(mock_beads_task_factory):
    task = mock_beads_task_factory(priority=BeadsPriority.HIGH)
    assert task.priority == BeadsPriority.HIGH
```

#### `work_command_mocks`
```python
@pytest.fixture
def work_command_mocks():
    """Provides all mocks needed for work command testing."""
    with patch('jean_claude.cli.commands.work.fetch_beads_task') as mock_fetch, \
         patch('jean_claude.cli.commands.work.run_two_agent_workflow') as mock_workflow:
        yield {
            'fetch_beads_task': mock_fetch,
            'run_two_agent_workflow': mock_workflow
        }
```
**Usage:** Testing the work command
```python
def test_work_command(cli_runner, work_command_mocks):
    work_command_mocks['fetch_beads_task'].return_value = some_task
    result = cli_runner.invoke(work, ['beads-123'])
```

### Core Fixtures (`tests/core/conftest.py`)

#### `sample_beads_task`
Similar to `mock_beads_task` but with different default values. Use in core tests.

#### `mock_subprocess_success`
```python
@pytest.fixture
def mock_subprocess_success():
    """Mock subprocess.run for successful execution."""
    with patch('subprocess.run') as mock:
        mock.return_value = MagicMock(returncode=0, stdout="Success")
        yield mock
```

#### `mock_subprocess_failure`
```python
@pytest.fixture
def mock_subprocess_failure():
    """Mock subprocess.run for failed execution."""
    with patch('subprocess.run') as mock:
        mock.return_value = MagicMock(returncode=1, stderr="Error")
        yield mock
```

### Orchestration Fixtures (`tests/orchestration/conftest.py`)

#### `workflow_state`
```python
@pytest.fixture
def workflow_state(tmp_path):
    """Returns a WorkflowState with temp directory."""
    return WorkflowState(
        workflow_id="test-workflow-123",
        agent_dir=tmp_path,
        features=[],
        phases={}
    )
```

#### `execution_result`
```python
@pytest.fixture
def execution_result():
    """Returns a sample ExecutionResult."""
    return ExecutionResult(
        success=True,
        output="Test output",
        duration=1.5
    )
```

## Common Testing Patterns

### Pattern 1: Testing CLI Commands

```python
def test_status_command(cli_runner):
    """Test the status command."""
    with patch('jean_claude.cli.commands.status.load_workflow_state') as mock_load:
        mock_load.return_value = WorkflowState(...)
        result = cli_runner.invoke(status, ['workflow-123'])

        assert result.exit_code == 0
        assert "Workflow Status" in result.output
```

### Pattern 2: Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_execution():
    """Test async function with AsyncMock."""
    with patch('module.async_func', new_callable=AsyncMock) as mock:
        mock.return_value = "result"

        result = await my_async_function()

        assert result == "result"
        mock.assert_called_once()
```

### Pattern 3: Testing File Operations

```python
def test_file_creation(tmp_path):
    """Test file creation using pytest's tmp_path."""
    output_file = tmp_path / "output.json"

    create_file(output_file, {"key": "value"})

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["key"] == "value"
```

### Pattern 4: Parametrized Tests

```python
@pytest.mark.parametrize("status,expected", [
    (BeadsStatus.OPEN, True),
    (BeadsStatus.IN_PROGRESS, True),
    (BeadsStatus.CLOSED, False),
])
def test_task_is_active(status, expected):
    """Test task active state for different statuses."""
    task = BeadsTask(status=status, ...)
    assert task.is_active() == expected
```

### Pattern 5: Testing Event Store

```python
def test_event_logging(tmp_path):
    """Test event store operations."""
    db_path = tmp_path / "events.db"
    initialize_event_store(db_path)

    logger = EventLogger(db_path)
    logger.log_event(
        workflow_id="test-123",
        event_type=EventType.WORKFLOW_START,
        data={"key": "value"}
    )

    events = logger.get_events("test-123")
    assert len(events) == 1
    assert events[0].event_type == EventType.WORKFLOW_START
```

### Pattern 6: Testing Mailbox Communication

```python
def test_mailbox_message(tmp_path):
    """Test mailbox message creation."""
    inbox = tmp_path / "INBOX"
    inbox.mkdir()

    write_message(
        inbox,
        Message(
            id="msg-123",
            content="Test message",
            priority=MessagePriority.NORMAL
        )
    )

    messages = read_messages(inbox)
    assert len(messages) == 1
    assert messages[0].content == "Test message"
```

## Mock Chaining Examples

### Example 1: Multiple Return Values

```python
@patch('module.get_data')
def test_multiple_calls(mock_get):
    """Test function that calls get_data multiple times."""
    mock_get.side_effect = ["first", "second", "third"]

    results = [process_data() for _ in range(3)]

    assert results == ["first", "second", "third"]
```

### Example 2: Conditional Mocking

```python
def side_effect_func(arg):
    if arg == "valid":
        return {"status": "ok"}
    raise ValueError("Invalid argument")

@patch('module.api_call')
def test_conditional(mock_api):
    """Test with conditional mock behavior."""
    mock_api.side_effect = side_effect_func

    result = call_api("valid")
    assert result["status"] == "ok"

    with pytest.raises(ValueError):
        call_api("invalid")
```

## Integration Test Patterns

### Pattern 1: Full Workflow Test

```python
@pytest.mark.asyncio
async def test_full_workflow(tmp_path):
    """Test complete workflow execution."""
    with patch('jean_claude.core.sdk_executor.execute_prompt_async', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = ExecutionResult(success=True, output="Done")

        workflow_id = await run_two_agent_workflow(
            task_description="Test task",
            agent_dir=tmp_path
        )

        # Verify state file was created
        state_file = tmp_path / workflow_id / "state.json"
        assert state_file.exists()

        # Verify workflow completed
        state = WorkflowState.load(state_file)
        assert state.current_phase == WorkflowPhase.COMPLETE
```

### Pattern 2: Testing with Temp Directories

```python
def test_with_multiple_dirs(tmp_path):
    """Test operations across multiple directories."""
    agent_dir = tmp_path / "agents"
    specs_dir = tmp_path / "specs"
    agent_dir.mkdir()
    specs_dir.mkdir()

    # Run operations
    create_workflow(agent_dir, specs_dir)

    # Verify results
    assert (agent_dir / "workflow-123").exists()
    assert (specs_dir / "workflow-123.md").exists()
```

## Debugging Failed Tests

### Strategy 1: Print Mock Calls

```python
@patch('module.function')
def test_debug(mock_func):
    """Debug test by examining mock calls."""
    my_function()

    print("Mock called:", mock_func.called)
    print("Call count:", mock_func.call_count)
    print("Call args:", mock_func.call_args_list)

    # Will show in pytest output with -s flag
```

### Strategy 2: Capture Logs

```python
def test_with_logs(caplog):
    """Test with log capture."""
    with caplog.at_level(logging.INFO):
        my_function()

    assert "Expected log message" in caplog.text
```

### Strategy 3: Single-Threaded Debugging

```bash
# Run tests single-threaded to avoid race conditions
uv run pytest -n 0 tests/test_my_module.py

# Run with print output
uv run pytest -s tests/test_my_module.py

# Run specific test with verbose output
uv run pytest -vv tests/test_my_module.py::test_my_function
```

## Anti-Patterns to Avoid

### ❌ Don't Test Framework Behavior

```python
# BAD - Testing Click's argument parsing
def test_click_argument(cli_runner):
    result = cli_runner.invoke(my_command, ['--help'])
    assert '--arg' in result.output  # Don't test Click's --help

# GOOD - Test your command's logic
def test_command_logic(cli_runner):
    result = cli_runner.invoke(my_command, ['--arg', 'value'])
    assert my_side_effect_happened()
```

### ❌ Don't Mock Everything

```python
# BAD - Mocking our own models
@patch('module.BeadsTask')
def test_with_mock_model(mock_task):
    # This defeats the purpose of Pydantic validation
    pass

# GOOD - Use real models
def test_with_real_model():
    task = BeadsTask(id="123", title="Test")
    assert task.id == "123"
```

### ❌ Don't Create Unnecessary Fixtures

```python
# BAD - Fixture for simple values
@pytest.fixture
def task_id():
    return "beads-123"

# GOOD - Use inline values
def test_something():
    task_id = "beads-123"
    # ... rest of test
```

### ❌ Don't Test Implementation Details

```python
# BAD - Testing private methods
def test_private_method():
    obj = MyClass()
    result = obj._private_method()  # Don't test private methods
    assert result == "something"

# GOOD - Test public interface
def test_public_interface():
    obj = MyClass()
    result = obj.public_method()  # Test what users call
    assert result == "expected"
```
