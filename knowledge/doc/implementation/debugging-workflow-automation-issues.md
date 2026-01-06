# Debugging Workflow Automation Issues

**Date**: 2026-01-04
**Authors**: Knowledge Capturer Agent
**Status**: Completed and Verified
**Confidence**: High

## Summary

Resolved multiple critical issues blocking automated workflow execution: SSE dashboard memory leak (100+ GB), missing EventLogger integration, git pre-commit hook blocking commits, and Claude Code parent hook interference. Workflows now run successfully with proper monitoring.

## Context

Running Jean Claude CLI to develop itself (dogfooding) exposed integration issues that unit tests missed. Two parallel workflows (Mailbox and Notes projection builders) revealed problems with background execution, event logging, memory management, and git automation.

## Issues Discovered and Fixed

### Issue 1: SSE Dashboard Memory Leak

**Symptom**: Memory consumption growing to 100+ GB, system becoming unresponsive

**Impact**: Complete system failure during long-running workflows

**Root Cause**:
- Infinite `while True` loops with no timeout
- No connection limit (multiple clients could connect)
- Loading entire event files into memory
- No deque bounds on event storage

**Discovery Process**:
```bash
# Process monitoring showed memory growth
ps aux | grep "jc resume"
# 100+ GB memory, 4+ hours runtime

# Event files kept growing
ls -lh agents/*/events.jsonl
# 50+ MB files being loaded entirely into memory
```

**Solution**: Multi-part fix in `src/jean_claude/dashboard/app.py`

1. **Added 1-hour timeout per SSE connection**:
```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def sse_timeout(seconds: int = 3600):
    """Enforce timeout on SSE connections to prevent infinite loops."""
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        logger.info(f"SSE connection timed out after {seconds}s")
        raise
```

2. **Limited to 5 concurrent connections per workflow**:
```python
# Global connection tracker
active_connections: dict[str, int] = {}
MAX_CONNECTIONS_PER_WORKFLOW = 5

# Before streaming
if active_connections.get(workflow_id, 0) >= MAX_CONNECTIONS_PER_WORKFLOW:
    raise HTTPException(503, f"Max {MAX_CONNECTIONS_PER_WORKFLOW} connections")
```

3. **Bounded event storage with deque**:
```python
from collections import deque

recent_events = deque(maxlen=1000)  # Auto-drops oldest events
# Only keep last 1000 events in memory
```

4. **Stream events instead of loading entire file**:
```python
def get_recent_events(events_file: Path, max_events: int = 1000):
    """Load only recent events, not entire file."""
    recent = deque(maxlen=max_events)
    if events_file.exists():
        with open(events_file) as f:
            for line in f:
                try:
                    recent.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return list(recent)
```

**Result**:
- Memory usage: 100+ GB → <100 MB
- Connection stability: Infinite loops → 1-hour max
- Resource protection: Unlimited → 5 connections max
- Event loading: Full file → Last 1000 events

**Files Modified**:
- `src/jean_claude/dashboard/app.py` - SSE endpoint fixes

### Issue 2: Missing EventLogger Integration in jc resume

**Symptom**: No SQLite event logging when resuming workflows

**Impact**: Lost visibility into resumed workflow progress and state

**Root Cause**: `jc resume` command didn't create/pass EventLogger to `run_auto_continue()`

**Discovery Process**:
```bash
# Expected events in SQLite
sqlite3 .jc/events.db "SELECT COUNT(*) FROM events WHERE workflow_id = 'xyz';"
# 0 rows - no events being logged

# Checked resume command code
# EventLogger never instantiated
```

**Solution**: Add EventLogger integration to `src/jean_claude/cli/commands/resume.py`

```python
from jean_claude.core.events import EventLogger

# Create event logger with project root
event_logger = EventLogger(project_root=project_root)

# Pass to auto_continue
await run_auto_continue(
    state=state,
    project_root=project_root,
    event_logger=event_logger,  # Now events go to SQLite
)
```

**Key Insight**: EventLogger only needs `project_root` at initialization time. The `workflow_id` is passed when emitting events, not at construction.

**Pattern**:
```python
# Initialize once with project root
logger = EventLogger(project_root="/path/to/project")

# Use with any workflow
await logger.emit(workflow_id="abc123", event_type="feature_started", ...)
await logger.emit(workflow_id="def456", event_type="task_completed", ...)
```

**Result**:
- ✅ Events now logged to `.jc/events.db`
- ✅ Workflow progress visible in SQLite
- ✅ Consistent with `jc work` behavior

**Files Modified**:
- `src/jean_claude/cli/commands/resume.py` - EventLogger integration

