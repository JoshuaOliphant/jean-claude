# Implement MailboxProjectionBuilder for inbox/outbox views

## Description

## Description

Create a projection builder that reconstructs inbox/outbox state from message events. This provides the foundation for the event-based mailbox API.

## Projection State Structure

```python
{
  "inbox": [                    # Messages to this agent
    {
      "event_id": str,
      "from_agent": str,
      "content": str,
      "priority": str,
      "correlation_id": str,
      "awaiting_response": bool,
      "received_at": datetime,
      "acknowledged": bool
    }
  ],
  "outbox": [                   # Messages from this agent awaiting response
    {
      "event_id": str,
      "to_agent": str,
      "content": str,
      "correlation_id": str,
      "sent_at": datetime,
      "completed": bool
    }
  ],
  "conversation_history": [     # All messages in chronological order
    {
      "event_id": str,
      "from_agent": str,
      "to_agent": str,
      "content": str,
      "timestamp": datetime
    }
  ]
}
```

## Implementation

Create `src/jean_claude/core/mailbox_projection.py`:

- MailboxProjectionBuilder class extending ProjectionBuilder
- apply_agent_message_sent() - Add to inbox (if to_agent) or outbox (if from_agent)
- apply_agent_message_acknowledged() - Mark inbox message as read
- apply_agent_message_completed() - Remove from outbox, add to history
- Helper methods: get_unread_inbox(), get_pending_outbox(), get_conversation()

## Files to Create

- `src/jean_claude/core/mailbox_projection.py`
- `tests/core/test_mailbox_projection.py`

## Acceptance Criteria

- [ ] MailboxProjectionBuilder implements all required apply_* methods
- [ ] Inbox correctly filters messages by to_agent
- [ ] Outbox correctly filters messages by from_agent with awaiting_response=True
- [ ] Message acknowledgment updates inbox state
- [ ] Message completion removes from outbox
- [ ] Conversation history preserves all messages in order
- [ ] Tests cover all projection scenarios
- [ ] Tests verify message priority handling
- [ ] Tests verify correlation ID tracking

## Dependencies

- Depends on: jean_claude-di8 (message event types)

## Agent Work Estimate

4-5 iterations (moderate complexity, needs comprehensive testing)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-61z
- **Status**: in_progress
- **Created**: 2026-01-02 21:41:17
- **Updated**: 2026-01-03 17:37:02
