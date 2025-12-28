# Chore Planning

Create a plan to complete the chore using the specified markdown `Plan Format`. Research the codebase and create a thorough plan.

## Variables
adw_id: $1
prompt: $2

## Instructions

- If the adw_id or prompt is not provided, stop and ask the user to provide them.
- Create a plan to complete the chore described in the `prompt`
- The plan should be simple, thorough, and precise
- Create the plan in the `specs/` directory with filename: `chore-{adw_id}-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short, descriptive name based on the chore (e.g., "update-readme", "add-logging", "refactor-agent")
- Research the codebase starting with `README.md`
- Replace every <placeholder> in the `Plan Format` with the requested value

## Codebase Structure

- `README.md` - Project overview and instructions (start here)
- `src/jean_claude/` - Main application code
- `src/jean_claude/cli/` - CLI commands
- `src/jean_claude/core/` - Core modules (agent, SDK executor, state)
- `src/jean_claude/orchestration/` - Workflow orchestration
- `tests/` - Test suite
- `.claude/commands/` - Claude command templates
- `specs/` - Specification and plan documents
- `pyproject.toml` - Python project configuration

## Plan Format

```md
# Chore: <chore name>

## Metadata
adw_id: `{adw_id}`
prompt: `{prompt}`

## Chore Description
<describe the chore in detail based on the prompt>

## Relevant Files
Use these files to complete the chore:

<list files relevant to the chore with bullet points explaining why. Include new files to be created under an h3 'New Files' section if needed>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers with bullet points. Start with foundational changes then move to specific changes. Last step should validate the work>

### 1. <First Task Name>
- <specific action>
- <specific action>

### 2. <Second Task Name>
- <specific action>
- <specific action>

## Validation Commands
Execute these commands to validate the chore is complete:

<list specific commands to validate the work. Be precise about what to run>
- Example: `uv run pytest tests/` - Run tests to validate the implementation

**Note:** If you create temporary verification scripts or status reports during implementation:
- Put verification scripts (check_*.py, demo_*.py) in `.jc/temp/`
- Put status reports (*_COMPLETE.md, *_VERIFICATION.md) in `.jc/reports/`
- Do NOT create these files in the project root

## Notes
<optional additional context or considerations>
```

## Chore
Use the chore description from the `prompt` variable.

## Report

Return the path to the plan file created.
