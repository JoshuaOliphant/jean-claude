# Add Beads task validation

## Description

Validate Beads tasks before starting work to catch quality issues early. Poor task descriptions lead to poor implementations.

## Validation Checks
- Description length (warn if < 50 chars)
- Presence of acceptance criteria
- Mention of tests/verification
- Valid priority and type

## Behavior Options
```bash
jc work poc-abc123              # Warn but proceed
jc work poc-abc123 --strict     # Fail if validation warnings
```

## Warning Output
```
⚠️  Task may need more detail:
   - Description is only 12 words (recommend 50+)
   - No acceptance criteria found
   - No mention of tests

Options:
  [1] Proceed anyway (agent will make assumptions)
  [2] Open task for editing (bd edit poc-abc123)
  [3] Cancel
```

## Agent Clarification
If task is too vague, agent could generate clarifying questions before starting:
```
Before I start "Add auth", I have questions:
1. What auth mechanism? (JWT, sessions, OAuth)
2. What endpoints? (register, login, logout, reset)
3. Should I add tests?
```

## Context
- Validation runs in jc work before agent starts
- Could also be a standalone command: jc validate poc-abc123

## Acceptance Criteria

- Validation checks description quality
- Warns about missing acceptance criteria
- strict flag fails on warnings
- Interactive prompt for proceed/edit/cancel
- Agent can ask clarifying questions for vague tasks

---

## Task Metadata

- **Task ID**: jean_claude-2sz.7
- **Status**: open
- **Created**: 2025-12-23 19:00:59
- **Updated**: 2025-12-23 19:00:59
