---
name: jean-claude-cli
description: Expert guide for Jean Claude CLI - a sophisticated AI orchestration framework featuring two-agent workflows, event sourcing, coordinator pattern with ntfy.sh, agent note-taking, mailbox communication, and real-time monitoring. Use when user asks about jc commands, workflows, Beads integration, agent coordination, or Jean Claude architecture.
---

# Jean Claude CLI Expert

Expert knowledge for using Jean Claude CLI (`jc`), a sophisticated AI-driven development workflow orchestration framework.

## Architecture Overview

Jean Claude is a **two-layer orchestration framework**:

1. **Agentic Layer**: `.claude/commands/` slash commands for Claude Code
2. **Application Layer**: `src/jean_claude/` CLI tool with four subsystems:
   - `cli/` - Click-based command interface (14+ commands)
   - `core/` - Business logic (56+ modules)
   - `orchestration/` - Multi-agent workflow engine
   - `dashboard/` - FastAPI monitoring UI with SSE streaming

**Key Innovations**:
- Event-sourced architecture (SQLite + JSON state)
- Two-agent pattern (Opus plans → Sonnet implements)
- Coordinator pattern (agent-to-agent + agent-to-human communication)
- Worktree isolation (parallel execution)

## Core Commands

### `jc init`
Initialize Jean Claude in a project (run once).

**Creates**:
- `.jc-project.yaml` - Project configuration
- `.claude/skills/jean-claude-cli/` - This skill
- `specs/` - Workflow specifications directory
- `agents/` - Agent working directories

**Example**:
```bash
jc init
```

### `jc prompt "description"`
Execute a single prompt with Claude Agent SDK.

**When to use**:
- Quick one-off tasks
- Testing prompts
- Simple code generation without workflow overhead

**Options**:
- `--model opus|sonnet|haiku` - Choose model (default: sonnet)
- `--stream` - Show real-time output
- `--raw` - Return raw response without formatting

**Example**:
```bash
jc prompt "Add docstrings to all functions" --model sonnet --stream
```

### `jc workflow "description"`
Run two-agent workflow without Beads tracking.

**When to use**:
- Ad-hoc feature development
- Complex multi-step tasks requiring planning
- Tasks needing strategic + tactical execution

**Phases**:
1. **Planning** (Opus): Analyzes scope, creates feature list in state.json
2. **Implementation** (Sonnet): Implements features one by one with fresh context
3. **Verification**: Runs tests, checks completion

**Options**:
- `--initializer-model opus|sonnet` - Planning model (default: opus)
- `--coder-model opus|sonnet|haiku` - Implementation model (default: sonnet)
- `--max-iterations N` - Max iterations (default: 10)
- `--auto-continue` - Resume automatically if interrupted

**Example**:
```bash
jc workflow "Add user authentication with JWT tokens" --auto-continue
```

### `jc work <task-id>`
Execute a Beads task using two-agent workflow.

**When to use**:
- Working on Beads-tracked issues
- Feature development with external issue tracking
- Tasks requiring team coordination

**Process**:
1. Fetches task from Beads (`bd show <task-id>`)
2. Generates spec in `specs/beads-{task-id}.md`
3. Runs two-agent workflow (Opus plans → Sonnet implements)
4. Updates Beads task status
5. Verifies completion

**Example**:
```bash
jc work beads-abc123
```

### `jc note`
Agent note-taking system for persistent knowledge capture.

**When to use**:
- Capturing insights during workflow execution
- Documenting decisions and patterns
- Building institutional knowledge
- Sharing context across workflows

**Subcommands**:
- `jc note add "content"` - Add note (agents can use this proactively)
- `jc note list` - View all notes
- `jc note list --workflow <id>` - Notes for specific workflow
- `jc note search "query"` - Search note contents

**Agent Usage**:
Agents executing in workflows can proactively use the note-taking API to:
- Document architectural decisions
- Record trade-offs considered
- Share discoveries with future workflows
- Build project-specific knowledge base

**Example**:
```bash
# Human usage
jc note add "Using SQLAlchemy 2.0 async patterns for all DB access"
jc note list --workflow a3b4c5d6

# Agent usage (within workflow)
await note_taking_api.create_note(
    content="Discovered circular import in auth module",
    workflow_id=workflow_id,
    category="architecture"
)
```

### `jc prime`
Gather project context efficiently.

**When to use**:
- Starting work in new codebase
- After long break from project
- Before planning major changes

