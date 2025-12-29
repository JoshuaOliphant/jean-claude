# Barrel Import Mapping Report

## Overview

This report documents all barrel imports from `jean_claude.core` found in the codebase. Barrel imports are imports that use the `core/__init__.py` file to re-export items from submodules.

**Generated:** 2025-12-28

## Summary Statistics

- **Total files with barrel imports:** 53
- **Total import statements:** 134
- **Source files (src/):** 29
- **Test files (tests/):** 24

## What are Barrel Imports?

The `jean_claude.core` package currently re-exports 33 items from 15 different modules through its `__init__.py` file. This allows imports like:

```python
from jean_claude.core import WorkflowState
```

instead of:

```python
from jean_claude.core.state import WorkflowState
```

## Current Barrel Exports

The `src/jean_claude/core/__init__.py` file exports:

### From `agent.py`:
- `ExecutionResult`
- `PromptRequest`
- `RetryCode`
- `TemplateRequest`
- `execute_prompt`
- `execute_template`
- `find_claude_cli`
- `check_claude_installed`

### From `beads.py`:
- `BeadsTask`
- `BeadsTaskStatus`

### From `beads_trailer_formatter.py`:
- `BeadsTrailerFormatter`

### From `commit_body_generator.py`:
- `CommitBodyGenerator`

### From `events.py`:
- `Event`
- `EventLogger`
- `EventType`

### From `feature_commit_orchestrator.py`:
- `FeatureCommitOrchestrator`

### From `git_file_stager.py`:
- `GitFileStager`

### From `inbox_count.py`:
- `InboxCount`

### From `inbox_count_persistence.py`:
- `read_inbox_count`
- `write_inbox_count`

### From `mailbox_api.py`:
- `Mailbox`

### From `mailbox_paths.py`:
- `MailboxPaths`

### From `message.py`:
- `Message`
- `MessagePriority`

### From `message_reader.py`:
- `read_messages`

### From `message_writer.py`:
- `MessageBox`
- `write_message`

### From `state.py`:
- `Feature`
- `WorkflowPhase`
- `WorkflowState`

### From `task_validator.py`:
- `TaskValidator`
- `ValidationResult`

### From `test_runner_validator.py`:
- `TestRunnerValidator`

### From `validation_output_formatter.py`:
- `ValidationOutputFormatter`

## Most Frequently Imported Items

### Top 10 Most Imported Classes/Functions:

1. **WorkflowState** - 19 occurrences
2. **BeadsTask** - 10 occurrences
3. **Message** - 10 occurrences
4. **ExecutionResult** - 9 occurrences
5. **BeadsTaskStatus** - 8 occurrences
6. **MailboxPaths** - 8 occurrences
7. **ValidationResult** - 7 occurrences
8. **MessagePriority** - 7 occurrences
9. **PromptRequest** - 6 occurrences
10. **Feature** - 6 occurrences

### Most Imported Modules:

1. **jean_claude.core.state** - 19 imports
2. **jean_claude.core.beads** - 13 imports
3. **jean_claude.core.agent** - 12 imports
4. **jean_claude.core.mailbox_paths** - 12 imports
5. **jean_claude.core.message** - 11 imports

## Files Breakdown

### Source Files (29 files)

#### Core Module Files (11 files)
Files within `src/jean_claude/core/` that import from other core modules:
- `edit_and_revalidate.py`
- `feature_commit_orchestrator.py`
- `inbox_count_persistence.py`
- `interactive_prompt_handler.py`
- `mailbox_api.py`
- `message_reader.py`
- `message_writer.py`
- `sdk_executor.py`
- `task_validator.py`
- `validation_output_formatter.py`
- `verification.py`

#### CLI Command Files (7 files)
Files in `src/jean_claude/cli/commands/`:
- `implement.py`
- `logs.py`
- `prime.py`
- `prompt.py`
- `run.py`
- `status.py`
- `work.py`

#### Orchestration Files (4 files)
Files in `src/jean_claude/orchestration/`:
- `auto_continue.py`
- `post_tool_use_hook.py`
- `subagent_stop_hook.py`
- `two_agent.py`
- `user_prompt_submit_hook.py`

#### Dashboard Files (1 file)
- `src/jean_claude/dashboard/app.py`

### Test Files (24 files)

#### Core Tests (4 files)
- `tests/core/conftest.py`
- `tests/core/test_mailbox_api.py`
- `tests/core/test_message_reader.py`
- `tests/core/test_message_writer.py`

#### Orchestration Tests (7 files)
- `tests/orchestration/conftest.py`
- `tests/orchestration/test_auto_continue.py`
- `tests/orchestration/test_auto_continue_integration.py`
- `tests/orchestration/test_post_tool_use_hook.py`
- `tests/orchestration/test_subagent_stop_hook.py`
- `tests/orchestration/test_two_agent.py`
- `tests/orchestration/test_user_prompt_submit_hook.py`

#### CLI Tests (1 file)
- `tests/cli/commands/test_work_error_handling.py`

#### Root Test Files (12 files)
- `tests/conftest.py`
- `tests/test_commit_body_generator.py`
- `tests/test_commit_error_handler.py`
- `tests/test_commit_message_formatter.py`
- `tests/test_commit_workflow_integration.py`
- `tests/test_conventional_commit_parser.py`
- `tests/test_edit_integration.py`
- `tests/test_feature_commit_orchestrator.py`
- `tests/test_git_file_stager.py`
- `tests/test_interactive_prompt.py`
- `tests/test_security.py`
- `tests/test_spec_generation.py`
- `tests/test_state.py`
- `tests/test_status_command.py`
- `tests/test_task_validator.py`
- `tests/test_test_runner_validator.py`
- `tests/test_verification.py`
- `tests/test_work_command.py`

## Next Steps

The next features in the workflow will use this mapping to:

1. Create a reference mapping of exports to their source modules
2. Update all barrel imports to direct imports
3. Remove the barrel exports from `core/__init__.py`
4. Verify no barrel imports remain
5. Measure startup time improvement

## Data File

The complete mapping data is available in: `barrel_imports_mapping.json`

This JSON file contains:
- Summary statistics
- Full list of files with their imports
- Module names and imported items for each import statement