### Issue 3: Git Pre-Commit Hook Blocking Automation

**Symptom**: Workflows getting stuck at "committing feature..." step for 5+ seconds per commit

**Impact**: 5.7s per commit × 15 features = 85+ seconds wasted on hooks alone

**Root Cause**: Beads pre-commit hook runs `bd sync --flush-only`, which:
1. Checks if beads daemon is running
2. If not, starts daemon (5+ second startup time)
3. Performs sync operations
4. All in foreground, blocking commit

**Discovery Process**:
```bash
# Workflow stuck on commit
tail -f agents/*/cc_raw_output.jsonl
# "Committing feature..." repeated, no progress

# Check git process
ps aux | grep git
# git commit process in D state (uninterruptible sleep)

# Test pre-commit hook speed
time git commit -m "test" --allow-empty
# real: 5.7s - way too slow for automation

# Check what hook does
cat .git/hooks/pre-commit
# Runs 'bd sync --flush-only' - requires daemon
```

**Solution**: Configure beads `sync-branch` to skip hook logic

```bash
# Set sync-branch in beads config
bd config set sync.branch beads-sync

# Hook detects sync-branch and exits early:
# .git/hooks/pre-commit checks config.yaml
# If sync.branch is set, exits with code 0 immediately
```

**Why This Works**:
- `sync-branch` tells beads to commit to a separate sync branch
- Main branch commits don't need hook's sync logic
- Hook short-circuits when sync-branch is configured
- Clean configuration solution, no code changes needed

**Result**:
```bash
# After configuration
time git commit -m "test" --allow-empty
# real: 0.02s - 285× faster!
```

**Speed Improvement**:
- Before: 5.7s per commit
- After: 0.02s per commit
- 285× faster
- 15 features: 85s → <1s

**Files Modified**:
- `.beads/config.yaml` - Added `sync.branch: beads-sync`

**Lesson**: Configuration over code changes. Beads already had the feature, just needed to enable it.

### Issue 4: Claude Code Parent Hook Interference

**Symptom**: "Stream closed" errors flooding logs when running `jc resume` in background

**Error Message**:
```
BrokenPipeError: [Errno 32] Broken pipe
StreamClosedError: Stream is closed
Error in hook execution: Communication error
```

**Impact**: Log spam, confusion about source of errors, unclear if Jean Claude hooks were broken

**Root Cause**:
- Parent Claude Code process has hooks configured in `~/.claude/settings.json`
- When `jc resume` runs in background (nohup, &), stdin/stdout are disconnected
- Parent hooks try to communicate via disconnected streams
- **Important**: These were NOT Jean Claude's hooks, they were the parent CLI's hooks

**Discovery Process**:
```bash
# Background process errors
tail -f nohup.out
# Stream closed errors appearing immediately

# Where do hooks come from?
cat ~/.claude/settings.json
# Has hooks configured for parent Claude Code

# Are these our hooks?
ls .claude/hooks/
# Empty - these are parent CLI hooks

# Test hypothesis
CLAUDE_HOOKS_DISABLED=1 nohup jc resume xyz &
# Still seeing errors - env var didn't help
```

**Solution**: Disable parent hook loading in SDK executor

```python
# src/jean_claude/core/sdk_executor.py

from claude_agent_sdk import AgentSDK

sdk = AgentSDK(
    setting_sources=[],  # Don't load ~/.claude/settings.json
    # ... other config
)
```

**Why This Works**:
- `setting_sources=[]` prevents SDK from loading parent CLI settings
- Parent hooks never execute in child processes
- Jean Claude's own hooks (if any) still work via SDK config
- Clean separation between parent CLI and Jean Claude contexts

**Result**:
- ✅ No more stream errors in logs
- ✅ Clean background execution
- ✅ Parent hooks don't interfere

**Files Modified**:
- `src/jean_claude/core/sdk_executor.py` - Added `setting_sources=[]`

**Note**: This solution works around the immediate problem but `setting_sources=[]` may not fully prevent all parent hook execution. Future investigation needed if issues recur.

### Issue 5: Missing InboxWriter Import

**Symptom**: `NameError: name 'InboxWriter' is not defined` during workflow execution

**Impact**: Workflows crashed when trying to write to agent inbox

**Root Cause**: Import statement missing in `auto_continue.py`

**Discovery Process**: Dogfooding - running `jc work` exposed the missing import during actual workflow execution

**Solution**: Add import statement

```python
# src/jean_claude/orchestration/auto_continue.py
from jean_claude.core.inbox_writer import InboxWriter
```

