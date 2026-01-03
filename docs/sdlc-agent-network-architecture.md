# SDLC Agent Network Architecture

**Date:** 2026-01-02
**Status:** Architectural Design
**Authors:** Claude (Sonnet 4.5), La Boeuf

---

## Executive Summary

This document proposes a **conversational agent network architecture** for Jean Claude that enables SDLC agents (Plan, Implement, Test, Review, Deploy) to collaborate bidirectionally, escalate intelligently through multiple levels, and operate as a distributed system with full event sourcing observability.

### Key Innovations

1. **Collaborative Agent Network** - Agents ask each other questions, provide feedback, and iterate together
2. **Multi-Level Escalation** - Agent ↔ Agent (Level 1) → Coordinator (Level 2) → La Boeuf (Level 3)
3. **Event Sourcing as Communication** - Every message is an event; complete audit trail of all interactions
4. **Pipeline Parallelism** - Test Feature 1 while implementing Feature 2
5. **Conversation Threading** - Multi-message dialogues tracked with full context

### Strategic Context

This architecture represents the **ultimate evolution** of Jean Claude's two-agent pattern:

**Current:** Opus (plan once) → Sonnet (implement features sequentially)
**Future:** Distributed agent pool → Collaborative network → Intelligent escalation → Complete observability

---

## Table of Contents

