# Feature: Edit Task Integration

## Overview

Implemented the `edit-task-integration` feature (Feature 11 of 15) which allows users to edit Beads tasks directly from the validation prompt when issues are detected.

## What Was Implemented

### 1. EditTaskHandler Module
**File:** `src/jean_claude/core/edit_task_handler.py`

A new handler class that invokes the `bd edit` command to open a Beads task in the user's editor.

**Key Features:**
- Invokes `bd edit <task_id>` subprocess
- Waits for editor to close before returning
- Supports custom bd CLI path
- Proper error handling for subprocess failures

### 2. Edit and Revalidate Flow
**File:** `src/jean_claude/core/edit_and_revalidate.py`

A complete workflow function that:
1. Opens the task in editor using `bd edit`
2. Waits for user to finish editing
3. Fetches the updated task from Beads
4. Re-validates the task
5. Returns the validation result

**Key Features:**
- Supports strict mode validation
- Propagates errors properly
- Returns ValidationResult for consistent handling

### 3. Work Command Integration
**File:** `src/jean_claude/cli/commands/work.py`

Enhanced the `jc work` command with validation and edit capabilities:

**New Features:**
- Added `--strict` flag for strict validation mode
- Validates tasks before starting work
- Shows interactive prompt when validation issues are found
- Implements edit-and-revalidate loop:
  - User can choose to edit the task
  - Task opens in editor
  - After editing, task is re-validated
  - Loop continues until user proceeds or cancels
- Re-fetches task data after successful edit

**User Flow:**
1. User runs `jc work <task-id>`
2. Task is fetched and validated
3. If issues found, user sees interactive prompt:
   - [1] Proceed anyway
   - [2] Open task for editing
   - [3] Cancel
4. If user selects [2]:
   - Task opens in editor
   - User makes changes and saves
   - Task is re-fetched and re-validated
   - User sees updated validation results
   - Can edit again or proceed/cancel
5. Work continues with validated task

### 4. Comprehensive Tests
**Files:**
- `tests/test_edit_integration.py` - Unit tests for edit components
- `tests/test_edit_integration_flow.py` - Integration tests for complete flow

**Test Coverage:**
- EditTaskHandler initialization and configuration
- Subprocess invocation and error handling
- Edit and revalidate workflow
- Strict mode handling
- Error propagation
- Multi-edit loop scenarios
- Work command integration

## Technical Details

### Dependencies
- Uses existing `TaskValidator` for validation
- Uses existing `InteractivePromptHandler` for user prompts
- Uses existing `fetch_beads_task` for fetching task data
- Integrates with Beads CLI (`bd edit` command)

### Error Handling
- Validates task_id is not empty
- Handles subprocess failures gracefully
- Propagates errors from bd CLI
- Handles KeyboardInterrupt during editing

### Validation Loop
The edit loop continues until:
- Task passes all validations, OR
- User chooses to proceed despite warnings, OR
- User cancels the operation, OR
- An error occurs

### Strict Mode
When `--strict` flag is used:
- Validation warnings are converted to errors
- Task must pass all checks to proceed
- Edit loop enforces stricter requirements

## Usage Examples

### Basic Usage
```bash
# Work on a task with validation
jc work jean_claude-2sz.7

# If validation issues found:
# [1] Proceed anyway
# [2] Open task for editing  <- Select this
# [3] Cancel

# Task opens in editor, make changes, save and close
# Task is re-validated automatically
```

### With Strict Mode
```bash
# Enforce strict validation (warnings become errors)
jc work jean_claude-2sz.7 --strict

# Task must pass all validation checks to proceed
# Or user must edit until it passes
```

### With Other Flags
```bash
# Combine with other work command flags
jc work jean_claude-2sz.7 --strict --model opus --show-plan
```

## Files Created/Modified

### New Files
1. `src/jean_claude/core/edit_task_handler.py` - EditTaskHandler class
2. `src/jean_claude/core/edit_and_revalidate.py` - Edit and revalidate workflow
3. `tests/test_edit_integration.py` - Unit tests
4. `tests/test_edit_integration_flow.py` - Integration tests

### Modified Files
1. `src/jean_claude/cli/commands/work.py` - Added validation and edit integration

## State Management

Updated `agents/beads-jean_claude-2sz.7/state.json`:
- Marked `edit-task-integration` feature as completed
- Updated `current_feature_index` to 11
- Incremented `iteration_count` to 11
- Set `tests_passing` to true

## Next Steps

Feature 11 is now complete. The next feature in the workflow is:
- Feature 12: `clarifying-questions-generator` - Create ClarifyingQuestionsGenerator that analyzes vague task descriptions and generates relevant questions.

## Notes

This implementation follows TDD (Test-Driven Development) principles:
1. Tests were written first
2. Implementation was created to pass the tests
3. Integration was verified through comprehensive test coverage

The feature integrates seamlessly with existing validation infrastructure and provides a smooth user experience for improving task quality before starting work.
