# Plan TDD

Break down large specifications into focused TDD tasks following the test-first approach.

## Variables
adw_id: $1
spec_file: $2

## Instructions

- Read the specification file from `spec_file` variable
- Break down the spec into small, focused TDD tasks
- Each task should follow the Red-Green-Refactor cycle
- Create individual task files in `specs/tdd/` directory
- Each task file should be named: `tdd-{adw_id}-{task_number}-{descriptive-name}.md`
- Tasks should be ordered from foundational to specific
- Each task should be completable in 15-30 minutes
- Focus on one test case per task where possible

## Codebase Structure

- `README.md` - Project overview and instructions
- `adws/` - AI Developer Workflow scripts and modules
- `specs/` - Specification and plan documents
- `specs/tdd/` - TDD task breakdown files
- `pyproject.toml` - Python project configuration

## TDD Task Format

```md
# TDD Task {task_number}: <task name>

## Metadata
adw_id: `{adw_id}`
parent_spec: `{spec_file}`
task_number: `{task_number}`

## Test Case
<describe the specific test case to write>

## Red Phase (Write Failing Test)
<describe the test to write that will fail>

## Green Phase (Make It Pass)
<describe the minimal implementation to make the test pass>

## Refactor Phase (Clean Up)
<describe any refactoring needed after the test passes>

## Files to Modify
<list files that will be modified in this task>

## Validation
- Run the test and verify it fails (Red)
- Implement the solution and verify it passes (Green)
- Refactor if needed and verify tests still pass (Refactor)
```

## Report

Return a summary of the TDD tasks created:
- Total number of tasks
- List of task file paths created
- Recommended execution order