**Process**:
Uses fast Haiku model to explore codebase and return condensed summary (~500 words) covering:
- Tech stack
- Entry points
- Testing setup
- Architecture patterns

**Options**:
- `--raw` - Return raw markdown without formatting
- `--output <file>` - Save to file

**Example**:
```bash
jc prime --raw
```

### `jc status`
Check workflow status and progress.

**When to use**:
- Monitoring running workflows
- Checking feature completion
- Debugging stuck workflows

**Options**:
- `<workflow-id>` - Specific workflow (default: latest)
- `--json` - JSON output for scripting

**Example**:
```bash
jc status                    # Latest workflow
jc status a3b4c5d6          # Specific workflow
jc status --json | jq .      # Programmatic access
```

### `jc logs`
View workflow event logs.

**When to use**:
- Debugging workflow issues
- Auditing agent actions
- Real-time monitoring

**Options**:
- `<workflow-id>` - Specific workflow (default: latest)
- `--follow` - Follow mode (real-time, like `tail -f`)
- `--level debug|info|warning|error` - Filter by log level

**Example**:
```bash
jc logs --follow              # Real-time monitoring
jc logs a3b4c5d6             # Specific workflow
jc logs --level error         # Errors only
```

### `jc dashboard`
Launch web monitoring dashboard.

**When to use**:
- Visual workflow monitoring
- Team collaboration
- Real-time progress tracking

**Features**:
- Live SSE streaming (no polling)
- Event timeline visualization
- Feature progress tracking
- Cost and duration metrics
- Multi-workflow monitoring

**Example**:
```bash
jc dashboard                  # Launches on http://localhost:8000
```

Access dashboard in browser to see:
- Real-time event stream
- Workflow state (features, phases, costs)
- Agent communication logs
- Test results and validation

### `jc migrate`
Update existing project to latest Jean Claude version.

**When to use**:
- After upgrading Jean Claude
- Adopting new features
- Syncing project structure

**Process**:
- Creates missing directories
- Adds new slash commands
- **Updates jean-claude-cli skill** with latest features
- Updates CLAUDE.md section
- Does NOT overwrite existing files

**Options**:
- `--dry-run` - Preview changes without applying

**Example**:
```bash
jc migrate --dry-run          # Preview
jc migrate                    # Apply updates
```

## Two-Agent Pattern

Jean Claude's core innovation: **strategic planning with tactical execution**.

### Architecture

1. **Initializer Agent (Opus)**:
   - Analyzes scope ONCE
   - Creates feature list as JSON
   - Writes to `agents/{workflow-id}/state.json`
   - Expensive but thorough

2. **Coder Agent (Sonnet)**:
   - Loops through feature list
   - Implements ONE feature per iteration
   - Gets FRESH context each iteration (prevents bloat)
   - Verifies after each feature
   - Cheap and efficient

3. **Shared State**:
   - `agents/{workflow-id}/state.json` - Single source of truth
   - Features: `not_started` → `in_progress` → `completed`
   - Phases: `planning` → `implementing` → `verifying` → `complete`
   - Event log: `agents/{workflow-id}/events.jsonl`

### Benefits

- **Cost-effective**: Expensive model only for planning
- **Context management**: Fresh context per feature prevents bloat
- **Quality**: Strategic planning + focused execution
- **Resumable**: Crash recovery from state.json
- **Auditable**: Complete event log

### State Management

**WorkflowState structure** (`agents/{workflow-id}/state.json`):
```json
{
  "workflow_id": "a3b4c5d6",
  "features": [
    {
      "id": "feat-1",
      "name": "Add JWT authentication",
      "status": "completed",
      "description": "...",
      "verification": "..."
    }
  ],
  "current_phase": "implementing",
  "costs": {"initializer": 0.45, "coder": 1.23},
  "session_ids": ["sess-1", "sess-2"]
}
```

## Event Sourcing Architecture

Jean Claude uses **event sourcing** for complete auditability and crash recovery.

### Event Store

**Dual persistence**:
1. **SQLite database** (`.jc/events.db`) - Centralized, queryable
2. **JSONL files** (`agents/{workflow-id}/events.jsonl`) - Per-workflow append-only log

**Event types**:
- `workflow_started`, `workflow_completed`
- `feature_started`, `feature_completed`
- `agent_invocation`, `agent_response`
- `test_run`, `validation_check`
- `error_detected`, `blocker_detected`
- `message_sent`, `message_received`
- `note_created`, `note_updated`

### Snapshots

Every 100 events, system creates **snapshot** for bounded replay:
- Current workflow state
- Feature completion status
- Agent session history
- Cost accumulation

