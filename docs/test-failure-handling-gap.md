# Test Failure Handling Gap in Auto-Continue Workflow

**Date:** 2026-01-02
**Status:** Critical Gap Identified
**Impact:** Workflows stop abruptly instead of requesting help

---

## The Problem

When the auto-continue workflow encounters test failures during verification, it **stops immediately** instead of using the mailbox system to request user help. This defeats the purpose of having blocker detection and pause handling infrastructure.

### What Happens Now (Broken)

```python
# In auto_continue.py lines 372-386
if not verification_result.passed:
    console.print("[red]✗ Verification failed![/red]")
    for failed_test in verification_result.failed_tests:
        console.print(f"  [red]• {failed_test}[/red]")
    console.print("[yellow]Stopping workflow due to test failures[/yellow]")
    break  # ❌ JUST STOPS - doesn't ask for help!
```

**Result:** Workflow exits, leaving user confused about what happened.

### What Should Happen (Expected)

```python
# What it SHOULD do:
if not verification_result.passed:
    # 1. Detect blocker
    blocker_detector = FailureDetector()
    blocker = blocker_detector.detect_blocker(verification_result.test_output)

    # 2. Write to INBOX
    inbox_writer = InboxWriter(workflow_dir)
    inbox_writer.write_to_inbox(Message(
        from_agent="auto_continue",
        to_agent="user",
        subject="Test Failures Detected",
        body=f"""Verification failed with {len(failed_tests)} test failures:

{format_failures(failed_tests)}

{blocker.suggestions}

What would you like me to do?
- [FIX] Attempt to fix the test failures
- [SKIP] Skip verification and continue anyway
- [STOP] Stop the workflow for manual intervention
""",
        priority=MessagePriority.URGENT
    ))

    # 3. Pause workflow
    pause_handler = WorkflowPauseHandler(project_root)
    pause_handler.pause_workflow(state, reason="Test failures require user decision")

    # 4. Break and wait for user response
    break
```

**Result:** Workflow pauses gracefully, user receives notification, can respond via mailbox.

---

## Infrastructure Already Exists (But Not Connected)

### 1. Test Failure Detection

✅ **Exists:** `src/jean_claude/core/test_failure_detector.py`
- `FailureDetector` class implementing `BlockerDetector` interface
- Detects pytest/unittest failures, assertion errors, import errors
- Extracts context (stack traces, test files, error types)
- Generates helpful suggestions

❌ **Not Used In:** `auto_continue.py` verification failure handling

### 2. Workflow Pause Handler

✅ **Exists:** `src/jean_claude/core/workflow_pause_handler.py`
- `WorkflowPauseHandler` class for graceful pausing
- Sets `waiting_for_response=True` in state
- Logs `WORKFLOW_PAUSED` event
- Docstring explicitly mentions "test failures" as a use case

❌ **Not Used In:** `auto_continue.py` verification failure handling

### 3. Mailbox System

✅ **Exists:** Full mailbox infrastructure
- `InboxWriter` for agent → user messages
- `OutboxMonitor` for user → agent responses
- MCP tools (`ask_user`, `notify_user`)
- Message serialization with priority levels

✅ **Partially Used In:** `auto_continue.py` has inbox monitoring (lines 280-315)
❌ **Missing:** Test failure doesn't trigger inbox write

### 4. Resume Handler

✅ **Exists:** `src/jean_claude/core/workflow_resume_handler.py`
- `WorkflowResumeHandler` for resuming paused workflows
- Parses user decisions (FIX, SKIP, STOP, etc.)
- Clears `waiting_for_response` flag

✅ **Used In:** `auto_continue.py` resume logic (lines 336-340)

---

## Why This Matters

### Current User Experience (Bad)

```
Running verification tests...
✗ Verification failed! Fix these tests before continuing:
  • tests/core/test_event_query.py::TestGetEventsErrorHandling::test_get_events_handles_sql_execution_error

Output:
[... test output ...]

Stopping workflow due to test failures

Workflow incomplete
Resume with: jc implement beads-jean_claude-50z
```

User sees cryptic error, has to manually investigate, manually fix, manually resume.

### Desired User Experience (Good)

```
Running verification tests...
✗ Verification failed!

📬 Agent sent message to INBOX:
   Subject: Test Failures Detected
   Priority: URGENT

   "I found 1 test failure during verification. The test
   test_get_events_handles_sql_execution_error has an AttributeError.

   Suggestions:
   - Check object attribute names and method calls
   - Verify mock object configurations

   What should I do?
   - [FIX] Let me try to fix it
   - [SKIP] Continue anyway
   - [STOP] Wait for manual fix"

⏸️  Workflow paused, waiting for your response...

To respond: jc mailbox reply
```