- [Architectural Patterns Comparison](#architectural-patterns-comparison)
- [Recommended Architecture: Agent Pool with Mailbox](#recommended-architecture-agent-pool-with-mailbox)
- [Communication Protocol Design](#communication-protocol-design)
- [Multi-Level Escalation Hierarchy](#multi-level-escalation-hierarchy)
- [Event Sourcing Schema](#event-sourcing-schema)
- [State Machine Design](#state-machine-design)
- [Complete Examples](#complete-examples)
- [Implementation Roadmap](#implementation-roadmap)
- [Critical Design Decisions](#critical-design-decisions)
- [Recommendations](#recommendations)

---

## Architectural Patterns Comparison

### Pattern 1: Subagent Delegation

**Architecture:**
```
Main Coordinator (Sonnet)
    ├─> Delegates to Plan Subagent (Opus)
    ├─> Delegates to Implement Subagent (Sonnet)
    ├─> Delegates to Test Subagent (Haiku)
    ├─> Delegates to Review Subagent (Opus)
    └─> Delegates to Deploy Subagent (Haiku)
```

**How it works:**
- Single main agent orchestrates entire workflow
- Invokes subagents synchronously via Task tool
- Main agent's context accumulates all subagent responses
- WorkflowState.json is single source of truth

**Pros:**
- ✅ Low complexity - familiar orchestration pattern
- ✅ Easy to debug - single process
- ✅ Simple state management
- ✅ Simple event sourcing - single event stream

**Cons:**
- ❌ Context bloat - main coordinator accumulates all responses
- ❌ Sequential only - no parallelism
- ❌ No peer collaboration - agents can't help each other
- ❌ High cost for long workflows

**Best for:** Simple workflows, learning the pattern, quick validation

---

### Pattern 2: Hybrid - SDLC Subagent Workflow

**Architecture:**
```
SDLC Orchestrator (Sonnet)
    1. Plan Subagent (Opus) → Features list [ONCE]
    2. Loop through features:
        - Implement Subagent (Sonnet) → Code [FRESH CONTEXT]
        - Test Subagent (Haiku) → Validation [FRESH CONTEXT]
    3. Review Subagent (Opus) → Quality check [ONCE]
    4. Deploy Subagent (Haiku) → Release [ONCE]
```

**How it works:**
- Orchestrator manages SDLC sequence
- Each feature implementation gets fresh Implement subagent (like current Coder)
- Plan/Review/Deploy run once per workflow
- Test runs after each feature

**Pros:**
- ✅ Fresh context per feature - preserves two-agent benefit
- ✅ Low complexity - evolution of current pattern
- ✅ Easy migration path
- ✅ Moderate cost - similar to current two-agent
- ✅ Simple event sourcing - single stream

**Cons:**
- ⚠️ Sequential features - no parallelism
- ❌ Limited collaboration - hardcoded test → implement loop
- ❌ Single point of failure

**Best for:** Near-term implementation, evolutionary improvement, production stability

---

### Pattern 3: Agent Pool with Mailbox (Recommended Long-Term)

**Architecture:**
```
Agent Pool (All running concurrently):
┌─────────────────┐
│ Plan Agent      │◄─── START message
│ (Opus)          │───┐
└─────────────────┘   │
                      ▼
┌─────────────────┐ Mailbox
│ Implement Agent │◄─── FEATURES_READY
│ (Sonnet)        │───┐
└─────────────────┘   │
                      ▼
┌─────────────────┐ WorkflowState (Event-Sourced)
│ Test Agent      │◄─── FEATURE_DONE  ───┐
│ (Haiku)         │───┐                  │
└─────────────────┘   │                  ▼
                      ▼              Event Store
┌─────────────────┐
│ Review Agent    │◄─── TESTS_PASSED
│ (Opus)          │───┐
└─────────────────┘   │
                      ▼
┌─────────────────┐
│ Deploy Agent    │◄─── REVIEW_APPROVED
│ (Haiku)         │
└─────────────────┘
```

**How it works:**
- All agents spawn at workflow start
- Agents wait for messages in their INBOX
- Message routing:
  1. Plan → "FEATURES_READY" → Implement
  2. Implement → "FEATURE_DONE" → Test
  3. Test → "TESTS_PASSED" → Implement (next feature) OR Review (if all done)
  4. Review → "REVIEW_APPROVED" → Deploy
  5. Deploy → "WORKFLOW_COMPLETE" → Shutdown all agents
- Each agent reads/writes events (no shared state file)
- Event store tracks all agent actions

**Pros:**
- ✅ Perfect context isolation - each agent fresh context
- ✅ True collaboration - agents ask each other questions
- ✅ Pipeline parallelism - test F1 while implementing F2
- ✅ Perfect event sourcing fit - distributed events naturally logged
- ✅ Multi-level escalation - peer → coordinator → human
- ✅ Resilient - agents can crash and restart
- ✅ Scalable - agents can run on different machines
- ✅ Conversation corpus - train future models on effective collaboration

**Cons:**
- ❌ High complexity - distributed system
- ❌ Harder debugging - multiple processes
- ❌ Requires mature mailbox system
- ❌ State synchronization challenges
- ❌ Event correlation complexity

**Best for:** Long-term vision, complex workflows, maximum collaboration

---

## Recommended Architecture: Agent Pool with Mailbox

### Network Topology

```
                            ┌──────────────────┐
                            │   La Boeuf       │
                            │   (Human)        │
                            └────────▲─────────┘
                                     │
                            ┌────────┴─────────┐
                            │   Coordinator    │
                            │   (Meta-Agent)   │
                            └────────▲─────────┘
                                     │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
    Level 2 Escalation         Level 2 Escalation        Level 2 Escalation
         │                          │                          │
         ▼                          ▼                          ▼
┌─────────────────┐        ┌─────────────────┐       ┌─────────────────┐
│   Plan Agent    │◄──────►│ Implement Agent │◄─────►│   Test Agent    │
│   (Opus)        │ Level 1│   (Sonnet)      │Level 1│   (Haiku)       │
└─────────────────┘        └─────────────────┘       └─────────────────┘
         ▲                          │                          │
         │                          │                          │
         │                          ▼                          ▼
         │                 ┌─────────────────┐       ┌─────────────────┐
         └────────────────►│  Review Agent   │◄──────┤  Deploy Agent   │
                  Level 1  │   (Opus)        │Level 1│   (Haiku)       │
                           └─────────────────┘       └─────────────────┘

Legend:
◄────► : Bidirectional peer communication (Level 1)
   │    : Escalation path to Coordinator (Level 2)
   ▲    : Escalation to Human (Level 3)
```

### Communication Flows

**Happy Path (No Escalations):**
```
Plan ──features──> Implement ──code──> Test ──passed──> Review ──approved──> Deploy
                      ▲                   │
                      └──────fixes────────┘
                      (feedback loop)
```

**With Level 1 Escalation (Peer Collaboration):**
```
Implement ──❓ clarification──> Plan
Implement <──✓ answer───────── Plan
```

**With Level 2 Escalation (System Blocker):**
```
Implement ──❓ clarification──> Plan
Plan ──🚨 can't answer──> Coordinator
Coordinator ──🔍 searches docs──> [found answer]
Coordinator ──✓ unblock──> Plan
Plan ──✓ answer──> Implement
```

**With Level 3 Escalation (Human Decision):**
```
Implement ──❓ clarification──> Plan
Plan ──🚨 can't answer──> Coordinator
Coordinator ──🔍 searches docs──> [not found]
Coordinator ──📱 ntfy──> La Boeuf
La Boeuf ──✅ decision──> Coordinator
Coordinator ──✓ unblock──> Plan
Plan ──✓ answer──> Implement
```

---

## Communication Protocol Design

### Message Type Taxonomy

```python
class MessageType(str, Enum):
    # Workflow coordination
    START = "start"                    # Orchestrator → Plan: Begin workflow
    WORKFLOW_COMPLETE = "complete"      # Any agent → Orchestrator: Workflow done

    # Work handoffs (forward progress)
    FEATURES_READY = "features_ready"   # Plan → Implement: Here's the plan
    FEATURE_DONE = "feature_done"       # Implement → Test: Code ready
    TESTS_PASSED = "tests_passed"       # Test → Review: Quality gate passed
    REVIEW_APPROVED = "review_approved" # Review → Deploy: Ship it

    # Clarification requests (backward questions)
    REQUEST_CLARIFICATION = "request_clarification"  # Any → Any: Need more info
    PROVIDE_CLARIFICATION = "provide_clarification"  # Any → Any: Here's the detail

    # Feedback loops (iteration)
    REQUEST_CHANGES = "request_changes"  # Test/Review → Implement: Fix this
    CHANGES_COMPLETE = "changes_complete" # Implement → Test/Review: Fixed

    # Collaboration
    REQUEST_REVIEW = "request_review"    # Any → Review: Check my work
    APPROVE_WORK = "approve_work"        # Review → Any: Looks good
    REJECT_WORK = "reject_work"          # Review → Any: Needs work

    # Escalation (multi-level)
    REPORT_BLOCKER = "report_blocker"    # Agent → Coordinator: I'm stuck
    ESCALATE_TO_HUMAN = "escalate_to_human"  # Coordinator → La Boeuf: Need decision
    HUMAN_RESPONSE = "human_response"    # La Boeuf → Coordinator: Here's my answer
    UNBLOCK_AGENT = "unblock_agent"      # Coordinator → Agent: Proceed with this

    # Status
    AGENT_READY = "agent_ready"          # Agent → Pool: I'm ready for work
    AGENT_BUSY = "agent_busy"            # Agent → Pool: Working on something
    AGENT_WAITING = "agent_waiting"      # Agent → Pool: Blocked, waiting
```

### Message Model

```python
class Message(BaseModel):
    """Enhanced message with conversation threading."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    thread_id: str | None = None  # For tracking conversations
    in_reply_to: str | None = None  # For threading responses

    from_agent: str
    to_agent: str
    workflow_id: str

    message_type: MessageType
    priority: MessagePriority

    payload: dict
    context: dict = {}  # Additional context (files changed, error messages, etc.)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None  # For time-sensitive messages

    # Conversation tracking
    conversation_history: list[str] = []  # Previous message IDs in thread

    def reply(self, message_type: MessageType, payload: dict) -> "Message":
        """Create a reply message in the same thread."""
        return Message(
            thread_id=self.thread_id or self.id,
            in_reply_to=self.id,
            from_agent=self.to_agent,  # Swap sender/receiver
            to_agent=self.from_agent,
            workflow_id=self.workflow_id,
            message_type=message_type,
            payload=payload,
            conversation_history=[*self.conversation_history, self.id],
        )
```

### Conversation Threading

```python
class Conversation:
    """Tracks a multi-message conversation between agents."""

    def __init__(self, thread_id: str, workflow_id: str):
        self.thread_id = thread_id
        self.workflow_id = workflow_id
        self.messages: list[Message] = []
        self.participants: set[str] = set()
        self.status: Literal["active", "resolved", "escalated"] = "active"
        self.resolution: str | None = None

    def to_summary(self) -> str:
        """Generate human-readable conversation summary."""
        lines = [f"Conversation {self.thread_id} ({self.status})"]
        lines.append(f"Participants: {', '.join(self.participants)}")
        lines.append(f"Messages: {len(self.messages)}\n")

        for msg in self.messages:
            lines.append(f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.from_agent} → {msg.to_agent}")
            lines.append(f"  Type: {msg.message_type}")

            if msg.message_type == MessageType.REQUEST_CLARIFICATION:
                lines.append(f"  Question: {msg.payload.get('question', 'N/A')}")
            elif msg.message_type == MessageType.PROVIDE_CLARIFICATION:
                lines.append(f"  Answer: {msg.payload.get('answer', 'N/A')}")

            lines.append("")

        if self.resolution:
            lines.append(f"Resolution: {self.resolution}")

        return "\n".join(lines)
```

---

## Multi-Level Escalation Hierarchy

### Three Levels of Escalation

```
Level 1: Agent-to-Agent (Peer Collaboration)
  └─> Implement asks Plan for clarification
  └─> Test asks Review for edge case guidance
  └─> Deploy asks Review for final approval

Level 2: Agent-to-Coordinator (System-Level Blockers)
  └─> Agent can't answer question (missing requirements)
  └─> Agent encounters technical blocker (API down, credentials missing)
  └─> Agent detects ambiguity that needs resolution
  └─> Agent exceeds retry limit (stuck in loop)

Level 3: Coordinator-to-La Boeuf (Business Decisions)
  └─> Architectural decision needed
  └─> Business logic clarification
  └─> Security/compliance decision
  └─> Budget approval (expensive operation)
  └─> Timeline decision (skip tests vs delay?)
```

### Coordinator Agent Design

```python
class CoordinatorAgent:
    """Meta-agent that manages the SDLC agent pool and escalates to humans."""

    async def handle_escalation(self, message: Message):
        """Route escalation based on type and severity."""

        blocker_type = message.payload["blocker_type"]

        # Level 2 escalations: Can coordinator resolve?
        if blocker_type == "missing_requirement":
            # Try to find answer in project docs
            answer = await self.search_project_context(message.payload["original_question"])

            if answer:
                # Found it! Send back to agent
                await self.unblock_agent(message.from_agent, answer)
            else:
                # Can't find it, escalate to La Boeuf (Level 3)
                await self.escalate_to_human(message)

        elif blocker_type in ["architectural_decision", "business_logic", "security_decision"]:
            # These ALWAYS go to La Boeuf (Level 3)
            await self.escalate_to_human(message)

    async def escalate_to_human(self, message: Message):
        """Level 3 escalation: Send to La Boeuf via ntfy."""

        escalation_details = self.build_escalation_message(message)

        # Send via ntfy (existing mailbox tools)
        escalate_to_human(
            title=f"🚨 {blocker_type.replace('_', ' ').title()}",
            message=escalation_details,
            priority=5,  # Urgent
            project_name=Path.cwd().name
        )

        # Poll for response
        response = await self.wait_for_human_response(timeout=600)  # 10 minutes

        if response:
            await self.unblock_agent(message.from_agent, response)
        else:
            # No response, pause workflow
            self.state.pause("awaiting_human_response")
```

### Escalation Example: OAuth Provider Decision

**Full escalation flow:**

```
1. Implement Agent realizes OAuth provider is ambiguous
   [Implement] clarification_requested (to: plan, question: OAuth provider)

2. Plan Agent can't answer from existing requirements
   [Plan] blocker_reported (to: coordinator, reason: missing_requirement)

3. Coordinator searches project docs
   [Coordinator] searching_project_context (query: OAuth provider)
   [Coordinator] search_failed (reason: not_found_in_docs)

4. Coordinator escalates to La Boeuf via ntfy
   [Coordinator] escalated_to_human (blocker: missing_requirement)

   📱 La Boeuf receives notification:
   "[jean-claude] 🚨 Missing Requirement"

   Workflow: sdlc-a3b4c5d6
   Agent: implement
   Blocker: missing_requirement

   Question: What OAuth provider should I use?

   Context:
   - Current code: src/auth/oauth.py
   - Ambiguity: oauth_provider parameter undefined

   What should I do?

5. La Boeuf responds via ntfy
   "sdlc-a3b4c5d6: Use GitHub OAuth. Our audience is developers."

   [Coordinator] human_response_received (decision: GitHub OAuth)

6. Coordinator unblocks Implement Agent
   [Coordinator] agent_unblocked (agent: implement, resolution: human_decision)

7. Implement Agent continues with GitHub OAuth
   [Implement] resumed_work (feature_id: auth-1, oauth_provider: GitHub)
   [Implement] feature_completed (feature_id: auth-1)
```

---

## Event Sourcing Schema

### Database Schema

```sql
-- .jc/events.db schema enhancement

-- Core events table
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT UNIQUE NOT NULL,  -- UUID for deduplication
    workflow_id TEXT NOT NULL,
    timestamp REAL NOT NULL,

    -- Agent identification
    agent_id TEXT NOT NULL,         -- Which agent generated this event
    agent_type TEXT NOT NULL,       -- plan, implement, test, review, deploy, coordinator

    -- Event classification
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL,   -- workflow, agent, message, conversation, escalation

    -- Payload
    payload JSON NOT NULL,

    -- Conversation threading
    thread_id TEXT,                 -- Conversation thread this event belongs to
    message_id TEXT,                -- If event relates to a message
    in_reply_to TEXT,               -- Parent message ID

    -- Relationships
    related_feature_id TEXT,        -- Which feature being worked on
    related_agent_id TEXT,          -- Other agent involved (for messages)

    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_workflow_timestamp ON events(workflow_id, timestamp);
CREATE INDEX idx_agent_type ON events(agent_id, agent_type, timestamp);
CREATE INDEX idx_thread ON events(thread_id, timestamp);
CREATE INDEX idx_event_type ON events(event_type, workflow_id);

-- Messages table (denormalized for quick message queries)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT UNIQUE NOT NULL,
    thread_id TEXT,
    in_reply_to TEXT,

    workflow_id TEXT NOT NULL,
    from_agent TEXT NOT NULL,
    to_agent TEXT NOT NULL,

    message_type TEXT NOT NULL,
    priority TEXT NOT NULL,

    payload JSON NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    delivered_at DATETIME,
    read_at DATETIME,
    responded_at DATETIME,

    conversation_status TEXT DEFAULT 'pending',

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

CREATE INDEX idx_message_thread ON messages(thread_id, created_at);
CREATE INDEX idx_message_to ON messages(to_agent, delivered_at);

-- Conversations table (aggregate view)
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,

    initiated_by TEXT NOT NULL,
    initiated_at DATETIME NOT NULL,

    participants JSON NOT NULL,
    message_count INTEGER DEFAULT 0,

    status TEXT DEFAULT 'active',   -- active, resolved, escalated
    resolution TEXT,
    resolved_at DATETIME,

    escalated_to TEXT,
    escalation_reason TEXT,
    escalated_at DATETIME,

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);

-- Agent states table (current state snapshot)
CREATE TABLE IF NOT EXISTS agent_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,

    current_state TEXT NOT NULL,
    blocked_on TEXT,

    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,

    work_queue_size INTEGER DEFAULT 0,
    active_threads INTEGER DEFAULT 0,

    UNIQUE(agent_id, workflow_id)
);

-- Escalations table
CREATE TABLE IF NOT EXISTS escalations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    escalation_id TEXT UNIQUE NOT NULL,
    workflow_id TEXT NOT NULL,
    thread_id TEXT,

    from_agent TEXT NOT NULL,
    to_level TEXT NOT NULL,         -- coordinator, human

    blocker_type TEXT NOT NULL,
    context JSON NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    resolution TEXT,
    resolved_by TEXT,

    FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
);
```

### Event Types

```python
class EventCategory(str, Enum):
    WORKFLOW = "workflow"
    AGENT = "agent"
    MESSAGE = "message"
    CONVERSATION = "conversation"
    ESCALATION = "escalation"
    FEATURE = "feature"

class EventType(str, Enum):
    # Workflow events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_PAUSED = "workflow_paused"

    # Agent lifecycle events
    AGENT_STARTED = "agent_started"
    AGENT_STATE_CHANGED = "agent_state_changed"
    AGENT_STOPPED = "agent_stopped"

    # Message events
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"
    MESSAGE_RESPONDED = "message_responded"

    # Conversation events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_RESOLVED = "conversation_resolved"
    CONVERSATION_ESCALATED = "conversation_escalated"

    # Work events
    FEATURE_STARTED = "feature_started"
    FEATURE_COMPLETED = "feature_completed"

    # Collaboration events
    CLARIFICATION_REQUESTED = "clarification_requested"
    CLARIFICATION_PROVIDED = "clarification_provided"
    CHANGES_REQUESTED = "changes_requested"

    # Escalation events
    BLOCKER_REPORTED = "blocker_reported"
    ESCALATED_TO_HUMAN = "escalated_to_human"
    HUMAN_RESPONSE_RECEIVED = "human_response_received"
    AGENT_UNBLOCKED = "agent_unblocked"

    # Quality gates
    TESTS_PASSED = "tests_passed"
    TESTS_FAILED = "tests_failed"
    REVIEW_APPROVED = "review_approved"
```

### Key Queries

**Reconstruct Conversation:**
```python
def get_conversation_timeline(thread_id: str) -> list[dict]:
    return db.execute("""
        SELECT timestamp, agent_id, event_type, payload
        FROM events
        WHERE thread_id = ?
        ORDER BY timestamp ASC
    """, (thread_id,)).fetchall()
```

**Get Workflow Timeline:**
```python
def get_workflow_timeline(workflow_id: str) -> list[dict]:
    return db.execute("""
        SELECT timestamp, agent_id, agent_type, event_type, payload
        FROM events
        WHERE workflow_id = ?
        ORDER BY timestamp ASC
    """, (workflow_id,)).fetchall()
```

**Get Active Conversations:**
```python
def get_active_conversations(workflow_id: str) -> list[Conversation]:
    rows = db.execute("""
        SELECT thread_id, initiated_by, participants, message_count, status
        FROM conversations
        WHERE workflow_id = ? AND status = 'active'
        ORDER BY initiated_at DESC
    """, (workflow_id,)).fetchall()
    return [Conversation(**row) for row in rows]
```

---

## State Machine Design

### Workflow State Machine

```python
class WorkflowPhase(str, Enum):
    INITIALIZING = "initializing"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    REVIEWING = "reviewing"
    DEPLOYING = "deploying"
    PAUSED = "paused"
    COMPLETE = "complete"
    FAILED = "failed"

class WorkflowStateMachine:
    """State machine for SDLC workflow."""

    # Valid state transitions
    TRANSITIONS = {
        WorkflowPhase.INITIALIZING: [WorkflowPhase.PLANNING, WorkflowPhase.FAILED],
        WorkflowPhase.PLANNING: [WorkflowPhase.IMPLEMENTING, WorkflowPhase.PAUSED, WorkflowPhase.FAILED],
        WorkflowPhase.IMPLEMENTING: [WorkflowPhase.TESTING, WorkflowPhase.PAUSED, WorkflowPhase.FAILED],
        WorkflowPhase.TESTING: [
            WorkflowPhase.IMPLEMENTING,  # Tests failed, back to implementation
            WorkflowPhase.REVIEWING,      # Tests passed
            WorkflowPhase.PAUSED,
            WorkflowPhase.FAILED
        ],
        WorkflowPhase.REVIEWING: [
            WorkflowPhase.IMPLEMENTING,  # Review rejected
            WorkflowPhase.DEPLOYING,      # Review approved
            WorkflowPhase.PAUSED,
            WorkflowPhase.FAILED
        ],
        WorkflowPhase.DEPLOYING: [WorkflowPhase.COMPLETE, WorkflowPhase.FAILED],
        WorkflowPhase.PAUSED: [  # Can resume to any active phase
            WorkflowPhase.PLANNING,
            WorkflowPhase.IMPLEMENTING,
            WorkflowPhase.TESTING,
            WorkflowPhase.REVIEWING,
            WorkflowPhase.DEPLOYING,
            WorkflowPhase.FAILED
        ],
        WorkflowPhase.COMPLETE: [],  # Terminal state
        WorkflowPhase.FAILED: [],     # Terminal state
    }
```

### Agent State Machine

```python
class AgentPhase(str, Enum):
    # Initialization
    STARTING = "starting"
    REGISTERING = "registering"

    # Idle states
    IDLE = "idle"
    WAITING_FOR_WORK = "waiting_work"

    # Active work states
    PROCESSING_MESSAGE = "processing_message"
    EXECUTING_TASK = "executing_task"
    WRITING_CODE = "writing_code"
    RUNNING_TESTS = "running_tests"
    PERFORMING_REVIEW = "performing_review"

    # Blocked states
    WAITING_FOR_PEER_RESPONSE = "waiting_peer"
    WAITING_FOR_COORDINATOR = "waiting_coordinator"
    WAITING_FOR_HUMAN = "waiting_human"
    WAITING_FOR_RESOURCE = "waiting_resource"

    # Error states
    RETRYING = "retrying"
    ERROR = "error"

    # Terminal states
    COMPLETED_WORK = "completed"
    SHUTDOWN = "shutdown"

class AgentStateMachine:
    """State machine for individual agent."""

    def __init__(self, agent_id: str, agent_type: str, workflow_id: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.workflow_id = workflow_id
        self.current_phase = AgentPhase.STARTING

        # Blocking tracking
        self.blocked_on: str | None = None
        self.blocked_since: datetime | None = None

    def block_on_peer(self, peer_agent: str, reason: str):
        """Block on another agent (Level 1 escalation)."""
        self.transition(
            AgentPhase.WAITING_FOR_PEER_RESPONSE,
            blocked_on=peer_agent,
            reason=reason
        )

    def escalate_to_coordinator(self, reason: str):
        """Escalate to coordinator (Level 2)."""
        self.transition(
            AgentPhase.WAITING_FOR_COORDINATOR,
            blocked_on="coordinator",
            reason=reason
        )

    def escalate_to_human(self, reason: str):
        """Escalate to human (Level 3)."""
        self.transition(
            AgentPhase.WAITING_FOR_HUMAN,
            blocked_on="human",
            reason=reason
        )
```

---

## Complete Examples

### Example 1: Clarification Request (Level 1)

**Scenario:** Implement agent needs OAuth provider details

```python
# Implement agent processing "implement authentication"
class ImplementAgent(SDLCAgent):
    async def process_feature(self, feature: Feature):
        # Start implementing
        log_event("feature_started", feature_id=feature.id)

        # Realize we need more detail
        if self.needs_clarification(feature):
            # Ask Plan agent for details
            clarification_request = Message(
                from_agent="implement",
                to_agent="plan",
                workflow_id=self.workflow_id,
                message_type=MessageType.REQUEST_CLARIFICATION,
                payload={
                    "feature_id": feature.id,
                    "question": "What OAuth provider should I use?",
                    "context": {"ambiguity": "oauth_provider parameter undefined"}
                },
                priority=MessagePriority.HIGH
            )

            await self.send_message(clarification_request)

            # Wait for Plan agent to respond
            response = await self.wait_for_reply(clarification_request.id, timeout=300)

            if response.message_type == MessageType.PROVIDE_CLARIFICATION:
                oauth_provider = response.payload["answer"]
                await self.implement_with_context(feature, oauth_provider)
```

**Event Sequence:**
```
[Implement] feature_started (feature_id: auth-1)
[Implement] clarification_requested (to: plan, question: OAuth provider)
[Implement] agent_waiting (blocked_on: plan)
[Plan]      clarification_request_received (question: OAuth provider)
[Plan]      clarification_provided (answer: GitHub OAuth)
[Implement] clarification_received (answer: GitHub OAuth)
[Implement] agent_working (resumed: auth-1)
[Implement] feature_completed (feature_id: auth-1)
```

---

### Example 2: Feedback Loop (Test → Implement → Test)

**Scenario:** Test agent finds failures, Implement fixes, Test re-runs

```python
class TestAgent(SDLCAgent):
    async def process_feature(self, message: Message):
        feature = message.payload["feature"]

        test_result = await self.run_tests(feature)

        if test_result.passed:
            # Tests pass, send to Review
            next_message = Message(
                from_agent="test",
                to_agent="review",
                workflow_id=self.workflow_id,
                message_type=MessageType.TESTS_PASSED,
                payload={"feature": feature, "coverage": test_result.coverage}
            )
            await self.send_message(next_message)
        else:
            # Tests fail, send back to Implement with details
            feedback = Message(
                from_agent="test",
                to_agent="implement",
                workflow_id=self.workflow_id,
                message_type=MessageType.REQUEST_CHANGES,
                payload={
                    "feature": feature,
                    "failures": test_result.failures,
                },
                thread_id=message.thread_id,
                priority=MessagePriority.HIGH
            )
            await self.send_message(feedback)
```

**Event Sequence (with feedback loop):**
```
[Implement] feature_completed (feature_id: auth-1)
[Test]      tests_run (feature_id: auth-1, passed: False)
[Test]      test_failures_reported (feature_id: auth-1, count: 3)
[Implement] change_request_received (feature_id: auth-1, failures: 3)
[Implement] changes_applied (feature_id: auth-1)
[Implement] changes_completed (feature_id: auth-1)
[Test]      tests_run (feature_id: auth-1, passed: True)  # RERUN
[Test]      feature_validated (feature_id: auth-1)
[Review]    review_started (feature_id: auth-1)
```

---

### Example 3: Multi-Level Escalation (All 3 Levels)

**Scenario:** Implement → Plan → Coordinator → La Boeuf

```
1. Implement Agent realizes OAuth provider is ambiguous
   [Implement] clarification_requested (to: plan, question: OAuth provider)

2. Plan Agent can't answer from existing requirements
   [Plan] blocker_reported (to: coordinator, reason: missing_requirement)

3. Coordinator searches project docs
   [Coordinator] searching_project_context (query: OAuth provider)
   [Coordinator] search_failed (reason: not_found_in_docs)

4. Coordinator escalates to La Boeuf via ntfy
   [Coordinator] escalated_to_human (blocker: missing_requirement)

   📱 La Boeuf receives: "[jean-claude] 🚨 Missing Requirement"

5. La Boeuf responds: "sdlc-a3b4c5d6: Use GitHub OAuth"
   [Coordinator] human_response_received (decision: GitHub OAuth)

6. Coordinator unblocks Plan agent
   [Coordinator] agent_unblocked (agent: plan, resolution: human_decision)

7. Plan agent sends answer to Implement agent
   [Plan] clarification_provided (answer: GitHub OAuth)

8. Implement agent continues
   [Implement] resumed_work (oauth_provider: GitHub)
   [Implement] feature_completed (feature_id: auth-1)
```

**Complete Event Store Timeline:**
```sql
SELECT timestamp, agent, event_type, payload
FROM events
WHERE workflow_id = 'sdlc-a3b4c5d6'
ORDER BY timestamp;

-- Results:
10:23:15  implement    clarification_requested    {"to":"plan","question":"OAuth provider"}
10:23:16  implement    agent_waiting              {"blocked_on":"plan"}
10:23:17  plan         clarification_request_received  {"question":"OAuth provider"}
10:23:20  plan         blocker_reported           {"to":"coordinator","reason":"missing_requirement"}
10:23:21  coordinator  escalation_received        {"from":"plan","blocker":"missing_requirement"}
10:23:22  coordinator  searching_project_context  {"query":"OAuth provider"}
10:23:25  coordinator  search_failed              {"reason":"not_found_in_docs"}
10:23:26  coordinator  escalated_to_human         {"blocker":"missing_requirement"}
10:28:43  coordinator  human_response_received    {"decision":"GitHub OAuth"}
10:28:44  coordinator  agent_unblocked            {"agent":"plan"}
10:28:44  plan         agent_state_changed        {"from":"waiting_coordinator","to":"executing_task"}
10:28:45  plan         clarification_provided     {"answer":"GitHub OAuth"}
10:28:46  implement    agent_state_changed        {"from":"waiting_peer","to":"executing_task"}
10:28:47  implement    agent_state_changed        {"from":"executing_task","to":"writing_code"}
10:35:12  implement    feature_completed          {"feature_id":"auth-1"}
```

---

## Implementation Roadmap

### Overview: 4-Phase Approach Over 12 Months

| Phase | Duration | Focus | Risk | Value |
|-------|----------|-------|------|-------|
| Phase 1 | Months 1-3 | Hybrid SDLC with human escalation | Low | Immediate |
| Phase 2 | Months 4-6 | Add peer collaboration (Level 1) | Medium | High |
| Phase 3 | Months 7-9 | Full agent pool with parallelism | High | Very High |
| Phase 4 | Months 10-12 | Optimization and learning | Medium | Long-term |

---

### Phase 1: Hybrid SDLC with Limited Mailbox (Months 1-3)

**Goal:** Replace two-agent pattern with flexible SDLC subagent workflow

**What to Build:**
- 5 SDLC subagents (Plan, Implement, Test, Review, Deploy)
- Sequential orchestration (no parallelism yet)
- Fresh context per feature (preserve two-agent benefit)
- Level 3 escalation only (coordinator → La Boeuf via ntfy)
- Simple event sourcing (single timeline)

**Deliverables:**
```python
# src/jean_claude/core/subagents.py
@register_subagent("plan")
@register_subagent("implement")
@register_subagent("test")
@register_subagent("review")
@register_subagent("deploy")

# src/jean_claude/orchestration/sdlc_workflow.py
async def run_sdlc_workflow(task_description, workflow_id):
    # Plan → Implement (loop) → Test → Review → Deploy
    pass

# src/jean_claude/cli/commands/sdlc.py
jc sdlc plan "feature"
jc sdlc pipeline "feature"
```

**Success Criteria:**
- [ ] 5 SDLC subagents defined
- [ ] Sequential workflow working
- [ ] Fresh context per feature validated
- [ ] Level 3 escalation to ntfy working
- [ ] Event logging to .jc/events.db
- [ ] Replaces current two-agent pattern in `jc work`

**Risk:** Low
**Effort:** 200-300 hours
**Value:** Immediate - production-ready SDLC workflow

---

### Phase 2: Add Peer Collaboration (Months 4-6)

**Goal:** Enable agent-to-agent communication (Level 1 escalation)

**What to Build:**
- Bidirectional messaging (Implement ↔ Plan, Test ↔ Implement)
- Conversation threading in event store
- Feedback loops (Test → Implement → Test)
- Message delivery and acknowledgment
- Still sequential features (no parallelism)

**Deliverables:**
```python
# Enhanced mailbox system
async def send_message(message: Message)
async def wait_for_reply(message_id: str, timeout: int)

# Conversation tracking
class ConversationManager:
    def start_conversation(message: Message)
    def add_to_conversation(message: Message)
    def get_active_conversations()

# Database schema updates
CREATE TABLE conversations (...)
CREATE TABLE messages (...)
```

**Success Criteria:**
- [ ] Agents can ask each other questions
- [ ] Conversations tracked with thread_id
- [ ] Feedback loops working (test failures → implement → retest)
- [ ] Message delivery reliable
- [ ] Conversation summaries in dashboard

**Risk:** Medium
**Effort:** 300-400 hours
**Value:** High - true collaboration enables

---

### Phase 3: Full Agent Pool with Parallelism (Months 7-9)

**Goal:** Distributed agent pool with pipeline parallelism

**What to Build:**
- Concurrent agent pool (all agents running)
- Pipeline parallelism (test F1 while implementing F2)
- Event-sourced state (no WorkflowState.json, derive from events)
- Full mailbox routing
- Distributed event correlation
- WorkflowState locking/versioning (or full event sourcing)

**Deliverables:**
```python
# Agent pool
class AgentPool:
    async def start(workflow_id)
    async def shutdown()

# Base agent class
class SDLCAgent:
    async def run()  # Main loop: read inbox, process, send outbox

# Event-sourced state
class WorkflowState:
    @classmethod
    def from_events(workflow_id)  # Reconstruct from event log
```

**Success Criteria:**
- [ ] All agents run concurrently
- [ ] Pipeline parallelism working (overlapping work)
- [ ] State derived from events (no shared file)
- [ ] Distributed events correlated by workflow_id
- [ ] Dashboard shows parallelism (Gantt chart)
- [ ] Agents can crash and restart

**Risk:** High
**Effort:** 400-600 hours
**Value:** Very High - full architecture realized

---

### Phase 4: Optimization & Learning (Months 10-12)

**Goal:** Optimize performance and extract learnings

**What to Build:**
- Agent spawn pooling (reuse agents)
- Conversation analysis (which patterns work best?)
- Automatic remediation (coordinator learns common fixes)
- Training corpus extraction (feed back into model training)
- Performance metrics (parallelism speedup, escalation rates)

**Deliverables:**
```python
# Analytics
def analyze_conversation_patterns(workflow_id)
def calculate_parallelism_speedup()
def identify_common_escalations()

# Optimization
class AgentPoolOptimizer:
    def reuse_agents()
    def predict_resource_needs()

# Learning
def extract_training_examples(workflow_id)
```

**Success Criteria:**
- [ ] Agent reuse reduces startup overhead
- [ ] Conversation patterns documented
- [ ] Automatic remediation for common issues
- [ ] Training corpus generated
- [ ] Performance metrics dashboard

**Risk:** Medium
**Effort:** 300-400 hours
**Value:** Long-term - continuous improvement

---

## Critical Design Decisions

### Decision 1: State Synchronization Strategy

**Option A: Single WorkflowState.json with locking**
```python
with WorkflowState.lock(workflow_id):
    state = WorkflowState.load(workflow_id)
    state.mark_feature_complete(feature_id)
    state.save()
```
- ✅ Simple
- ❌ Agents block each other (bottleneck)

**Option B: Event-sourced state (no shared file)**
```python
# Agents emit events, state is derived
emit_event("feature_completed", feature_id=feature.id)
state = WorkflowState.from_events(workflow_id)
```
- ✅ No locking, fully async
- ✅ Natural fit for event sourcing
- ❌ More complex (need event replay)

**Recommendation:** Option B - full event sourcing (Phase 3)

---

### Decision 2: Message Delivery Guarantees

**Option A: At-most-once (fire and forget)**
- ✅ Fast
- ❌ Messages can be lost

**Option B: At-least-once (retry until acknowledged)**
```python
async def send_message(message: Message):
    while not acknowledged:
        await write_to_inbox(message)
        await asyncio.sleep(5)
```
- ✅ Reliable
- ❌ Duplicate messages possible
- ⚠️ Need idempotency

**Option C: Exactly-once (transactional)**
- ✅ Most reliable
- ❌ Most complex

**Recommendation:** Option B for Phase 2-3, upgrade to C for production

---

### Decision 3: Agent Lifespan

**Option A: Persistent agents (run entire workflow)**
```python
await agent_pool.start(workflow_id)  # Agents run until complete
```
- ✅ Agents maintain context
- ❌ Context bloat
- ❌ More memory

**Option B: Ephemeral agents (spawn per task)**
```python
agent = ImplementAgent.spawn(feature_id)
await agent.implement(feature)
agent.shutdown()
```
- ✅ Fresh context (like two-agent!)
- ✅ Lower memory
- ❌ More startup overhead

**Recommendation:** Option B - ephemeral Implement/Test, persistent Plan/Review/Deploy

---

### Decision 4: Coordinator Model

**Option A: Active coordinator (manages everything)**
```python
class Coordinator:
    async def run(self):
        while not done:
            await self.orchestrate()  # Route messages, monitor health
```
- ✅ Central control
- ❌ Single point of failure
- ❌ Coordinator bottleneck

**Option B: Passive coordinator (escalation handler only)**
```python
class Coordinator:
    async def run(self):
        while True:
            escalation = await self.wait_for_escalation()
            await self.handle(escalation)
```
- ✅ Agents self-organize
- ✅ Coordinator only for exceptions
- ⚠️ Message routing in agents

**Recommendation:** Option B - agents self-coordinate, coordinator handles escalations

---

## Recommendations

### Summary Comparison

| Dimension | Simple Pipeline | Hybrid SDLC | Agent Pool |
|-----------|----------------|-------------|------------|
| **Context Efficiency** | Poor | ✅ Excellent | ✅✅ Perfect |
| **Event Sourcing Fit** | ✅ Simple | ✅ Simple | ✅✅ Natural |
| **Parallelization** | ❌ Sequential | ⚠️ Sequential | ✅✅ Pipeline |
| **Cost** | High | Moderate | ✅ Optimal |
| **Complexity** | ✅ Low | ✅ Low | ❌ High |
| **Mailbox Usage** | Only escalation | Only escalation | ✅✅ Core |
| **Migration Path** | Medium | ✅ Easy | ❌ Hard |
| **Resilience** | Single point | Single point | ✅ Distributed |

### Final Recommendation: Staged Migration

**Build in 4 Phases Over 12 Months**

1. **Phase 1 (Now)** - Hybrid SDLC with human escalation
   - Low risk, immediate value
   - Replaces two-agent pattern
   - Production-ready SDLC workflow

2. **Phase 2 (Later)** - Add peer collaboration
   - Bidirectional messaging
   - Feedback loops
   - Conversation threading

3. **Phase 3 (Future)** - Full agent pool
   - Pipeline parallelism
   - Event-sourced state
   - Distributed architecture

4. **Phase 4 (Optimization)** - Learning and improvement
   - Conversation analysis
   - Automatic remediation
   - Training corpus

### Key Insights

**Event Sourcing as Communication Backbone**
In this architecture, event sourcing isn't just logging - it's the *communication protocol*. Every message between agents is an event, every state change is an event. The event store becomes a time-traveling debugger.

**Multi-Level Escalation is Organizational Intelligence**
The three-level hierarchy mimics human organizations: peers collaborate (Level 1), managers handle resources (Level 2), executives make business decisions (Level 3). Agents autonomously decide when to escalate.

**Conversation Threading Enables Learning**
By threading conversations, we build a training corpus: "Here's how agents successfully resolved OAuth ambiguity in 3 messages." Future models learn from effective collaboration patterns.

**Fresh Context is Non-Negotiable**
The two-agent pattern's killer feature is spawning fresh agents per feature. Any new architecture MUST preserve this - either through fresh subagent invocations (Phase 1) or ephemeral agent spawns (Phase 3).

---

## Next Steps

### Immediate Actions

1. **Review this document** - Validate architectural approach
2. **Choose starting phase** - Phase 1 (safe) vs Phase 3 (ambitious)
3. **Prototype single pattern** - Test one collaboration scenario
4. **Design decisions** - Make calls on state synchronization, message delivery

### Questions to Answer

1. **Timeline** - 12-month roadmap realistic? Or compress/extend?
2. **Resources** - Solo development or team effort?
3. **Risk tolerance** - Conservative (Phase 1) or aggressive (Phase 3)?
4. **Mailbox maturity** - Is current mailbox implementation ready for Phase 2?

### Files to Create

```
src/jean_claude/
├── core/
│   ├── message_types.py          # Message taxonomy
│   ├── conversations.py          # Conversation threading
│   └── agent_state.py            # Agent state machine
├── orchestration/
│   ├── sdlc_workflow.py          # Phase 1: Hybrid SDLC
│   ├── agent_pool.py             # Phase 3: Agent pool
│   └── coordinator.py            # Coordinator agent
└── cli/
    └── commands/
        └── sdlc.py               # SDLC commands

docs/
└── sdlc-agent-network-architecture.md  # This document
```

---

**End of Document**

*Generated: 2026-01-02*
*Agent: Claude Sonnet 4.5*
*Review Status: Awaiting La Boeuf approval*