**Benefits**:
- Instant crash recovery
- Complete audit trail
- Deterministic replay
- Performance optimization

### Querying Events

```bash
# Via CLI
jc logs a3b4c5d6 --level error

# Via SQLite
sqlite3 .jc/events.db "SELECT * FROM events WHERE workflow_id='a3b4c5d6'"

# Via dashboard
jc dashboard  # Real-time event stream
```

## Coordinator Pattern

Jean Claude implements **hierarchical agent coordination** with human-in-the-loop escalation.

### Architecture

```
Main Claude Code (Coordinator)
    ↓
Subagents (Initializer, Coder, etc.)
    ↓
Mailbox Tools (ask_user, notify_user)
    ↓
Coordinator Triage (90% auto-answer, 10% escalate)
    ↓
ntfy.sh (Mobile notifications)
    ↓
Human Response
```

### Mailbox Communication

**Location**: `agents/{workflow-id}/INBOX/` and `OUTBOX/`

**Message format**:
```json
{
  "id": "msg-abc123",
  "from": "coder-agent",
  "to": "coordinator",
  "priority": "normal",
  "question": "Should I use SQLite or PostgreSQL?",
  "context": {"feature_id": "feat-2"},
  "created_at": "2026-01-03T12:34:56Z"
}
```

**Priorities**:
- `LOW` - FYI, non-blocking
- `NORMAL` - Needs answer within 1 hour
- `URGENT` - Critical decision, blocks progress
- `CRITICAL` - Safety/security concern

### Coordinator Triage

**Automatic answers (90%)**:
- Questions answerable from codebase
- Decisions matching existing patterns
- Simple clarifications

**Escalated to human (10%)**:
- Architectural decisions
- Business logic choices
- Security/compliance questions
- Ambiguous requirements

### ntfy.sh Integration

**Setup**:
```bash
# .env configuration
export JEAN_CLAUDE_NTFY_TOPIC="your-escalation-topic"
export JEAN_CLAUDE_NTFY_RESPONSE_TOPIC="your-response-topic"
```

**Notification format**:
```
[project-name] Question from Coder Agent

Workflow: a3b4c5d6
Feature: Add authentication

Question: Should I implement OAuth2 or JWT tokens?
Context: User mentioned "simple auth" but didn't specify protocol.

Reply with: a3b4c5d6: your response
```

**Response format** (from phone):
```
a3b4c5d6: Use JWT tokens for simplicity
```

**Multi-project support**:
All projects share same ntfy topics. Workflow ID ensures correct routing:
```
Project A (jean-claude):      a3b4c5d6
Project B (my-api-server):    f8e2a1b9
Project C (website):          2c7d9e4a

# You receive:
[jean-claude] Architecture Question
[my-api-server] Should I add rate limiting?
[website] Use SQLite or Postgres?

# You respond:
a3b4c5d6: Use the pattern from existing code
f8e2a1b9: Yes, add rate limiting
2c7d9e4a: Use Postgres
```

### Polling Pattern

**Coordinators poll for responses** (not blocking):
```python
max_attempts = 30  # 30 attempts × 10 seconds = 5 minutes
for attempt in range(max_attempts):
    time.sleep(10)  # Poll every 10 seconds

    responses = poll_ntfy_responses()
    matching = [r for r in responses if r['workflow_id'] == workflow_id]

    if matching:
        response = matching[0]['response']
        break
else:
    # Timeout - proceed with default or pause workflow
    handle_timeout()
```

**Why polling?**:
- Respects asynchronous nature of mobile communication
- Allows human time to think
- Provides clear timeout behavior
- Shows progress during wait

## Beads Integration

Jean Claude integrates with Beads issue tracker for project-wide task management.

### Beads Workflow

```bash
# 1. Find available work
bd ready                           # Show tasks with no blockers

# 2. Execute task
jc work beads-abc123              # Two-agent workflow

# 3. Close when done
bd close beads-abc123             # Mark complete
```

### Finding Work

```bash
bd ready                          # Available tasks (no blockers)
bd list --status=open             # All open tasks
bd list --status=in_progress      # Your active work
bd show beads-abc123              # Detailed task view
```

### Creating Tasks

```bash
# Create task
bd create \
  --title="Add feature X" \
  --type=feature \
  --priority=2                    # 0-4 or P0-P4 (0=critical, 4=backlog)

# Add dependencies
bd dep add beads-yyy beads-xxx   # yyy depends on xxx (xxx blocks yyy)
```

