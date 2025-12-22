# Two-Agent Workflow Pattern

The two-agent workflow is Jean Claude's implementation of Anthropic's autonomous coding quickstart pattern for handling complex, long-running development tasks.

## Overview

The two-agent pattern splits complex work into two specialized agents:

1. **Initializer Agent** (Planning) - Runs once at start
   - Uses Opus by default (better at architecture and planning)
   - Analyzes the entire task scope
   - Creates comprehensive feature breakdown
   - Defines all test cases upfront
   - Saves plan to `WorkflowState`

2. **Coder Agent** (Execution) - Runs in loop until complete
   - Uses Sonnet by default (faster, cost-effective for coding)
   - Reads `WorkflowState` each iteration
   - Implements ONE feature at a time
   - Runs verification tests before new work
   - Updates state after completion
   - Fresh context each iteration

## Why This Pattern Works

### Context Window Efficiency

Instead of maintaining a growing context with hundreds of messages, each coding session starts fresh:

```
Session 1: Read state → Implement Feature 1 → Update state
Session 2: Read state → Implement Feature 2 → Update state
Session 3: Read state → Implement Feature 3 → Update state
...
```

The state file serves as shared memory between sessions, eliminating the need to remember previous work.

### Better Model Selection

Different tasks require different capabilities:

- **Planning** requires architectural thinking → Opus excels here
- **Coding** requires speed and accuracy → Sonnet is cost-effective

By splitting the work, you get the best of both models.

### Verification-First Approach

Before starting new work, the coder agent:

1. Reads the state file
2. Runs ALL existing tests
3. Fixes any failures before proceeding
4. Only then implements the next feature

This prevents regression cascades and ensures quality.

## Usage

### Basic Usage

```bash
jc workflow "Build a user authentication system with JWT and OAuth2"
```

This will:
1. Call Opus to create a feature breakdown
2. Show you the plan
3. Ask for confirmation
4. Execute features one by one with Sonnet

### Custom Workflow ID

```bash
jc workflow "Add logging middleware" --workflow-id auth-logging
```

Use custom IDs for easier tracking and organization.

### Model Selection

```bash
# Use Opus for both (slower, higher quality)
jc workflow "Complex architecture" -i opus -c opus

# Use Haiku for simple tasks (faster, cheaper)
jc workflow "Add docstrings" -i haiku -c haiku

# Default: Opus plans, Sonnet codes (recommended)
jc workflow "Standard feature"
```

### Auto-Confirm

```bash
# Skip confirmation prompt (useful for automation)
jc workflow "Simple task" --auto-confirm
```

### Custom Working Directory

```bash
jc workflow "Add tests" --working-dir /path/to/project
```

## State Management

The workflow state is saved to `agents/{workflow_id}/state.json`:

```json
{
  "workflow_id": "two-agent-abc12345",
  "workflow_name": "Build authentication system",
  "workflow_type": "two-agent",
  "features": [
    {
      "name": "user-model",
      "description": "Create User model with SQLAlchemy",
      "status": "completed",
      "test_file": "tests/test_user_model.py",
      "tests_passing": true,
      "started_at": "2025-12-21T10:00:00",
      "completed_at": "2025-12-21T10:05:00"
    },
    {
      "name": "jwt-tokens",
      "description": "Implement JWT token generation and validation",
      "status": "in_progress",
      "test_file": "tests/test_jwt.py",
      "tests_passing": false,
      "started_at": "2025-12-21T10:05:00"
    },
    {
      "name": "oauth-integration",
      "description": "Add OAuth2 support for Google and GitHub",
      "status": "not_started",
      "test_file": "tests/test_oauth.py"
    }
  ],
  "current_feature_index": 1,
  "iteration_count": 2,
  "max_iterations": 9,
  "progress_percentage": 33.3,
  "total_cost_usd": 0.45,
  "total_duration_ms": 125000
}
```

## Feature Breakdown Best Practices

The initializer agent follows these guidelines:

### Small Features

Each feature should be max **100 lines of code**:

✅ Good:
```json
{
  "name": "basic-validation",
  "description": "Add email and username validation to User model",
  "test_file": "tests/test_user_validation.py"
}
```

❌ Too large:
```json
{
  "name": "complete-auth-system",
  "description": "Build entire authentication with login, registration, OAuth, and password reset",
  "test_file": "tests/test_auth.py"
}
```

### Independent Features

Features should be self-contained when possible:

✅ Good (independent):
```json
[
  {"name": "password-hashing", "description": "..."},
  {"name": "email-validation", "description": "..."}
]
```

❌ Bad (tightly coupled):
```json
[
  {"name": "part-1-of-login", "description": "..."},
  {"name": "part-2-of-login", "description": "..."}
]
```

### Dependency Order

List features in dependency order:

✅ Good:
```json
[
  {"name": "user-model", "description": "Create User model"},
  {"name": "user-repository", "description": "Implement UserRepository (uses User model)"},
  {"name": "auth-service", "description": "Create AuthService (uses UserRepository)"}
]
```

### Test Coverage

Every feature MUST have a test file:

✅ Good:
```json
{
  "name": "jwt-tokens",
  "test_file": "tests/test_jwt.py"
}
```

❌ Missing tests:
```json
{
  "name": "jwt-tokens",
  "test_file": null
}
```

## Resuming Workflows

If a workflow is interrupted or fails, you can resume it:

```bash
# The workflow will tell you the command to resume
jc run agents/two-agent-abc12345/state.json
```

