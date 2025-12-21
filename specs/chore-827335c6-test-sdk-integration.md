# Chore: Test SDK Integration

## Metadata
adw_id: `827335c6`
prompt: `Test SDK integration`

## Chore Description

The Jean Claude project has recently integrated the Claude Code SDK (instead of subprocess-based execution) as the primary execution backend. This chore involves creating comprehensive tests for the SDK executor module (`src/jean_claude/core/sdk_executor.py`) to ensure proper functionality, error handling, and edge cases. The SDK provides async execution with streaming, retry logic, and observability through saved output files.

The tests should cover:
1. Core SDK prompt execution with different models
2. Template execution (slash commands)
3. Error handling (CLINotFoundError, ProcessError, ClaudeSDKError, TimeoutError)
4. Retry logic with exponential backoff
5. Output serialization and file saving
6. Integration with the ExecutionResult model
7. Async/sync wrapper functionality
8. Configuration and environment setup

## Relevant Files

### Existing Implementation
- `src/jean_claude/core/sdk_executor.py` - SDK executor module with async execution
- `src/jean_claude/core/agent.py` - Agent models, data types, and subprocess fallback
- `src/jean_claude/core/state.py` - Workflow state management
- `pyproject.toml` - Project configuration and dependencies

### Existing Tests
- `tests/test_state.py` - Comprehensive state management tests (good reference)

### New Files
- `tests/test_sdk_executor.py` - SDK executor unit tests with mock SDK calls
- `tests/test_sdk_integration.py` - Integration tests with actual SDK (if available)

## Step by Step Tasks

### 1. Create SDK Executor Unit Tests with Mocks
- Create `tests/test_sdk_executor.py` file
- Write tests for `_execute_prompt_async()` function:
  - Test successful execution with single text block response
  - Test successful execution with multiple text blocks
  - Test AssistantMessage with no TextBlocks
  - Test ResultMessage handling (session_id, cost_usd)
- Write tests for `_serialize_message()` function:
  - Test AssistantMessage serialization with TextBlocks
  - Test AssistantMessage with other block types
  - Test ResultMessage serialization with all fields
- Write tests for `_save_outputs()` function:
  - Test JSONL file creation and format
  - Test JSON array file creation
  - Test final result JSON file saving
  - Test output directory creation

### 2. Test Error Handling in SDK Executor
- Create tests for exception handling in `_execute_prompt_async()`:
  - CLINotFoundError: Verify error message and retry code
  - ProcessError: Verify exit code handling
  - ClaudeSDKError: Verify SDK error message preservation
  - TimeoutError: Verify timeout handling
  - Generic Exception: Verify fallback error handling
- Verify each error returns ExecutionResult with success=False

### 3. Test Retry Logic in SDK Executor
- Create tests for `execute_prompt_async()` function:
  - Test successful execution on first attempt (no retries)
  - Test successful execution on second attempt after transient error
  - Test successful execution on third attempt after multiple errors
  - Test max retries exhausted (returns error after 3 failures)
  - Test RetryCode.NONE skips retries (CLINotFoundError case)
  - Verify delay pattern [1, 3, 5] seconds between retries

### 4. Test Template Execution in SDK Executor
- Create tests for `execute_template_async()` function:
  - Test command and args are joined correctly in prompt
  - Test model is passed through correctly
  - Test working_dir is passed through
  - Test dangerously_skip_permissions is set to True
- Create tests for sync wrappers:
  - Test `execute_prompt_sdk()` works from sync context
  - Test `execute_template_sdk()` works from sync context
  - Verify anyio.run wrapping is correct

### 5. Test Model Mapping and Options
- Create tests for ClaudeCodeOptions configuration:
  - Test model names: "sonnet", "opus", "haiku"
  - Test working_dir path handling
  - Test max_turns default (100)
  - Test permission_mode: "acceptEdits" when dangerously_skip_permissions=True
  - Test permission_mode: None when dangerously_skip_permissions=False

### 6. Test Output Directory Handling
- Create tests for output directory creation:
  - Test output_dir from request is used if provided
  - Test default output_dir: `agents/{workflow_id}`
  - Test directory is created with parents=True
  - Test workflow_id generation is 8-character UUID
  - Test multiple calls generate unique directories

### 7. Test Message Type Handling
- Create tests for SDK message type handling:
  - Test AssistantMessage with TextBlock
  - Test AssistantMessage with other block types (non-TextBlock)
  - Test ResultMessage with all attributes
  - Test message serialization for observability
  - Test edge case: empty messages list
  - Test edge case: ResultMessage without expected attributes

### 8. Test Integration with Agent Module
- Create tests verifying SDK executor integration:
  - Test ExecutionResult model compatibility
  - Test all RetryCode values are used correctly
  - Test PromptRequest/TemplateRequest data models
  - Verify output constants (OUTPUT_JSONL, OUTPUT_JSON, FINAL_OBJECT_JSON)

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run pytest tests/test_sdk_executor.py -v` - Run all SDK executor tests
- `uv run pytest tests/test_sdk_executor.py --cov=src/jean_claude/core/sdk_executor --cov-report=term-missing` - Check code coverage (target: >85%)
- `uv run ruff check src/jean_claude/core/sdk_executor.py` - Lint SDK executor module
- `uv run ruff check tests/test_sdk_executor.py` - Lint test file
- `uv run mypy src/jean_claude/core/sdk_executor.py` - Type checking
- `uv run pytest tests/test_sdk_executor.py::TestSDKExecutorAsync::test_execute_prompt_async_success -v` - Sanity check single test

## Notes

- **Mocking Strategy**: Use `unittest.mock` or `pytest-mock` to mock SDK imports and functions. This avoids needing the actual Claude CLI installed during tests.
- **Async Testing**: Tests should use `pytest-asyncio` which is already in dev dependencies.
- **Message Fixtures**: Create reusable message fixtures for AssistantMessage, TextBlock, and ResultMessage
- **Error Scenarios**: Test both retryable and non-retryable errors separately
- **Observability**: Verify that output files are created with correct JSON structure
- **Backward Compatibility**: Ensure tests don't break existing subprocess-based fallback in `agent.py`
- **Coverage**: Aim for >85% code coverage on `sdk_executor.py` module
- **Performance**: Keep test execution time reasonable (<5 seconds for unit tests)