### Closing Tasks

```bash
bd close beads-abc123                              # Single task
bd close beads-abc beads-def beads-xyz            # Batch (efficient!)
bd close beads-abc --reason="Completed in PR #42" # With reason
```

### Sync and Collaboration

```bash
bd sync                           # Push to git remote
bd sync --status                  # Check sync status
bd stats                          # Project statistics
bd doctor                         # Check for issues
```

### Spec Generation

When running `jc work <task-id>`, Jean Claude:
1. Fetches task details: `bd show <task-id>`
2. Generates spec: `specs/beads-{task-id}.md`
3. Renders with Jinja2 template
4. Passes spec to Initializer agent

**Spec template** (`src/jean_claude/templates/beads_spec.md`):
```markdown
# {{ title }}

**Task ID**: {{ task_id }}
**Type**: {{ type }}
**Priority**: {{ priority }}

## Description
{{ description }}

## Acceptance Criteria
{{ acceptance_criteria }}

## Dependencies
{% for dep in dependencies %}
- {{ dep }}
{% endfor %}
```

## Advanced Features

### Auto-Continue

Autonomous continuation loop with error recovery.

**When to use**:
- Long-running workflows
- Unattended execution
- Large migrations/refactorings

**How it works**:
1. Coder implements feature
2. Runs tests automatically
3. If tests fail:
   - Detects error type
   - Attempts automatic fix
   - Retries (max 3 attempts)
4. If tests pass:
   - Moves to next feature
5. If blocked:
   - Writes message to INBOX
   - Waits for coordinator

**Options**:
```bash
jc workflow "Large refactoring" \
  --auto-continue \
  --max-iterations 50
```

**Error detection**:
- Test failures (`test_failure_detector.py`)
- Ambiguity detection (`ambiguity_detector.py`)
- Blocker detection (`blocker_detector.py`)
- Runtime errors (`error_detector.py`)

### Verification System

**After each feature**:
1. Runs test command (`uv run pytest`)
2. Parses output for failures
3. If failures:
   - Logs to event store
   - Triggers auto-continue retry
   - Or escalates to coordinator
4. If success:
   - Marks feature complete
   - Proceeds to next feature

**Test commands** (`.jc-project.yaml`):
```yaml
tooling:
  test_command: uv run pytest
  linter_command: uv run ruff check .
  format_command: uv run ruff format .
```

### Worktree Isolation

**Future feature**: Each workflow executes in isolated git worktree.

**Benefits**:
- Parallel workflow execution
- No branch conflicts
- Clean commit history
- Easy rollback

**Planned structure**:
```
trees/
├── workflow-a3b4c5d6/    # Isolated worktree
│   └── .git              # Linked to main repo
└── workflow-f8e2a1b9/    # Another workflow
    └── .git
```

### Security Hooks

Jean Claude validates all bash commands before execution.

**Validation** (`src/jean_claude/core/security.py`):
- Dangerous commands (rm -rf /, dd, mkfs)
- Unquoted variables in rm/mv
- Eval/exec with user input
- Network commands to internal IPs

**Override** (if needed):
```python
# In workflow state
"security": {
  "allow_dangerous": false,
  "allowed_commands": ["rm -rf node_modules"]
}
```

## Dashboard & Monitoring

### Web Dashboard

```bash
jc dashboard              # Launches on http://localhost:8000
```

**Features**:
- Real-time SSE streaming (no polling, zero latency)
- Event timeline with filtering
- Feature progress visualization
- Cost tracking (per agent, per feature)
- Duration metrics
- Multi-workflow support

**Tech stack**:
- FastAPI + Uvicorn
- sse-starlette for live updates
- Jinja2 templates
- SQLite event queries

### Event Streaming

**Server-Sent Events** provide zero-latency updates:
```javascript
// Browser connects to /events stream
const eventSource = new EventSource('/events');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update UI in real-time
};
```

**Event types streamed**:
- Feature started/completed
- Test results
- Agent messages
- Cost updates
- Error/blocker detection

### Cost Tracking

**Tracked per workflow**:
```json
{
  "costs": {
    "initializer": 0.45,      // Opus planning
    "coder": 1.23,            // Sonnet implementation
    "total": 1.68
  },
  "tokens": {
    "input": 125000,
    "output": 45000
  }
}
```

Access via:
- `jc status --json | jq .costs`
- Dashboard cost panel
- Event store queries

## Configuration

### Project Config (`.jc-project.yaml`)

