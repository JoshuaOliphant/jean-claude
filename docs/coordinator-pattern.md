# Coordinator Pattern for Agent Communication

## Overview

Jean Claude implements a **coordinator pattern** where the main Claude Code instance acts as a proxy between sub-agents and the human user. This enables:

- **Intelligent triage** - Claude Code answers most agent questions automatically
- **Reduced noise** - Humans only get notified for critical decisions
- **Faster workflows** - No waiting for human response on routine questions
- **Human-in-the-loop when needed** - Critical decisions still get human judgment

## Architecture

```
┌─────────────┐
│   Agent     │  (sub-agent running task)
│  (Sonnet)   │
└──────┬──────┘
       │ ask_user("How do I handle this test failure?")
       ↓
┌──────────────────────┐
│      INBOX           │  (filesystem-based message queue)
│  inbox.jsonl         │
└──────┬───────────────┘
       │ monitors
       ↓
┌──────────────────────────────┐
│   Coordinator (Claude Code)  │  (main instance)
│                              │
│  Decision:                   │
│   ├─ Answer myself? → OUTBOX │
│   └─ Escalate? → ntfy human │
└──────┬───────────────────────┘
       │
       ├─ Most cases: writes to OUTBOX
       │               (agent continues immediately)
       │
       └─ Critical only: escalate_to_human()
                         (sends ntfy push notification)
                         ↓
                   ┌──────────────┐
                   │  Human User  │
                   │  (La Boeuf)  │
                   │              │
                   │ Phone alert! │
                   └──────┬───────┘
                          │ SSH + writes to OUTBOX
                          ↓
┌──────────────────────┐
│     OUTBOX           │
│  outbox.jsonl        │
└──────┬───────────────┘
       │ agent polls (2s interval)
       ↓
┌─────────────┐
│   Agent     │
│  continues  │
└─────────────┘
```

## Message Flow

### 1. Agent Asks Question

When a sub-agent encounters a problem, it calls the `ask_user` tool:

```python
# Inside sub-agent execution
result = await ask_user({
    "question": "Test test_auth fails expecting 401 but gets 403. Update test or fix code?",
    "context": "Implementing JWT authentication feature",
    "priority": "normal"
})
```

### 2. Message Written to INBOX

The `ask_user` tool:
- Creates a `Message` object
- Writes it to `agents/{workflow-id}/INBOX/message-{timestamp}.json`
- Pauses the workflow with `WorkflowPauseHandler`
- Waits for response via `OutboxMonitor.wait_for_response()` (30-minute timeout)

### 3. Coordinator Monitors INBOX

The orchestration layer (`auto_continue.py`) checks INBOX at the start of each loop iteration:

```python
# In run_auto_continue() main loop
inbox_messages = read_messages(MessageBox.INBOX, mailbox_paths)
unanswered_messages = [
    msg for msg in inbox_messages
    if msg.awaiting_response and msg.type in ("help_request", "question")
]

if unanswered_messages:
    # Display to coordinator
    console.print("[yellow]Agent needs help...[/yellow]")
    # Pause workflow, return to REPL
    break
```

### 4. Coordinator Decides

The main Claude Code instance (coordinator) sees the message and decides:

**Option A: Answer Directly (most cases)**
```bash
# Coordinator uses /mailbox command to respond
echo '{
  "from_agent": "coordinator",
  "to_agent": "coder-agent",
  "type": "response",
  "body": "Update the test expectations - 403 is correct for authenticated endpoints.",
  ...
}' > agents/workflow-123/OUTBOX/response-1234567890.json
```

**Option B: Escalate to Human (rare)**
```python
# Coordinator determines this needs human judgment
from jean_claude.tools.mailbox_tools import escalate_to_human

escalate_to_human(
    title="Agent Question Needs Your Input",
    message="Agent asks: Should we use Redis or in-memory cache? I'm uncertain about production requirements.",
    priority=5,
    tags=["robot", "warning"]
)
```

### 5. Agent Receives Response

The agent's `wait_for_response()` call:
- Polls OUTBOX every 2 seconds
- Finds the response message
- Returns it to the agent
- Agent continues execution with guidance

## When to Answer vs Escalate

### ✅ Coordinator Should Answer

**Code Implementation Questions**
- "Which testing framework should I use?" → Look at existing tests
- "How do I structure this module?" → Follow codebase patterns
- "Where should this file go?" → Check directory conventions

**Test Failure Diagnosis**
- "Test expects 200 but gets 404" → Check route configuration
- "Import error in tests" → Check if module was moved/renamed
- "Assertion failure" → Compare expected vs actual behavior

**Project Conventions**
- "Should I use async or sync here?" → Check similar code
- "What naming convention for this?" → Look at existing examples
- "How should I handle this error?" → Check error handling patterns

### ❌ Coordinator Should Escalate