**Result**:
- ✅ Workflows can write inbox messages
- ✅ Agent communication works

**Files Modified**:
- `src/jean_claude/orchestration/auto_continue.py` - Added import

**Lesson**: Unit tests with mocks can miss missing imports. Integration testing (dogfooding) finds them.

## Patterns & Principles

### 1. Dogfooding Reveals Real Integration Issues

**Pattern**: Use the tool to build the tool

**Evidence**:
- Unit tests all passed
- Workflows failed in production
- Missing imports, hook conflicts, daemon timing issues only appeared during real usage

**Principle**: Integration tests are valuable but nothing beats production usage

**Reusability**: Apply to all Jean Claude development - use `jc work` to build `jc` features

### 2. Systematic Debugging Process

**Pattern**: Symptoms → Logs → Process State → Trace → Test → Fix

**Process Used**:
1. Observe symptoms (stuck workflows, memory leak)
2. Examine logs (filter signal from noise)
3. Check process state (CPU, memory, runtime via `ps`)
4. Inspect state files (workflow state, git status)
5. Trace execution flow (found blocking point)
6. Test hypothesis (pre-commit hook timing)
7. Implement solution (sync-branch configuration)

**Principle**: Systematic investigation beats random fixes

**Reusability**: Template for debugging any Jean Claude automation issue

### 3. Configuration Over Code Changes

**Pattern**: Prefer enabling existing features over writing new code

**Evidence**:
- Beads already had `sync-branch` feature
- Just needed configuration: `bd config set sync.branch beads-sync`
- No need to modify FeatureCommitOrchestrator or disable hooks

**Principle**: Cleaner, more maintainable, follows upstream best practices

**Reusability**: Check for configuration options before coding solutions

### 4. Multi-Level Event Monitoring

**Pattern**: Comprehensive observability with different granularities

**Levels Used**:
- **Process metrics**: CPU, memory, PID via `ps aux`
- **Event streams**: JSONL files for streaming/tailing
- **Database events**: SQLite for querying and analysis
- **Live activity**: `cc_raw_output.jsonl` from agent iterations
- **Application logs**: Standard Python logging

**Principle**: Different debugging needs require different observation tools

**Reusability**: Template for monitoring any Jean Claude workflow

### 5. Background Process Communication Challenges

**Pattern**: Backgrounded processes lose interactive communication

**Evidence**:
- `nohup jc resume &` disconnects stdin/stdout
- Parent hooks expecting interactive streams fail
- Stream closed errors flood logs

**Solution**: Detect background mode and skip interactive features

**Principle**: Automation contexts need fast-fail, no interactive prompts

**Reusability**: Any Jean Claude background execution should check if interactive

### 6. Memory-Efficient Event Loading

**Pattern**: Bounded collections for unbounded data

**Evidence**:
```python
from collections import deque

recent_events = deque(maxlen=1000)  # Auto-drops oldest
```

**Principle**: Use bounded data structures for streaming data

**Reusability**: Apply to any Jean Claude component loading log files

### 7. SSE Connection Resource Limits

**Pattern**: Enforce limits on long-lived connections

**Protections Added**:
- Timeout per connection (1 hour)
- Max concurrent connections (5 per workflow)
- Bounded event buffer (1000 events)
- Graceful connection cleanup

**Principle**: Never trust clients to disconnect cleanly

**Reusability**: Template for any SSE endpoint in Jean Claude

## Debugging Commands Reference

### Process Monitoring

```bash
# Find running workflows
ps aux | grep "jc resume"

# Check memory usage
ps aux | grep jc | awk '{print $4, $6, $11}'

# Monitor in real-time
watch -n 1 'ps aux | grep jc'
```

### Event Inspection

```bash
# Check event file sizes
ls -lh agents/*/events.jsonl

# Count events per workflow
wc -l agents/*/events.jsonl

# Tail live events
tail -f agents/*/cc_raw_output.jsonl

# Query SQLite events
sqlite3 .jc/events.db "SELECT * FROM events WHERE workflow_id = 'xyz' ORDER BY timestamp DESC LIMIT 10;"
```

### Git Hook Testing

```bash
# Test pre-commit hook speed
time git commit -m "test" --allow-empty

# Check what hook does
cat .git/hooks/pre-commit

# Test without hooks
git commit --no-verify -m "test"
```

### Beads Daemon

```bash
# Check daemon status
bd daemon status

# Start daemon manually
bd daemon start

# Check sync configuration
bd config get sync.branch
```

### Background Processes