```yaml
directories:
  specs: specs/              # Workflow specifications
  agents: agents/            # Agent working directories (state.json)
  trees: trees/              # Git worktrees (future)
  source: src/
  tests: tests/

tooling:
  test_command: uv run pytest
  linter_command: uv run ruff check .
  format_command: uv run ruff format .

workflows:
  default_model: sonnet      # sonnet|opus|haiku
  auto_commit: true          # Auto-commit after features
  max_iterations: 10

vcs:
  issue_tracker: beads       # beads|github
  platform: github           # github|gitlab
```

### Environment Variables

**Authentication**:
```bash
ANTHROPIC_API_KEY=sk-...           # Optional (not needed for Claude Max)
CLAUDE_CODE_USE_BEDROCK=1          # Use AWS Bedrock backend
AWS_PROFILE=default                # Bedrock credentials
AWS_REGION=us-east-1
```

**Project**:
```bash
ADW_ISSUE_TRACKER=beads            # beads|github
ADW_MODEL_SET=base                 # base (sonnet) | advanced (opus)
LOG_LEVEL=INFO                     # DEBUG|INFO|WARNING|ERROR|CRITICAL
```

**Notifications**:
```bash
JEAN_CLAUDE_NTFY_TOPIC=escalation-topic
JEAN_CLAUDE_NTFY_RESPONSE_TOPIC=response-topic
```

## Common Workflows

### Feature Development with Beads

```bash
# 1. Create task
bd create --title="Add user authentication" --type=feature --priority=2

# 2. Execute with two-agent workflow
jc work beads-auth123 --auto-continue

# 3. Monitor progress
jc logs --follow

# 4. Verify
uv run pytest tests/
jc status

# 5. Close task
bd close beads-auth123
```

### Ad-hoc Feature Development

```bash
# Direct workflow without Beads
jc workflow "Add user authentication with JWT" --auto-continue

# Monitor in dashboard
jc dashboard

# Check status
jc status --json
```

### Quick Refactoring

```bash
jc prompt "Refactor module X to use async/await" --model sonnet --stream
```

### Large Migration

```bash
jc workflow "Migrate from SQLAlchemy 1.4 to 2.0" \
  --initializer-model opus \
  --coder-model sonnet \
  --auto-continue \
  --max-iterations 30
```

### Agent Note-Taking During Workflow

**Agents proactively capture knowledge**:
```python
# Within workflow execution
await note_taking_api.create_note(
    content="Using Redis pub/sub for real-time features",
    workflow_id=workflow_id,
    category="architecture"
)
```

**Review notes later**:
```bash
jc note list --workflow a3b4c5d6
jc note search "Redis"
```

### Multi-Project Coordination

**Run workflows across projects**:
```bash
# Terminal 1: Project A
cd ~/projects/jean-claude
jc workflow "Add feature X" --auto-continue

# Terminal 2: Project B
cd ~/projects/my-api
jc workflow "Add feature Y" --auto-continue

# Terminal 3: Project C
cd ~/projects/website
jc workflow "Add feature Z" --auto-continue
```

**Phone receives**:
```
[jean-claude] Architecture Question (workflow: a3b4c5d6)
[my-api] Database choice? (workflow: f8e2a1b9)
[website] Use REST or GraphQL? (workflow: 2c7d9e4a)
```

**Respond with workflow IDs**:
```
a3b4c5d6: Use pattern from existing code
f8e2a1b9: Use PostgreSQL
2c7d9e4a: Use REST for simplicity
```

## Troubleshooting

### Workflow Stuck

```bash
# Check status
jc status

# View logs
jc logs --follow

# Check for agent questions
ls agents/*/INBOX/

# Read messages
cat agents/a3b4c5d6/INBOX/msg-*.json

# Respond via coordinator or manually
```

### Beads Sync Issues

```bash
bd doctor                 # Check for issues
bd sync --status          # Check sync status
bd sync                   # Force sync
```

### Event Store Corruption

```bash
# Rebuild from JSONL logs
jc doctor --rebuild-events

# Verify integrity
sqlite3 .jc/events.db "PRAGMA integrity_check"
```

### Dashboard Not Updating

```bash
# Check SSE connection
curl http://localhost:8000/events

# Restart dashboard
pkill -f "jc dashboard"
jc dashboard
```

### ntfy.sh Notifications Not Working

```bash
# Test topic
curl -d "Test message" ntfy.sh/your-topic

# Check environment variables
echo $JEAN_CLAUDE_NTFY_TOPIC
echo $JEAN_CLAUDE_NTFY_RESPONSE_TOPIC

# Test from CLI
jc test-ntfy "Test escalation"
```

