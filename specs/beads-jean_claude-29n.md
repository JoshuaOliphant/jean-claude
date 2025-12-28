# Agent mailbox communication system

## Description

## Agent Mailbox Communication System

Enable inter-agent communication through a persistent mailbox system integrated with SDK hooks.

### Storage Architecture
- `agents/{workflow_id}/mailbox/inbox.jsonl` - Append-only incoming messages
- `agents/{workflow_id}/mailbox/outbox.jsonl` - Append-only sent messages  
- `agents/{workflow_id}/mailbox/inbox_count.json` - Quick unread check: {"unread": N, "last_checked": "..."}

### Message Format (JSONL line)
```json
{"id": "msg-001", "from": "beads-xyz", "to": "coordinator", "type": "help_request", "subject": "...", "body": "...", "priority": "urgent|normal|low", "created_at": "...", "awaiting_response": true}
```

### SDK Hook Integration
1. **SubagentStop hook** - Detects help requests when agent stops, notifies orchestrator via systemMessage
2. **UserPromptSubmit hook** - Injects unread messages as additionalContext when agent resumes
3. **PostToolUse hook** - Updates inbox_count when messages are written to mailbox paths

### Priority Levels
- `urgent`: Agent blocked, immediate attention needed
- `normal`: Question/FYI, process at natural breakpoints  
- `low`: Optional feedback, review when convenient

### Agent Waiting Pattern
1. Agent writes to outbox with awaiting_response=true
2. Sets state.waiting_for_response=true
3. Agent stops (SubagentStop hook fires, notifies coordinator)
4. Coordinator reads message, writes response to agent inbox
5. Agent resumes, UserPromptSubmit hook injects response

---

## Implementation Context

### Files to Create
- `src/jean_claude/core/mailbox.py` - Mailbox, Message Pydantic models, read/write helpers
- `src/jean_claude/orchestration/mailbox_hooks.py` - SDK hook callbacks

### Files to Modify  
- `src/jean_claude/core/sdk_executor.py` - Register hooks in ClaudeAgentOptions
- `src/jean_claude/orchestration/workflow_state.py` - Add waiting_for_response fields

### Dependencies
- Uses existing JSONL pattern from agent output logging
- Integrates with WorkflowState for persistence
- Hooks use claude_agent_sdk HookMatcher pattern

### Error Handling
- Gracefully handle missing/corrupted mailbox files
- Create mailbox directory on first write
- Log but don't fail if hook cannot read mailbox

---

## Acceptance Criteria
- [ ] Agents can send messages to coordinator or other agents
- [ ] Orchestrator receives notification when help is requested (via SubagentStop hook)
- [ ] Agents see unread messages automatically on resume (via UserPromptSubmit hook)
- [ ] Priority field routes urgent messages with systemMessage
- [ ] Message history preserved in append-only JSONL
- [ ] inbox_count.json enables quick unread check without parsing JSONL
- [ ] State tracks waiting_for_response flag for blocked agents

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-29n
- **Status**: in_progress
- **Created**: 2025-12-26 18:11:57
- **Updated**: 2025-12-26 18:47:29
