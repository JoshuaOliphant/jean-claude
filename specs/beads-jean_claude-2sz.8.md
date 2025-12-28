# Feature-to-commit integration

## Description

Ensure each completed feature results in a well-formed git commit with Beads traceability.

## Commit Message Format
```
feat(auth): create User model with password hashing

- Add User model with email, hashed_password fields
- Create Alembic migration for users table
- Implement bcrypt password hashing utility

Beads: jean_claude-abc123
Feature: 1/4
```

## Commit Workflow
1. Feature implementation completes
2. Run tests to verify
3. Stage relevant files (agent determines which)
4. Generate commit message following conventional commits
5. Include Beads task ID as trailer
6. Include feature number for context

## Agent Guidance
Prompt should instruct agent to:
- Use conventional commit prefixes (feat, fix, refactor, test, docs)
- Scope to the feature area (auth, api, models)
- Write meaningful commit body
- Always include Beads trailer

## Context
- Agent already has git access via Bash tool
- Should integrate with existing commit patterns
- Don't commit if tests fail

## Acceptance Criteria

- Each feature produces exactly one commit
- Commit messages follow conventional commits format
- Beads task ID included as trailer
- Feature number included for ordering
- Tests must pass before commit
- Commit only relevant files (not entire worktree)

---

## Task Metadata

- **Task ID**: jean_claude-2sz.8
- **Status**: in_progress
- **Created**: 2025-12-23 19:01:24
- **Updated**: 2025-12-26 09:16:42