The coder will pick up from the last incomplete feature.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  CLI Command: jc workflow "description"         │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│  run_two_agent_workflow()                       │
│  ├─ Phase 1: Initializer                        │
│  └─ Phase 2: Coder (auto-continue loop)         │
└───┬────────────────────────────────────────┬────┘
    │                                        │
    ▼                                        ▼
┌─────────────────────┐          ┌────────────────────────┐
│  run_initializer()  │          │  run_auto_continue()   │
│  ├─ Execute prompt  │          │  ├─ Loop until done    │
│  ├─ Parse JSON      │          │  ├─ Verify tests       │
│  ├─ Create state    │          │  ├─ Execute feature    │
│  └─ Save to disk    │          │  └─ Update state       │
└──────────┬──────────┘          └───────────┬────────────┘
           │                                 │
           ▼                                 ▼
     ┌────────────────────────────────────────────┐
     │  agents/{workflow_id}/state.json           │
     │  (Shared state between agents)             │
     └────────────────────────────────────────────┘
```

## Security

The two-agent workflow respects all Jean Claude security settings:

- **Security hooks** validate bash commands before execution
- **Tool permissions** limit what agents can access
- **Workflow types** (`readonly`, `development`, `testing`) control allowlists
- **Verification-first** prevents deploying broken code

See [CLAUDE.md](../CLAUDE.md#security-configuration) for security details.

## Examples

### Simple Feature

```bash
jc workflow "Add a health check endpoint to the FastAPI application"
```

**Initializer might create:**
```json
{
  "features": [
    {
      "name": "health-endpoint",
      "description": "Create /health endpoint that returns 200 OK with timestamp",
      "test_file": "tests/test_health.py"
    },
    {
      "name": "health-dependencies",
      "description": "Add database and Redis connection checks to health endpoint",
      "test_file": "tests/test_health_deps.py"
    }
  ]
}
```

### Complex System

```bash
jc workflow "Build a notification system with email, SMS, and push notifications"
```

**Initializer might create:**
```json
{
  "features": [
    {
      "name": "notification-models",
      "description": "Create Notification, NotificationTemplate, and NotificationLog models",
      "test_file": "tests/test_notification_models.py"
    },
    {
      "name": "email-provider",
      "description": "Implement EmailProvider using SendGrid API",
      "test_file": "tests/test_email_provider.py"
    },
    {
      "name": "sms-provider",
      "description": "Implement SMSProvider using Twilio API",
      "test_file": "tests/test_sms_provider.py"
    },
    {
      "name": "push-provider",
      "description": "Implement PushProvider using Firebase Cloud Messaging",
      "test_file": "tests/test_push_provider.py"
    },
    {
      "name": "notification-service",
      "description": "Create NotificationService that routes to appropriate provider",
      "test_file": "tests/test_notification_service.py"
    },
    {
      "name": "notification-api",
      "description": "Add FastAPI endpoints for sending notifications",
      "test_file": "tests/test_notification_api.py"
    },
    {
      "name": "notification-templates",
      "description": "Add Jinja2 template support for notification content",
      "test_file": "tests/test_notification_templates.py"
    }
  ]
}
```

## Comparison to Other Workflows

### Two-Agent vs. Single Prompt

| Aspect | Single Prompt | Two-Agent |
|--------|--------------|-----------|
| **Context Usage** | All messages in one session | Fresh context each feature |
| **Cost** | Can exceed limits on large tasks | Scales to any size |
| **Planning** | Inline with coding | Separate planning phase |
| **Resume** | Difficult | Easy (read state file) |
| **Visibility** | All or nothing | Feature-by-feature progress |

### Two-Agent vs. ADW Slash Commands

| Aspect | Slash Commands | Two-Agent |
|--------|---------------|-----------|
| **Use Case** | Templated workflows | Open-ended tasks |
| **Feature Breakdown** | Manual | Automatic |
| **Planning** | Human-defined | AI-defined |
| **Iteration** | Single execution | Multi-iteration loop |

## Troubleshooting

### Initializer Returns Invalid JSON

**Symptom:** `ValueError: Initializer output is not valid JSON`

**Fix:** The initializer prompt is designed to output only JSON, but sometimes Claude adds extra text. The code handles markdown code blocks automatically. If it still fails, check `agents/{workflow_id}/initializer/` for the raw output.

### Features Too Large

**Symptom:** Coder takes too long on one feature

**Fix:** The initializer should break features into ~100 line chunks. If it doesn't, you can manually edit `agents/{workflow_id}/state.json` to split the feature.

### Tests Keep Failing

**Symptom:** Verification fails repeatedly

**Fix:** The coder will attempt to fix failing tests before moving on. If it can't, check:
1. Is the test file path correct?
2. Are there dependency issues?
3. Is the feature too complex?

You can manually fix tests and update the state file to mark them passing.

### Workflow Stuck

**Symptom:** Coder doesn't advance to next feature

**Fix:** Check `agents/{workflow_id}/state.json`:
- Is `current_feature_index` advancing?
- Are features marked as `completed`?
- Is `iteration_count` increasing?

You can manually edit the state to skip a feature or reset progress.

## References

- [Anthropic Autonomous Coding Quickstart](https://github.com/anthropics/anthropic-quickstarts/tree/main/autonomous-coding)
- [Autonomous Agent Patterns](./autonomous-agent-patterns.md)
- [Auto-Continue Orchestration](../src/jean_claude/orchestration/auto_continue.py)
- [Two-Agent Implementation](../src/jean_claude/orchestration/two_agent.py)