```bash
# Start in background with logging
nohup jc resume workflow-id > workflow.log 2>&1 &

# Check background process
jobs
ps aux | grep "jc resume"

# Stop background process
kill $(pgrep -f "jc resume")
```

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Memory usage | 100+ GB | <100 MB |
| SSE connection limits | Unlimited | 5 per workflow |
| SSE timeout | Infinite | 1 hour |
| Event loading | Full file | Last 1000 |
| EventLogger in resume | Missing | Working |
| Git commit speed | 5.7s | 0.02s |
| Parent hook errors | Flooding logs | None |
| Workflow completion | Stuck | Running |
| Missing imports | 1 | 0 |

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `src/jean_claude/dashboard/app.py` | Added timeout, connection limits, bounded deque | Fix memory leak |
| `src/jean_claude/cli/commands/resume.py` | Added EventLogger integration | Enable SQLite logging |
| `src/jean_claude/core/sdk_executor.py` | Added `setting_sources=[]` | Prevent parent hook loading |
| `src/jean_claude/orchestration/auto_continue.py` | Added InboxWriter import | Fix missing import |
| `.beads/config.yaml` | Added `sync.branch: beads-sync` | Speed up pre-commit hook |

## Lessons Learned

### For Development

1. **Dogfooding is essential** - Unit tests can't catch integration issues
2. **Real usage reveals real problems** - Use the tool to build the tool
3. **Configuration beats code** - Check for existing features before coding
4. **Systematic debugging works** - Follow consistent investigation process

### For Memory Management

1. **Bound all collections** - Use `deque(maxlen=N)` for streaming data
2. **Enforce timeouts** - Never allow infinite loops in production
3. **Limit connections** - Protect resources from unlimited clients
4. **Stream, don't load** - Process data incrementally

### For Background Processes

1. **Disconnect from parent** - Use `setting_sources=[]` to isolate
2. **No interactive features** - Background processes can't prompt
3. **Fast-fail on issues** - Don't block waiting for unavailable resources
4. **Log comprehensively** - You can't attach a debugger

### For Git Automation

1. **Hooks can block** - Pre-commit hooks run synchronously
2. **Daemon startup is slow** - 5+ seconds to start beads daemon
3. **Configuration options exist** - Check docs before patching
4. **Test with --allow-empty** - Fast way to test commit speed

## Future Considerations

### When Running More Workflows

- Monitor SSE connection count per project
- May need to increase connection limit (currently 5)
- Consider connection pooling or multiplexing

### When Event Files Grow Larger

- Current 1000-event limit may be too small
- Could make configurable via `.jc-project.yaml`
- Consider event rotation or archival

### When Parent Hooks Change

- `setting_sources=[]` may not fully prevent execution
- Monitor for hook-related errors
- May need more aggressive isolation

### When Beads Daemon Improves

- Faster startup may make sync-branch unnecessary
- Could remove configuration and use default behavior
- Test periodically with daemon improvements

## Related Documentation

- [Pattern: SSE Resource Management](../patterns/sse-resource-management.md) *(to be created)*
- [Pattern: Background Process Isolation](../patterns/background-process-isolation.md) *(to be created)*
- [Decision: Beads Sync Branch Configuration](../decisions/beads-sync-branch.md) *(to be created)*
- [Testing: Dogfooding Workflows](../testing/dogfooding-workflows.md) *(to be created)*

## Workflows Tested

Successfully tested with:
- Mailbox projection builder workflow
- Notes projection builder workflow
- Both running in parallel for 2+ hours
- 15+ features committed per workflow
- Zero crashes, clean logs

## Questions for Future Investigation

1. **Parent Hook Isolation**: Does `setting_sources=[]` fully prevent parent hook execution, or are there edge cases?
2. **Daemon Reliability**: Can beads daemon startup time be reduced for automation contexts?
3. **FeatureCommitOrchestrator**: Should it have a `--no-verify` option for automation?
4. **Process Health Monitoring**: Should auto-continue loop track memory/CPU and self-terminate if unhealthy?
5. **Event File Rotation**: Should we implement automatic rotation when files exceed size threshold?

## Confidence Assessment

- **Memory leak fix**: HIGH - Tested, verified with `ps aux`, stable for 2+ hours
- **EventLogger integration**: HIGH - Events confirmed in SQLite database
- **Sync-branch solution**: HIGH - 0.02s commits vs 5.7s before
- **Parent hook isolation**: MEDIUM - Works but `setting_sources=[]` may have edge cases
- **InboxWriter import**: HIGH - Workflow now completes without errors

## Tags

#debugging #memory-leak #sse #event-logging #git-hooks #background-processes #dogfooding #beads-integration #workflow-automation #performance
