# Autonomous Agent Patterns

Analysis of Anthropic's autonomous coding agent quickstart and patterns applicable to Jean Claude.

## Source

Repository: `/claude-quickstarts/autonomous-coding`
Purpose: Long-running autonomous agents that code for extended periods using Claude Agent SDK

---

## Key Patterns

### 1. Two-Agent Pattern

**Problem**: Context windows have limits; long-running tasks exceed them.

**Solution**: Split work into two specialized agents:

1. **Initializer Agent** - Runs once at start
   - Analyzes entire project scope
   - Creates persistent state file (`feature_list.json`)
   - Defines ALL features and test cases upfront
   - "IT IS CATASTROPHIC TO REMOVE OR EDIT FEATURES IN FUTURE SESSIONS"

2. **Coding Agent** - Runs in loop until done
   - Reads state file each session
   - Works on ONE feature at a time
   - Updates state file when complete
   - Fresh context each iteration

**Why It Works**: Each session starts fresh with the state file as shared memory. The coding agent doesn't need to remember previous sessions—it just reads the current state.

### 2. File-Based State Machine

**Pattern**: Use a JSON file as the source of truth for workflow progress.

```json
{
  "features": [
    {
      "name": "User Authentication",
      "status": "completed",  // or "in_progress", "not_started"
      "test_file": "tests/test_auth.py",
      "tests_passing": true
    }
  ],
  "current_feature_index": 2,
  "iteration_count": 15
}
```

**Benefits**:
- Survives context resets
- Human-readable for debugging
- Version controllable
- No external dependencies (no database)

### 3. Verification-First Approach

**Pattern**: Before starting new work, verify existing work still passes.

From `coding_prompt.md`:
```
## STEP 1: GET YOUR BEARINGS (MANDATORY)

Before doing ANYTHING:
1. Read feature_list.json
2. Run ALL existing tests
3. If any test fails → FIX IT FIRST (don't move to new features)
4. Only after green → proceed to next feature
```

**Why It Works**: Prevents regression cascades. Each session validates the entire codebase before adding complexity.

### 4. Defense-in-Depth Security

Three layers of protection for autonomous execution:

**Layer 1: Sandbox** (environment level)
- Docker container isolation
- Network restrictions
- Filesystem boundaries

**Layer 2: Tool Permissions** (SDK level)
```python
allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
```

**Layer 3: Command Allowlist** (hook level)
```python
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "wc", "grep",
    "cp", "mkdir", "chmod", "npm", "node",
    "git", "ps", "lsof", "sleep", "pkill"
}
```

**Implementation**: Pre-tool-use hook validates bash commands:
```python
async def bash_security_hook(input_data, tool_use_id=None, context=None):
    command = input_data.get("command", "")
    base_command = extract_base_command(command)
    if base_command not in ALLOWED_COMMANDS:
        return {"decision": "block", "reason": f"Command not allowed: {base_command}"}
    return {"decision": "allow"}
```

### 5. Auto-Continue Loop

**Pattern**: Agent runs until a termination condition, not a fixed number of turns.

```python
async def run_autonomous_agent(project_dir, model, max_iterations):
    iteration = 0
    while iteration < max_iterations:
        client = create_client(project_dir, model)
        async with client:
            status, response = await run_agent_session(client, prompt, project_dir)

        if status == "completed":
            break
        elif status == "continue":
            await asyncio.sleep(AUTO_CONTINUE_DELAY_SECONDS)
            iteration += 1
        elif status == "error":
            handle_error(response)
            break
```

**Termination Conditions**:
- All features marked complete in state file
- Max iterations reached (safety limit)
- Unrecoverable error
- User interrupt

### 6. Feature-Based Progress (Not Test Count)

**Key Insight**: Progress is measured by features completed, not arbitrary test counts.

**Anti-Pattern** (from original):
> "Write a Python application with 200 tests"