User gets clear explanation, helpful suggestions, and can make informed decision.

---

## The Gap

### Code Location

**File:** `src/jean_claude/orchestration/auto_continue.py`
**Lines:** 372-386 (verification failure handling)

### Missing Integration

```diff
  if not verification_result.passed:
      console.print("[red]✗ Verification failed![/red]")
      for failed_test in verification_result.failed_tests:
          console.print(f"  [red]• {failed_test}[/red]")
-     console.print("[yellow]Stopping workflow due to test failures[/yellow]")
-     break
+
+     # Detect blocker type and generate suggestions
+     from jean_claude.core.test_failure_detector import FailureDetector
+     detector = FailureDetector()
+     blocker = detector.detect_blocker(verification_result.test_output)
+
+     # Write to INBOX
+     from jean_claude.core.inbox_writer import InboxWriter
+     from jean_claude.core.message import Message, MessagePriority
+     inbox_writer = InboxWriter(workflow_dir)
+     inbox_writer.write_to_inbox(Message(
+         from_agent="auto_continue",
+         to_agent="user",
+         subject="Test Failures Detected",
+         body=format_test_failure_message(failed_tests, blocker),
+         priority=MessagePriority.URGENT
+     ))
+
+     # Pause workflow
+     pause_handler = WorkflowPauseHandler(project_root)
+     pause_handler.pause_workflow(state, "Test failures detected during verification")
+
+     console.print("[yellow]⏸️  Workflow paused, waiting for user response...[/yellow]")
+     break
```

---

## Related Components

### Error Detection Chain

```
Verification Run
    ↓
VerificationResult (has failed_tests)
    ↓
FailureDetector.detect_blocker()
    ↓
BlockerDetails (type=TEST_FAILURE)
    ↓
InboxWriter.write_to_inbox()
    ↓
WorkflowPauseHandler.pause_workflow()
    ↓
User sees message via OutboxMonitor
    ↓
User responds via /mailbox reply
    ↓
WorkflowResumeHandler.resume_workflow()
    ↓
Workflow continues based on decision
```

**Current State:** Chain breaks after `VerificationResult` ❌
**Should Be:** Full chain from detection → pause → resume ✅

---

## Implementation Checklist

- [ ] Import `FailureDetector` in `auto_continue.py`
- [ ] Import `InboxWriter`, `Message`, `MessagePriority`
- [ ] Import `WorkflowPauseHandler`
- [ ] Add blocker detection after verification failure
- [ ] Format helpful message with suggestions
- [ ] Write message to INBOX with URGENT priority
- [ ] Call `pause_workflow()` with reason
- [ ] Update console output to indicate pause (not stop)
- [ ] Test with intentionally failing tests
- [ ] Verify mailbox notification appears
- [ ] Verify workflow can resume after user response
- [ ] Update documentation with new flow

---

## Test Cases Needed

1. **Verification fails → INBOX message appears**
2. **User chooses FIX → Agent attempts to fix tests**
3. **User chooses SKIP → Workflow continues despite failures**
4. **User chooses STOP → Workflow exits cleanly**
5. **Multiple test failures → Grouped in single message**
6. **Blocker detection → Correct suggestions generated**

---

## Documentation Updates Needed

- [ ] `docs/auto-continue-workflow.md` - Add mailbox integration section
- [ ] `CLAUDE.md` - Update workflow behavior description
- [ ] `docs/ARCHITECTURE.md` - Document test failure event flow

---

## Why This Wasn't Noticed Earlier

1. **Recent feature:** Mailbox system was just implemented (during jean_claude-50z)
2. **Partial integration:** Resume logic exists but pause triggering doesn't
3. **Testing gap:** Tests for pause handler exist, but not integrated into auto_continue
4. **Documentation lag:** Architecture docs describe the ideal flow but code doesn't match

---

## Priority Assessment

**Priority:** P0 (Critical)

**Rationale:**
- Defeats purpose of autonomous agent (can't ask for help)
- Poor user experience (cryptic failures)
- Infrastructure exists but not connected (easy fix)
- Blocks effective use of auto-continue for non-trivial workflows

**Estimated Effort:** 2-4 hours
- Code changes: 1 hour
- Testing: 1 hour
- Documentation: 1 hour
- Review/refinement: 1 hour

---

## Related Issues

- Blocker detection system (fully implemented)
- Pause/resume handlers (fully implemented)
- Mailbox infrastructure (fully implemented)
- **Gap:** Integration point in auto_continue verification

---

## Next Steps

1. Create GitHub issue: "Integrate mailbox system into auto-continue test failure handling"
2. Assign to current sprint
3. Implement changes in `auto_continue.py`
4. Add integration tests
5. Update documentation
6. Test with real failing workflows