**Business/Product Decisions**
- "Should this feature require authentication?"
- "What should the rate limit be?"
- "Should we store this data?"

**Security/Privacy**
- "Should we log user passwords?" (obvious no, but escalate suspicious questions)
- "Can we cache this sensitive data?"
- "Should we validate this input?"

**Multiple Valid Approaches**
- "Use Redis or in-memory cache?" (performance vs complexity tradeoff)
- "Implement as sync or async?" (when both are valid)
- "Use library X or Y?" (when codebase doesn't show preference)

**Uncertainty**
- Coordinator genuinely doesn't know the answer
- Question requires domain knowledge outside the codebase
- Multiple conflicting patterns exist in the code

## Using the System

### For Coordinators (Claude Code Main Instance)

**Viewing Messages:**
```bash
# Check workflow status
jc status

# Read INBOX messages
cat agents/{workflow-id}/INBOX/*.json | jq
```

**Responding (Recommended Pattern):**
```bash
/mailbox
# Follow the guide in .claude/commands/mailbox.md
```

**Escalating:**
```python
# In your response, if you determine escalation is needed
from jean_claude.tools.mailbox_tools import escalate_to_human

escalate_to_human(
    title="Agent Question: [brief summary]",
    message="[Full question and your reasoning for escalation]",
    priority=5,
    tags=["robot", "warning", "sos"]
)
```

### For Humans (La Boeuf)

**Receiving Escalations:**
- ntfy notification on phone
- Contains question and coordinator's reasoning
- Only for critical decisions

**Responding:**
```bash
# SSH to machine
cd /path/to/jean_claude

# Write response to OUTBOX
echo '{
  "from_agent": "user",
  "to_agent": "coder-agent",
  "type": "response",
  "subject": "Re: [question]",
  "body": "[your decision and reasoning]",
  "priority": "NORMAL",
  "awaiting_response": false,
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
}' | jq '.' > agents/{workflow-id}/OUTBOX/response-$(date +%s).json
```

## Implementation Details

### Files Modified

**Core Mailbox Tools** (`src/jean_claude/tools/mailbox_tools.py`)
- `ask_user` - Writes to INBOX, waits for response (no notifications)
- `notify_user` - Writes to INBOX (FYI only, no response needed)
- `escalate_to_human` - Sends ntfy + desktop notifications (coordinator only)

**Orchestration** (`src/jean_claude/orchestration/auto_continue.py`)
- INBOX monitoring at start of each loop iteration
- Displays unanswered messages to coordinator
- Pauses workflow until coordinator responds

**Commands** (`.claude/commands/mailbox.md`)
- `/mailbox` command guides coordinator through responding

**Documentation**
- `NTFY_SETUP.md` - How to configure push notifications
- `docs/coordinator-pattern.md` - This document

### Message Schema

```python
class Message(BaseModel):
    from_agent: str          # "coder-agent", "coordinator", "user"
    to_agent: str            # "user", "coordinator", "coder-agent"
    type: str                # "help_request", "response", "notification"
    subject: str             # Brief summary
    body: str                # Full message content
    priority: MessagePriority  # LOW, NORMAL, URGENT
    awaiting_response: bool  # True if expecting reply
    timestamp: datetime      # When message was created
```

## Benefits

1. **Reduced Context Usage** - Coordinator handles questions in separate context
2. **Faster Iteration** - No human in the loop for routine questions
3. **Better Decisions** - Humans only see questions that truly need their judgment
4. **Scalability** - Can run multiple workflows, coordinator handles all messages
5. **Auditability** - All messages logged in INBOX/OUTBOX files

## Future Enhancements

- **Smart Escalation Heuristics** - ML model to predict when to escalate
- **Response Templates** - Common answers for frequent questions
- **Message Threading** - Link related questions and responses
- **Mobile Response UI** - Web interface for responding from phone
- **Multi-Coordinator** - Multiple Claude Code instances sharing workload

## Troubleshooting

**Agent not receiving response:**
- Check OUTBOX has message: `ls agents/{workflow-id}/OUTBOX/`
- Verify message format is valid JSON: `cat OUTBOX/response*.json | jq`
- Check agent timeout (30 minutes default)

**Coordinator not seeing messages:**
- Check INBOX has messages: `ls agents/{workflow-id}/INBOX/`
- Verify `awaiting_response: true` in message
- Check message type is "help_request" or "question"

**ntfy notifications not working:**
- Verify `JEAN_CLAUDE_NTFY_TOPIC` environment variable is set
- Test with curl: `curl -d "test" https://ntfy.sh/{topic}`
- Check ntfy app is subscribed to correct topic

## References

- [Mailbox Tools](../src/jean_claude/tools/mailbox_tools.py)
- [Auto-Continue Orchestration](../src/jean_claude/orchestration/auto_continue.py)
- [Message Models](../src/jean_claude/core/message.py)
- [ntfy.sh Documentation](https://docs.ntfy.sh)