**Better Pattern**:
```json
{
  "features": [...],
  "total_features": 12,
  "completed_features": 7,
  "progress_percentage": 58.3
}
```

**Why**:
- Features are meaningful units of work
- Test count varies by feature complexity
- Users understand feature progress better than test counts

### 7. Prompt Engineering for Long-Running Tasks

**Clear Sections**: Use markdown headers and numbered steps
```markdown
## PHASE 1: INITIALIZATION (DO NOT SKIP)
## PHASE 2: IMPLEMENTATION
## PHASE 3: VERIFICATION
```

**Explicit Warnings**: Emphasize critical behaviors
```markdown
⚠️ CRITICAL: Never skip verification step
IT IS CATASTROPHIC TO: [list of forbidden actions]
```

**One Task at a Time**:
```markdown
Work on EXACTLY ONE feature per session.
Do not start the next feature until current is complete.
```

**State File as Contract**:
```markdown
The feature_list.json is your ONLY source of truth.
NEVER rely on memory from previous sessions.
```

---

## Application to Jean Claude

### Phase 2 Implementation Status

1. **✅ SDK Integration Complete**
   - Using `claude_code_sdk` for all new executions
   - Streaming support with proper async handling
   - Full telemetry and observability

2. **✅ Security Hooks Implemented**
   - Pre-tool-use validation for bash commands
   - Three workflow types with graduated allowlists:
     - `readonly`: Inspection only (ls, cat, git status)
     - `development`: Common dev tools (git, uv, pytest, npm)
     - `testing`: Development + test runners (coverage, tox)
   - Configurable per-workflow restrictions
   - Smart command parsing (handles paths, env vars, pipes)

3. **Add Auto-Continue Workflows**
   - Long-running chore/feature/bug workflows
   - State persistence in `agents/{adw_id}/workflow_state.json`
   - Verification-first on resume

4. **Feature-Based Progress Tracking**
   - Replace arbitrary counts with feature lists
   - Progress visualization in CLI
   - Resume capability

5. **Two-Agent Pattern for Complex Features**
   - Planning agent (creates feature list)
   - Implementation agent (executes one at a time)
   - State handoff between sessions

---

## Code Snippets to Adapt

### SDK Client Setup

```python
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions

def create_client(working_dir: Path, model: str) -> ClaudeSDKClient:
    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            working_directory=str(working_dir),
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher="Bash", hooks=[bash_security_hook])
                ]
            },
            max_turns=1000,
        )
    )
```

### State File Structure

```python
from pydantic import BaseModel
from typing import Literal

class Feature(BaseModel):
    name: str
    description: str
    status: Literal["not_started", "in_progress", "completed"]
    test_file: str | None = None
    tests_passing: bool = False

class WorkflowState(BaseModel):
    workflow_id: str
    workflow_type: str
    features: list[Feature]
    current_feature_index: int = 0
    iteration_count: int = 0

    @property
    def progress_percentage(self) -> float:
        completed = sum(1 for f in self.features if f.status == "completed")
        return (completed / len(self.features)) * 100 if self.features else 0
```

### Security Hook

```python
ALLOWED_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "wc",
    "cp", "mkdir", "touch", "chmod",
    "git", "uv", "python", "pytest",
    "npm", "node", "npx"
}

async def bash_security_hook(input_data, tool_use_id=None, context=None):
    command = input_data.get("command", "")
    parts = shlex.split(command)
    if not parts:
        return {"decision": "allow"}

    base_command = parts[0].split("/")[-1]  # Handle full paths

    if base_command not in ALLOWED_COMMANDS:
        return {
            "decision": "block",
            "reason": f"Command '{base_command}' not in allowlist"
        }
    return {"decision": "allow"}
```

---

## References

- [Claude Agent SDK Documentation](https://docs.anthropic.com/en/docs/claude-agent-sdk)
- [Anthropic Quickstarts](https://github.com/anthropics/anthropic-quickstarts)
- Original source: `/claude-quickstarts/autonomous-coding/`
