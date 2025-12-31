# Mailbox

Respond to agent messages in the mailbox system (coordinator pattern).

## Purpose

When agents call `ask_user` or `notify_user`, their messages appear in the INBOX.
As the coordinator, you (Claude Code) should triage these messages and either:
1. **Respond directly** - Answer on behalf of La Boeuf (most cases)
2. **Escalate** - Send ntfy notification to La Boeuf (critical decisions only)

## View Agent Messages

Read the current workflow's INBOX:

```bash
jc status
```

This shows the workflow ID. Then check messages:

```bash
cat agents/{workflow-id}/INBOX/*.json | jq
```

## Respond to Agent

When you see an agent question that you can answer:

1. **Understand the question** - Read the INBOX message carefully
2. **Formulate your response** - What should the agent do?
3. **Write to OUTBOX** - Create a response message

### Example Response

```bash
echo '{
  "from_agent": "coordinator",
  "to_agent": "coder-agent",
  "type": "response",
  "subject": "Re: Test failure question",
  "body": "Update the test expectations. The 403 status code is correct - the endpoint requires authentication. Change the test to expect 403 instead of 401.",
  "priority": "NORMAL",
  "awaiting_response": false,
  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
}' | jq '.' > agents/{workflow-id}/OUTBOX/response-$(date +%s).json
```

## Escalate to Human

Only escalate to La Boeuf when:
- Decision requires business/product judgment
- You're uncertain about the correct approach
- The question involves security or data privacy
- Multiple valid solutions exist and preference matters

### Escalation Process

1. **Use the escalate_to_human function** (available in mailbox_tools.py):

```python
from jean_claude.tools.mailbox_tools import escalate_to_human

escalate_to_human(
    title="Agent Question Needs Your Input",
    message="The agent is asking: [question]. I'm uncertain about [specific concern]. Please respond via terminal.",
    priority=5,  # Max urgency
    tags=["robot", "warning", "sos"]
)
```

2. **La Boeuf will receive ntfy notification** on their phone
3. **They'll respond via terminal** by writing to OUTBOX
4. **Agent continues** with their guidance

## Guidelines

**DO respond yourself when:**
- ✅ Question is about code implementation details
- ✅ Test failure diagnosis is straightforward
- ✅ Agent needs guidance on project conventions
- ✅ Decision follows clear patterns in the codebase

**DON'T respond yourself when:**
- ❌ Unsure about the correct approach
- ❌ Decision has business/product implications
- ❌ Security or privacy considerations involved
- ❌ La Boeuf's explicit preference is needed

## Tips

- **Be specific** - Agents need clear, actionable guidance
- **Reference code** - Point to examples in the codebase
- **Explain reasoning** - Help the agent learn patterns
- **Act quickly** - Agents are waiting (30-minute timeout)

## Workflow Resume

After you respond:
1. The agent's `ask_user` tool receives your response
2. The workflow automatically resumes
3. The agent continues with your guidance

No manual resume needed - it's automatic! 🎉