### High Costs

```bash
# Check workflow costs
jc status --json | jq .costs

# Use cheaper models
jc workflow "..." --coder-model haiku

# Reduce iterations
jc workflow "..." --max-iterations 5
```

## Key Concepts

- **Workflow ID**: Unique 8-char UUID per workflow (e.g., `a3b4c5d6`)
- **State JSON**: `agents/{workflow-id}/state.json` - single source of truth
- **Feature List**: Initializer creates, Coder implements one-by-one
- **Context Reset**: Fresh context per feature prevents bloat
- **Event Sourcing**: Immutable event log for auditability
- **Coordinator**: Main Claude Code instance managing subagents
- **Mailbox**: INBOX/OUTBOX for agent-to-agent communication
- **Escalation**: 10% of questions go to human via ntfy.sh
- **Snapshot**: Every 100 events for bounded replay
- **Verification**: Tests after each feature
- **Auto-continue**: Autonomous error recovery loop

## Best Practices

1. **Use Beads for tracking**: All significant work should have task ID
2. **Close tasks in batches**: `bd close task1 task2 task3` (efficient)
3. **Enable auto-continue for large tasks**: Unattended execution
4. **Let coordinator handle questions**: Don't interrupt workflows manually
5. **Respond promptly to escalations**: Coordinators timeout after 30 minutes
6. **Monitor via dashboard**: Real-time visibility beats polling
7. **Review notes regularly**: Build institutional knowledge
8. **Use appropriate models**: Haiku for simple tasks, Opus for complex planning
9. **Verify before closing**: Tests pass and feature works
10. **Keep workflow IDs handy**: Needed for multi-project responses

## Architecture Deep Dives

### Two-Agent State Machine

```
┌─────────────────┐
│ Workflow Start  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Initializer     │ (Opus, once)
│ - Analyze scope │
│ - Create list   │
│ - Write state   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Coder Loop      │ (Sonnet, N times)
│ For each feat:  │
│ - Read state    │
│ - Fresh context │
│ - Implement     │
│ - Test          │
│ - Update state  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Verification    │
│ - All tests pass│
│ - Features done │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Workflow End    │
└─────────────────┘
```

### Event Sourcing Flow

```
┌────────────┐     ┌──────────────┐     ┌─────────────┐
│ Workflow   │────▶│ Event        │────▶│ SQLite DB   │
│ Action     │     │ Emission     │     │ + JSONL     │
└────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Snapshot     │ (every 100 events)
                   │ Creation     │
                   └──────────────┘
                           │
                           ▼
                   ┌──────────────┐
                   │ Dashboard    │ (SSE stream)
                   │ Update       │
                   └──────────────┘
```

### Coordinator Communication Flow

```
┌─────────────┐
│ Subagent    │
│ needs help  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ ask_user()      │
│ writes to INBOX │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Coordinator     │────┐
│ reads INBOX     │    │ 90% auto-answer
└──────┬──────────┘    │ from codebase
       │               └─────────────┐
       │ 10% escalate                │
       ▼                             ▼
┌─────────────────┐          ┌──────────────┐
│ ntfy.sh         │          │ write to     │
│ notification    │          │ OUTBOX       │
└──────┬──────────┘          └──────────────┘
       │
       ▼
┌─────────────────┐
│ Human phone     │
│ responds        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Coordinator     │
│ polls response  │
│ writes to       │
│ OUTBOX          │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Subagent reads  │
│ OUTBOX          │
│ continues work  │
└─────────────────┘
```

## Resources

- **Documentation**: `docs/` directory
  - `two-agent-workflow.md` - Opus→Sonnet pattern details
  - `auto-continue-workflow.md` - Error recovery loops
  - `coordinator-pattern.md` - Agent communication
  - `event-store-architecture.md` - Event sourcing design
  - `beads-workflow.md` - Issue tracker integration
  - `streaming-implementation-summary.md` - SSE architecture

- **Templates**: `src/jean_claude/templates/`
  - `beads_spec.md` - Jinja2 template for Beads tasks

- **Skills**: `.claude/skills/`
  - `jean-claude-cli/` - This skill

- **Project Config**: `.jc-project.yaml` - Project-specific settings

---

**Remember**: Jean Claude orchestrates workflows, not just tasks. The two-agent pattern provides strategic planning with tactical execution. Event sourcing ensures auditability. The coordinator pattern scales agent autonomy while keeping humans in the loop for critical decisions.
