# Add message event types to event store

## Description

## Description

Add new event types to the event store for inter-agent messaging. This is the foundation for replacing the file-based mailbox system with event-based messaging.

## Event Types to Add

1. `agent.message.sent` - Agent sends a message to another agent
2. `agent.message.acknowledged` - Recipient acknowledges receiving message
3. `agent.message.completed` - Agent completes a task from a message

## Implementation Details

### Event Data Schemas

```python
# agent.message.sent
{
  "from_agent": str,          # Sender agent ID
  "to_agent": str,            # Recipient agent ID
  "content": str,             # Message content
  "priority": str,            # low, normal, urgent
  "correlation_id": str,      # UUID for tracking conversation
  "awaiting_response": bool,  # Does sender expect a response?
  "message_type": str         # task_request, status_update, question, answer
}

# agent.message.acknowledged  
{
  "correlation_id": str,      # Links to original message
  "from_agent": str,          # Agent acknowledging
  "acknowledged_at": str      # ISO timestamp
}

# agent.message.completed
{
  "correlation_id": str,      # Links to original message
  "from_agent": str,          # Agent completing task
  "result": str,              # Response/result content
  "success": bool             # Task succeeded or failed
}
```

## Files to Modify

- `src/jean_claude/core/event_models.py` - Add event type constants
- `src/jean_claude/core/projection_builder.py` - Add abstract methods for new event types
- Update all existing ProjectionBuilder test fixtures to implement new methods

## Acceptance Criteria

- [ ] Event type constants defined in event_models.py
- [ ] Event data schemas validated with Pydantic
- [ ] ProjectionBuilder has abstract methods: apply_agent_message_sent, apply_agent_message_acknowledged, apply_agent_message_completed
- [ ] All existing tests pass (projection builder fixtures updated)
- [ ] Can write and read message events from event store
- [ ] Event data serializes/deserializes correctly

## Agent Work Estimate

3-4 iterations (small feature, well-defined scope)

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-di8
- **Status**: in_progress
- **Created**: 2026-01-02 21:40:39
- **Updated**: 2026-01-03 08:04:49
