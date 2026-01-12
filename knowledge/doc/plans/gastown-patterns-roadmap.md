# Gastown Patterns Adoption Roadmap

**Vision**: Evolve Jean Claude from workflow automation tool to persistent workspace manager for 20-30 concurrent AI agents

**Source**: Comprehensive analysis of Steve Yegge's Gastown (January 2026)

**Status**: Strategic planning document - living roadmap

---

## Strategic Vision Shift

**Original Jean Claude Model**:
- Ephemeral workflow execution (start → complete → terminate)
- 2-agent pattern (Opus plans, Sonnet implements)
- Single-project focus
- No agent persistence

**Target Gastown-Inspired Model**:
- Persistent workspace with 20-30 concurrent agents
- Multi-project coordination
- Agent lifecycle management
- Crash recovery and session persistence
- Inter-agent communication
- Role-based agent taxonomy

---

## Pattern Categories

1. [Architecture & Design](#1-architecture--design-patterns) (10 patterns)
2. [Beads Integration](#2-beads-integration-patterns) (8 patterns)
3. [CLI & UX](#3-cli--ux-patterns) (10 patterns)
4. [Agent Patterns](#4-agent-patterns--ai-integration) (12 patterns)
5. [Testing & Quality](#5-testing--quality-patterns) (10 patterns)

**Total**: 50 patterns identified

---

## Complexity & Risk Ratings

- 🟢 **LOW**: Straightforward implementation, low risk, well-understood
- 🟡 **MEDIUM**: Moderate complexity, some architectural changes, manageable risk
- 🟠 **HIGH**: Significant refactoring, cross-cutting concerns, careful planning needed
- 🔴 **CRITICAL**: Core architecture changes, high risk, requires extensive testing

**Priority Ratings**:
- **P0**: Critical - Security/reliability issues or foundational requirements
- **P1**: High - Significant value, enables other patterns
- **P2**: Medium - Valuable but not blocking
- **P3**: Low - Nice to have, future enhancement
- **P4**: Experimental - Research/exploration phase

---

## 1. Architecture & Design Patterns

### 1.1 Agent Identity System ⭐

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P0 (FOUNDATIONAL)

**Description**: Hierarchical agent addressing system (`workspace/project/role/name`)

**Gastown Pattern**:
```bash
BD_ACTOR="gastown/polecats/toast"
GIT_AUTHOR_NAME="gastown/polecats/toast"
GIT_AUTHOR_EMAIL="steve@example.com"  # Human owner
```

**Jean Claude Implementation**:
```python
# src/jean_claude/core/identity.py
class AgentIdentity:
    workspace: str              # e.g., "main"
    project: str | None         # e.g., "jean-claude"
    role: AgentRole            # coordinator, worker, specialist
    name: str | None           # e.g., "coder-1"

    @property
    def address(self) -> str:
        """Slash-separated address: workspace/project/role/name"""
        parts = [self.workspace]
        if self.project:
            parts.append(self.project)
        parts.append(self.role.value)
        if self.name:
            parts.append(self.name)
        return "/".join(parts)
```

**Benefits**:
- Debugging: "Which agent broke this?"
- Auditing: Track all work by specific agent
- Performance: Measure agent effectiveness
- Compliance: Clear attribution chain

**Dependencies**: None (foundational)

**Integration Points**:
- Set `GIT_AUTHOR_NAME` in `core/agent.py`
- Log identity in all events (`core/events.py`)
- Track in workflow state (`core/state.py`)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 1.2 Agent Taxonomy

**Status**: Partial (has initializer/coder roles)
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Clear role-based agent types with lifecycle distinctions

**Gastown Taxonomy**:
| Type | Scope | Persistence | Purpose |
|------|-------|-------------|---------|
| Mayor | Town-wide | Persistent | Cross-project coordinator |
| Deacon | Town-wide | Persistent | Daemon & monitoring |
| Witness | Per-rig | Persistent | Worker lifecycle management |
| Refinery | Per-rig | Persistent | Merge queue processor |
| Polecat | Per-task | Ephemeral | Task-specific workers |

**Jean Claude Proposed Taxonomy**:
```python
class AgentRole(Enum):
    COORDINATOR = "coordinator"    # Cross-workspace (like Mayor)
    SUPERVISOR = "supervisor"      # Per-project monitoring (like Witness)
    WORKER = "worker"             # Task execution (like Polecat)
    SPECIALIST = "specialist"     # Capability-specific (refinery, etc.)

class AgentLifecycle(Enum):
    PERSISTENT = "persistent"     # Long-lived sessions
    EPHEMERAL = "ephemeral"      # Spawn → work → cleanup
    ON_DEMAND = "on_demand"      # Start when needed, idle timeout
```

**Benefits**:
- Clear separation of concerns
- Predictable agent behavior
- Easier debugging and monitoring
- Supports scaling to 20-30 agents

**Dependencies**: Agent Identity System (1.1)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 1.3 Manager Pattern

**Status**: Not implemented (scattered functions)
**Complexity**: 🟠 HIGH (refactoring)
**Priority**: P1

**Description**: Centralize domain operations behind manager interfaces

**Gastown Example**:
```go
type RigManager struct {
    townRoot string
    config   *config.RigsConfig
}

func (m *RigManager) DiscoverRigs() ([]*Rig, error)
func (m *RigManager) GetRig(name string) (*Rig, error)
func (m *RigManager) CreateRig(...) error
```

**Jean Claude Implementation**:
```python
# src/jean_claude/core/managers/workflow_manager.py
class WorkflowManager:
    def __init__(self, workspace_root: Path, event_logger: EventLogger):
        self.workspace_root = workspace_root
        self.event_logger = event_logger

    def create_workflow(self, workflow_id: str, ...) -> WorkflowState
    def get_workflow(self, workflow_id: str) -> WorkflowState
    def list_workflows(self, status: str = None) -> List[WorkflowState]
    def delete_workflow(self, workflow_id: str) -> None

# Similar managers:
# - AgentManager (spawn, monitor, kill agents)
# - ProjectManager (multi-project coordination)
# - NotesManager (already exists as notes_api.py)
# - BeadsManager (wrap all beads operations)
```

**Benefits**:
- Centralized business logic
- Easier testing (mock manager interface)
- Clear API boundaries
- Supports dependency injection

**Dependencies**: None (but enables other patterns)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH (architectural foundation)

---

### 1.4 State Layer Separation

**Status**: Partial (has events.db + state.json)
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Clear separation of configuration, operational, runtime, and event state

**Gastown Layers**:
1. **Configuration**: TOML/JSON (static, version-controlled)
2. **Operational**: Beads (dynamic, git-backed, survives crashes)
3. **Runtime**: Marker files (ephemeral, fast checks)
4. **Event**: Immutable audit trail

**Jean Claude Proposed Structure**:
```python
class StateType(Enum):
    CONFIGURATION = "configuration"   # Static settings
    OPERATIONAL = "operational"       # Dynamic workflow state
    RUNTIME = "runtime"               # Ephemeral session data
    EVENT = "event"                   # Audit trail

# File locations
Configuration:   .jc-project.yaml              # Static
                 .jc/workspace/config.yaml     # Workspace settings
Operational:     .jc/state/workflows.json      # Active workflows
                 .jc/state/agents.json         # Agent registry
Runtime:         .jc/runtime/active_workflow   # Symlink to current
                 .jc/runtime/locks/*.lock      # Session locks
Event:           .jc/events.db                 # Append-only
```

**Benefits**:
- Easier debugging (know where to look)
- Clear persistence requirements
- Better performance (runtime checks are fast)
- Supports multi-workspace architecture

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 1.5 Two-Level Hierarchy (Workspace/Project)

**Status**: Not implemented (single-project only)
**Complexity**: 🟠 HIGH
**Priority**: P2

**Description**: Organizational vs implementation separation

**Gastown Pattern**:
```
Town Level (~/gt/)              # Cross-project coordination
├── .beads/                    # Town-level issues (hq-* prefix)
├── mayor/                     # Global coordinator
└── Rigs/                      # Individual projects
    ├── gastown/
    │   ├── .beads/            # Project-level (gt-* prefix)
    │   └── polecats/
    └── myproject/
```

**Jean Claude Proposed**:
```
Workspace (~/.jc/workspaces/main/)
├── config.yaml                # Workspace settings
├── state/                     # Cross-project state
│   ├── workflows.json
│   └── agents.json
├── projects/                  # Individual projects
│   ├── jean-claude/
│   │   ├── .jc-project.yaml
│   │   ├── agents/
│   │   └── specs/
│   └── my-app/
│       └── ...
└── events.db                  # Unified event store
```

**Benefits**:
- Cross-project workflows
- Shared agent pool
- Unified monitoring
- Resource optimization

**Dependencies**: State Layer Separation (1.4), Manager Pattern (1.3)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 1.6 Protocol Pattern (Typed Messages)

**Status**: Partial (has Message model, not protocol-level)
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Strongly-typed inter-agent messages with payloads

**Gastown Example**:
```go
type MessageType string

const (
    TypeMergeReady    MessageType = "MERGE_READY"
    TypeMergeFailed   MessageType = "MERGE_FAILED"
)

type MergeReadyPayload struct {
    Branch    string
    Issue     string
    Polecat   string
    Timestamp time.Time
}
```

**Jean Claude Implementation**:
```python
# src/jean_claude/core/protocol.py
class ProtocolMessageType(Enum):
    WORKFLOW_READY = "workflow_ready"
    WORKFLOW_COMPLETE = "workflow_complete"
    FEATURE_COMPLETE = "feature_complete"
    AGENT_STUCK = "agent_stuck"
    NEEDS_HUMAN = "needs_human"
    HANDOFF_REQUEST = "handoff_request"

@dataclass
class WorkflowReadyPayload:
    workflow_id: str
    features: List[Feature]
    estimated_duration: int

@dataclass
class ProtocolMessage:
    type: ProtocolMessageType
    from_agent: str  # Agent address
    to_agent: str
    payload: dict
    timestamp: datetime
```

**Benefits**:
- Type-safe agent communication
- Clear semantics
- Easier debugging
- Protocol versioning

**Dependencies**: Agent Identity System (1.1)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH (enables agent coordination)

---

### 1.7 Molecule Pattern (Workflow as Data)

**Status**: Partial (has WorkflowState, not templates)
**Complexity**: 🟠 HIGH
**Priority**: P2

**Description**: Workflows are data structures, not code

**Gastown Pattern**:
```
Formula (TOML template)
    ↓ bd cook
Protomolecule (frozen template)
    ↓ bd mol pour
Molecule (live workflow with steps as beads)
    ↓ execute steps
    ↓ bd mol squash
Digest (completion record)
```

**Jean Claude Proposed**:
```python
# src/jean_claude/workflows/templates/two_agent.toml
name = "two_agent"
description = "Opus plans, Sonnet implements"

[[steps]]
id = "initialize"
agent_role = "coordinator"
action = "analyze_and_plan"

[[steps]]
id = "implement"
agent_role = "worker"
action = "implement_features"
depends_on = ["initialize"]
loop_until = "all_features_complete"

# Load and execute
workflow = WorkflowTemplate.load("two_agent")
instance = workflow.instantiate(workflow_id="abc123")
instance.execute_step("initialize")  # Reentrant!
```

**Benefits**:
- Survives crashes (can restart mid-workflow)
- Multiple agents can work same workflow
- Workflows are composable
- Easier to test (data vs code)

**Dependencies**: None (but benefits from State Layer Separation)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH (enables complex workflows)

---

### 1.8 Wisp Pattern (Ephemeral Workflows)

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P3

**Description**: Separate persistent from ephemeral workflows

**Gastown Pattern**:
- **Molecule**: Permanent record (features, bugs, releases)
- **Wisp**: Ephemeral operations (health checks, patrol loops)

**Jean Claude Implementation**:
```python
class WorkflowType(Enum):
    PERSISTENT = "persistent"   # Feature work, survives restart
    EPHEMERAL = "ephemeral"     # Health checks, monitoring

class WorkflowState:
    type: WorkflowType = WorkflowType.PERSISTENT

    def should_persist(self) -> bool:
        return self.type == WorkflowType.PERSISTENT
```

**Benefits**:
- Prevent operational noise in audit trail
- Faster cleanup (wisps auto-delete)
- Clear intent

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM (useful for monitoring agents)

---

### 1.9 Degraded Mode Operation

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P3

**Description**: Detect capabilities and adapt behavior

**Gastown Pattern**:
```bash
GT_DEGRADED=true  # Set when tmux unavailable

# Agents check and adapt:
if degraded:
    # No interactive interrupts
    # Focus on beads/git state only
```

**Jean Claude Implementation**:
```python
# src/jean_claude/core/capabilities.py
class CapabilityDetector:
    @staticmethod
    def has_git() -> bool

    @staticmethod
    def has_beads() -> bool

    @staticmethod
    def has_network() -> bool

    @staticmethod
    def has_dashboard() -> bool

# Adjust workflows
if not capabilities.has_beads():
    # Fall back to local state only
```

**Benefits**:
- Graceful degradation
- Works in restricted environments
- Better error messages

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW (nice to have)

---

### 1.10 Handoff System

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P1 (for persistent agents)

**Description**: Explicit session cycling with context preservation

**Gastown Pattern**:
```bash
# Agent triggers handoff
gt handoff

# Daemon respawns session
tmux kill-session -t session-name
gt agent spawn --resume-from-hook

# New session auto-primes
gt prime  # Loads work from hook
```

**Jean Claude Implementation**:
```python
# CLI: jc handoff workflow-abc --message "Completed auth module"

# Implementation:
def handoff(workflow_id: str, message: str):
    # 1. Save checkpoint
    state = workflow_manager.get_workflow(workflow_id)
    state.save_checkpoint(message)

    # 2. Signal daemon to restart agent
    agent_manager.request_restart(
        agent_id=state.current_agent,
        continuation=state.checkpoint
    )

    # 3. New agent picks up from checkpoint
    new_agent = agent_manager.spawn(
        role=state.current_agent_role,
        resume_from=state.checkpoint
    )
```

**Benefits**:
- Prevents context bloat
- Fresh perspective on problems
- Supports long-running workflows

**Dependencies**: Hook Persistence (4.1), Agent Manager (1.3)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL (for persistent agents)

---

## 2. Beads Integration Patterns

### 2.1 Input Validation ⚠️

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P0 (SECURITY CRITICAL)

**Description**: Validate all beads IDs to prevent command injection

**Gastown Fix**: gt-l1xsa (command injection vulnerability)

**Implementation**:
```python
# src/jean_claude/core/beads.py
import re

BEADS_ID_PATTERN = re.compile(r'^[a-z]{2,4}-[a-z0-9]+$', re.IGNORECASE)

def validate_beads_id(task_id: str) -> bool:
    """Prevent command injection attacks."""
    if not BEADS_ID_PATTERN.match(task_id):
        raise ValueError(
            f"Invalid beads ID format: {task_id}. "
            f"Must match pattern: <prefix>-<id>"
        )
    return True

# Update all functions
def fetch_beads_task(task_id: str) -> BeadsTask:
    validate_beads_id(task_id)  # Add this line
    # ... rest of function
```

**Benefits**:
- Prevents command injection
- Input sanitization
- Security hardening

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ CRITICAL

---

### 2.2 --no-daemon Flag

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P0 (RELIABILITY)

**Description**: Disable beads daemon for all operations

**Gastown Pattern**:
```go
cmd := exec.Command("bd", "--no-daemon", "show", id, "--json")
```

**Implementation**:
```python
def _run_bd_command(args: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Run bd command with --no-daemon for reliability."""
    full_args = ['bd', '--no-daemon'] + args
    return subprocess.run(
        full_args,
        capture_output=True,
        text=True,
        check=True,
        **kwargs
    )
```

**Benefits**:
- Avoids IPC overhead
- Prevents race conditions
- More reliable

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 2.3 BEADS_DIR Environment Variable

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: Explicit database path for multi-project support

**Gastown Pattern**:
```go
cmd.Env = append(os.Environ(), "BEADS_DIR="+beadsDir)
```

**Implementation**:
```python
def _run_bd_command(
    args: List[str],
    beads_dir: Optional[Path] = None,
    **kwargs
) -> subprocess.CompletedProcess:
    full_args = ['bd', '--no-daemon'] + args

    env = kwargs.pop('env', os.environ.copy())
    if beads_dir:
        env['BEADS_DIR'] = str(beads_dir)

    return subprocess.run(full_args, env=env, **kwargs)
```

**Benefits**:
- Explicit database selection
- Supports multi-project
- Prevents prefix mismatches

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 2.4 Beads Directory Resolution

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Follow `.beads/redirect` files for shared databases

**Gastown Pattern**:
```go
func ResolveBeadsDir(projectRoot string) string {
    beadsDir := filepath.Join(projectRoot, ".beads")
    redirectFile := filepath.Join(beadsDir, "redirect")

    if data, err := os.ReadFile(redirectFile); err == nil {
        return filepath.Join(projectRoot, string(data))
    }

    return beadsDir
}
```

**Implementation**:
```python
def resolve_beads_dir(project_root: Path) -> Path:
    """Follow .beads/redirect if present."""
    beads_dir = project_root / ".beads"
    redirect_file = beads_dir / "redirect"

    if redirect_file.exists():
        redirect_path = redirect_file.read_text().strip()
        if redirect_path:
            return (project_root / redirect_path).resolve()

    return beads_dir
```

**Benefits**:
- Enables shared beads databases
- Supports town/rig architecture
- Future-proofs multi-project

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 2.5 Formula Support (Workflow Templates)

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P2

**Description**: TOML-based workflow templates

**Gastown Pattern**:
```toml
formula = "shiny"
description = "Design before code, review before ship"

[[steps]]
id = "design"
description = "Think about architecture"

[[steps]]
id = "implement"
needs = ["design"]
```

**Implementation**:
```python
# src/jean_claude/core/formula.py
from pydantic import BaseModel
import tomli

class FormulaStep(BaseModel):
    id: str
    title: str
    description: str
    needs: List[str] = []

class Formula(BaseModel):
    formula: str
    description: str
    vars: Dict[str, FormulaVariable] = {}
    steps: List[FormulaStep] = []

    @classmethod
    def from_file(cls, path: Path) -> "Formula":
        with open(path, 'rb') as f:
            data = tomli.load(f)
        return cls(**data)

    def instantiate(self, variables: Dict[str, str]) -> str:
        """Generate markdown spec from formula."""
        # Validate + expand template
```

**Benefits**:
- Structured workflows
- Reusable templates
- Variable substitution
- Dependency tracking

**Dependencies**: Molecule Pattern (1.7)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 2.6 Prefix-Based Routing

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2 (multi-project feature)

**Description**: Route commands based on issue ID prefix

**Gastown Pattern**:
```
Issue ID: gt-123 → gastown/.beads
Issue ID: hq-789 → town/.beads
```

**Implementation**: Not needed until multi-project support

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM (future multi-project)

---

### 2.7 Agent Beads (Lifecycle Tracking)

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P3

**Description**: Track agent lifecycle in Beads itself

**Note**: Jean Claude's event store (.jc/events.db) is better suited for this. Don't duplicate.

**Applicability to Workspace Manager**: ⭐ LOW (use events.db instead)

---

### 2.8 Delegation Tracking

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P4

**Description**: Track work delegation and credit attribution

**Note**: Not in Jean Claude's scope currently.

**Applicability to Workspace Manager**: ⭐ LOW (future consideration)

---

## 3. CLI & UX Patterns

### 3.1 Command Grouping

**Status**: Not implemented (flat structure)
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: Organize commands into logical groups

**Gastown Pattern**:
```go
rootCmd.AddGroup(
    &cobra.Group{ID: GroupWork, Title: "Work Management:"},
    &cobra.Group{ID: GroupAgents, Title: "Agent Management:"},
)
```

**Implementation**:
```python
# src/jean_claude/cli/main.py
@click.group("workflow")
def workflow_commands():
    """Workflow execution and management"""

@click.group("project")
def project_commands():
    """Project setup and configuration"""

@click.group("agent")
def agent_commands():
    """Agent management and monitoring"""

cli.add_command(workflow_commands)
cli.add_command(project_commands)
cli.add_command(agent_commands)
```

**Benefits**:
- Clearer help output
- Better discoverability
- Logical organization

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 3.2 Standard Style Module

**Status**: Partial (inconsistent Rich usage)
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: Consistent styled output across all commands

**Implementation**:
```python
# src/jean_claude/cli/style.py
from rich.console import Console
from rich.theme import Theme

THEME = Theme({
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "blue",
    "dim": "dim",
})

console = Console(theme=THEME)

# Standard prefixes
SUCCESS = "[success]✓[/success]"
WARNING = "[warning]⚠[/warning]"
ERROR = "[error]✗[/error]"
INFO = "[info]→[/info]"

def print_success(message: str):
    console.print(f"{SUCCESS} {message}")

def print_error(message: str):
    console.print(f"{ERROR} {message}")
```

**Benefits**:
- Professional polish
- Consistent user experience
- Scannable output

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 3.3 Status Symbols

**Status**: Not implemented (text-only)
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: Unicode symbols for status visualization

**Gastown Pattern**:
```
✓ gt-123: Add auth middleware [completed]
▶ gt-456: Update tests [in_progress] @worker (12m)
○ gt-789: Documentation [not_started]
```

**Implementation**:
```python
STATUS_SYMBOLS = {
    "completed": "✓",
    "in_progress": "▶",
    "not_started": "○",
    "failed": "✗",
    "blocked": "⊘",
}

def format_feature_status(feature: Feature) -> str:
    symbol = STATUS_SYMBOLS[feature.status]
    return f"{symbol} {feature.name} [{feature.status}]"
```

**Benefits**:
- Quick visual scanning
- Professional appearance
- Clear status at a glance

**Dependencies**: Standard Style Module (3.2)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 3.4 Numeric Shortcuts

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P2

**Description**: Reference workflows by number instead of UUID

**Gastown Pattern**:
```bash
gt convoy list
# 1. hq-cv-abc: Feature X
# 2. hq-cv-xyz: Bugfix

gt convoy status 1  # Resolves to hq-cv-abc
```

**Implementation**:
```python
# ~/.jc/recent_workflows (stores last 10)
def resolve_workflow_ref(ref: str) -> str:
    if ref.isdigit():
        recent = load_recent_workflows()
        idx = int(ref) - 1
        if 0 <= idx < len(recent):
            return recent[idx]
    return ref  # Assume it's a workflow ID
```

**Benefits**:
- Convenience (no UUID typing)
- Faster CLI usage
- Better UX

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

### 3.5 Fuzzy Matching

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: "Did you mean?" suggestions for typos

**Implementation**:
```python
# Use difflib.get_close_matches
from difflib import get_close_matches

def suggest_command(typo: str, commands: List[str]) -> List[str]:
    return get_close_matches(typo, commands, n=3, cutoff=0.6)

# In error handler:
if unknown_command:
    suggestions = suggest_command(command, valid_commands)
    if suggestions:
        console.print(f"\n  Did you mean?\n")
        for s in suggestions:
            console.print(f"    • {s}")
```

**Benefits**:
- Typo tolerance
- Better user experience
- Helpful errors

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

### 3.6 JSON Output Support

**Status**: Partial (some commands only)
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: All display commands support `--json` flag

**Implementation**:
```python
@click.command()
@click.option('--json', 'output_json', is_flag=True)
def status(output_json: bool):
    data = get_workflow_status()

    if output_json:
        import json
        print(json.dumps(data, indent=2))
    else:
        # Rich formatted output
        print_status(data)
```

**Benefits**:
- Scriptable
- Integration with dashboards
- Automation-friendly

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 3.7 Interactive TUI Mode

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Interactive terminal UI for live monitoring

**Implementation**:
```python
# Using Rich Live or Textual
from rich.live import Live
from rich.table import Table

@click.command()
@click.option('--follow', is_flag=True)
def status(follow: bool):
    if follow:
        with Live(generate_status_table(), refresh_per_second=4) as live:
            while True:
                live.update(generate_status_table())
                time.sleep(0.25)
    else:
        print(generate_status_table())
```

**Benefits**:
- Real-time monitoring
- No manual refresh
- Better visibility

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH (for monitoring 20-30 agents)

---

### 3.8 Context-Aware Errors

**Status**: Partial
**Complexity**: 🟢 LOW
**Priority**: P2

**Description**: Show exact command path and actionable next steps

**Implementation**:
```python
def format_error(command_path: str, error: str) -> str:
    return (
        f"{error}\n\n"
        f"Run '{command_path} --help' for usage information"
    )
```

**Benefits**:
- Clearer errors
- Actionable guidance
- Better UX

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW

---

### 3.9 Silent Exit Codes

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P3

**Description**: Exit codes for shell scripting

**Implementation**:
```python
# Exit codes:
# 0: Success/complete
# 1: In progress
# 2: Failed
# 3: Not found

if output_json:
    sys.exit(0 if workflow.is_complete() else 1)
```

**Benefits**:
- Shell integration
- Scriptable
- CI/CD friendly

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW

---

### 3.10 Dashboard Auto-Open

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P3

**Description**: Auto-open browser when starting dashboard

**Implementation**:
```python
@click.command()
@click.option('--open', is_flag=True)
def dashboard(open: bool):
    start_dashboard()
    if open:
        import webbrowser
        webbrowser.open('http://localhost:8000')
```

**Benefits**:
- Convenience
- Better UX

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW

---

## 4. Agent Patterns & AI Integration

### 4.1 Hook Persistence ⭐

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P0 (CRITICAL for persistent agents)

**Description**: Persistent work assignment that survives crashes

**Gastown Pattern**:
```bash
# Attach work to agent's hook
gt mol attach <molecule-id>

# Check what's on hook
gt hook  # Shows current assignment

# Work persists across crashes/restarts
```

**Jean Claude Implementation**:
```python
# ~/.jc/runtime/hooks/{agent_id} (symlink)
# Points to: ~/.jc/state/workflows/{workflow_id}/state.json

class HookManager:
    def attach(self, agent_id: str, workflow_id: str):
        """Attach workflow to agent's hook."""
        hook_file = self.runtime_dir / "hooks" / agent_id
        target = self.state_dir / "workflows" / workflow_id / "state.json"
        hook_file.symlink_to(target)

    def get_hook(self, agent_id: str) -> Optional[str]:
        """Get agent's current work assignment."""
        hook_file = self.runtime_dir / "hooks" / agent_id
        if hook_file.exists():
            return hook_file.resolve().parent.name  # workflow_id

    def detach(self, agent_id: str):
        """Clear agent's hook."""
        hook_file = self.runtime_dir / "hooks" / agent_id
        hook_file.unlink(missing_ok=True)

# On agent spawn/restart:
workflow_id = hook_manager.get_hook(agent_id)
if workflow_id:
    # Resume from hook
    state = workflow_manager.get_workflow(workflow_id)
    agent.resume(state)
```

**Benefits**:
- Work survives crashes
- Clear assignment tracking
- Enables automatic recovery
- Supports persistent agents

**Dependencies**: State Layer Separation (1.4)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 4.2 Agent Session Management

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P0 (for persistent workspace)

**Description**: Spawn, monitor, and manage persistent agent sessions

**Gastown Pattern**:
- Mayor/Witness/Refinery: Long-lived tmux sessions
- Polecats: Spawn → work → cleanup
- Automatic restart on crash

**Jean Claude Implementation**:
```python
# src/jean_claude/core/managers/agent_manager.py
class AgentManager:
    def spawn(
        self,
        role: AgentRole,
        identity: AgentIdentity,
        resume_from: Optional[dict] = None
    ) -> AgentSession:
        """Spawn new agent session."""
        session = AgentSession(
            agent_id=identity.address,
            role=role,
            started_at=datetime.now()
        )

        # Attach to hook if resuming
        if resume_from:
            hook_manager.attach(identity.address, resume_from['workflow_id'])

        # Start agent process (SDK execution)
        process = self._start_agent_process(session)

        self.sessions[identity.address] = session
        return session

    def monitor(self, agent_id: str) -> AgentHealth:
        """Check agent health."""
        session = self.sessions.get(agent_id)
        if not session:
            return AgentHealth.NOT_RUNNING

        # Check last activity
        if session.last_activity_age() > 300:  # 5 min
            return AgentHealth.STUCK

        return AgentHealth.HEALTHY

    def kill(self, agent_id: str):
        """Terminate agent session."""
        session = self.sessions.get(agent_id)
        if session:
            session.process.terminate()
            hook_manager.detach(agent_id)
            del self.sessions[agent_id]

    def restart(self, agent_id: str):
        """Restart agent with current hook."""
        workflow_id = hook_manager.get_hook(agent_id)
        self.kill(agent_id)
        # Spawn new session (hook persists)
        identity = AgentIdentity.from_address(agent_id)
        self.spawn(identity.role, identity, resume_from={'workflow_id': workflow_id})
```

**Benefits**:
- Manage 20-30 concurrent agents
- Automatic health monitoring
- Crash recovery
- Clean lifecycle management

**Dependencies**: Hook Persistence (4.1), Agent Identity (1.1), Agent Taxonomy (1.2)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 4.3 Inter-Agent Communication (Mailbox)

**Status**: Partial (has notes, not mailbox)
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Async message passing between agents

**Gastown Pattern**:
```go
type Mailbox struct {
    identity string  // e.g., "gastown/polecats/toast"
}

// Send message
gt mail send <recipient> -s "subject" -m "message"

// Check inbox
gt mail inbox

// Messages support:
- Priority (LOW, NORMAL, URGENT)
- CC recipients
- Thread tracking
- Read/unread status
```

**Jean Claude Implementation**:
```python
# Extend existing Message model
class MailboxMessage(BaseModel):
    id: str
    from_agent: str  # Agent address
    to_agent: str
    cc: List[str] = []
    subject: str
    body: str
    priority: MessagePriority
    thread_id: Optional[str] = None
    read: bool = False
    timestamp: datetime

class Mailbox:
    def __init__(self, agent_id: str, storage_dir: Path):
        self.agent_id = agent_id
        self.inbox_dir = storage_dir / "mailboxes" / agent_id / "inbox"
        self.outbox_dir = storage_dir / "mailboxes" / agent_id / "outbox"

    def send(self, message: MailboxMessage):
        """Send message to recipient."""
        # Write to recipient's inbox
        recipient_inbox = self.storage_dir / "mailboxes" / message.to_agent / "inbox"
        message_file = recipient_inbox / f"{message.id}.json"
        message_file.write_text(message.json())

        # Also write to sender's outbox
        outbox_file = self.outbox_dir / f"{message.id}.json"
        outbox_file.write_text(message.json())

    def read_inbox(self, unread_only: bool = True) -> List[MailboxMessage]:
        """Read messages from inbox."""
        messages = []
        for file in self.inbox_dir.glob("*.json"):
            msg = MailboxMessage.parse_file(file)
            if not unread_only or not msg.read:
                messages.append(msg)
        return sorted(messages, key=lambda m: (m.priority.value, m.timestamp))

    def mark_read(self, message_id: str):
        """Mark message as read."""
        # Update message file
```

**Benefits**:
- Async agent coordination
- Priority-based handling
- Thread tracking
- Audit trail

**Dependencies**: Agent Identity (1.1)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL (for coordinating 20-30 agents)

---

### 4.4 Nudge Protocol

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Interrupt/nudge stuck or idle agents

**Gastown Pattern**:
```bash
# Witness checks polecat activity
if idle > 15 minutes:
    gt nudge gastown/polecats/toast "Are you making progress?"

# Escalate after 3 failed nudges
gt mail send mayor -s "Polecat stuck on gt-123"
```

**Implementation**:
```python
class AgentMonitor:
    def check_health(self):
        for agent_id, session in agent_manager.sessions.items():
            if session.idle_time() > 900:  # 15 min
                self.nudge(agent_id, "Please provide status update")
                session.nudge_count += 1

                if session.nudge_count >= 3:
                    # Escalate to coordinator
                    mailbox.send(MailboxMessage(
                        from_agent=self.identity.address,
                        to_agent="coordinator",
                        subject=f"Agent {agent_id} not responding",
                        priority=MessagePriority.URGENT
                    ))

    def nudge(self, agent_id: str, message: str):
        """Send interrupt message to agent."""
        # Could inject into agent's prompt context
        # Or send high-priority mailbox message
```

**Benefits**:
- Detect stuck agents
- Automatic escalation
- Coordinator awareness

**Dependencies**: Agent Session Management (4.2), Mailbox (4.3)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH (for monitoring health)

---

### 4.5 Context Priming via Hooks

**Status**: Partial (has SessionStart hook, not dynamic priming)
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Inject context based on agent state

**Gastown Pattern**:
```bash
# SessionStart hook runs:
gt prime

# Injects:
- Current hook (molecule)
- Mailbox (unread messages)
- Agent role
- Working directory
```

**Implementation**:
```python
# Hook: SessionStart
def on_session_start(agent_id: str) -> str:
    """Generate context injection prompt."""
    identity = AgentIdentity.from_address(agent_id)

    # Get hook
    workflow_id = hook_manager.get_hook(agent_id)

    # Get mailbox
    mailbox = Mailbox(agent_id)
    unread = mailbox.read_inbox(unread_only=True)

    # Build context
    context = f"""You are {agent_id} ({identity.role.value} agent).

CURRENT ASSIGNMENT:
{format_workflow_context(workflow_id) if workflow_id else "No active work"}

MAILBOX ({len(unread)} unread):
{format_messages(unread[:3])}  # Show top 3

YOUR ROLE:
{get_role_description(identity.role)}
"""

    return context
```

**Benefits**:
- Agents always have current context
- Survives restarts
- Role-specific instructions

**Dependencies**: Hook Persistence (4.1), Mailbox (4.3)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 4.6 Agent Configuration Presets

**Status**: Hardcoded model names
**Complexity**: 🟢 LOW
**Priority**: P2

**Description**: Built-in + custom agent configurations

**Gastown Pattern**:
```go
builtinPresets = map[string]*AgentConfig{
    "claude": {Model: "claude-sonnet-4-5", MaxTokens: 200000},
    "gemini": {Model: "gemini-2.0-flash", MaxTokens: 100000},
}

// Custom overrides in config
custom_agents:
  fast-coder:
    preset: claude
    model: claude-haiku-4
    max_tokens: 50000
```

**Implementation**:
```python
# src/jean_claude/core/agent_config.py
@dataclass
class AgentConfig:
    model: str
    max_tokens: int
    temperature: float = 0.7
    tools: List[str] = field(default_factory=list)

AGENT_PRESETS = {
    "opus": AgentConfig(
        model="claude-opus-4-5-20251101",
        max_tokens=200000
    ),
    "sonnet": AgentConfig(
        model="claude-sonnet-4-5-20250929",
        max_tokens=200000
    ),
    "haiku": AgentConfig(
        model="claude-haiku-4-0-20241226",
        max_tokens=100000
    ),
}

# Load with overrides
def load_agent_config(preset: str, **overrides) -> AgentConfig:
    config = AGENT_PRESETS[preset]
    return replace(config, **overrides)
```

**Benefits**:
- Easy model switching
- Custom configurations
- Cost optimization

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

### 4.7 Multi-Agent Monitoring

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P1 (for workspace manager)

**Description**: Monitor health of all concurrent agents

**Gastown Pattern**:
- Witness monitors polecats
- Deacon monitors all agents
- Health checks via tmux, beads state, file timestamps

**Implementation**:
```python
class WorkspaceMonitor:
    def __init__(self, workspace_root: Path):
        self.agent_manager = AgentManager(workspace_root)
        self.mailbox = Mailbox("monitor")

    def run(self):
        """Main monitoring loop."""
        while True:
            for agent_id in self.agent_manager.list_agents():
                health = self.agent_manager.monitor(agent_id)

                if health == AgentHealth.STUCK:
                    self.handle_stuck_agent(agent_id)
                elif health == AgentHealth.CRASHED:
                    self.handle_crashed_agent(agent_id)

            time.sleep(30)  # Check every 30 seconds

    def handle_stuck_agent(self, agent_id: str):
        # Nudge → escalate → restart
        pass

    def handle_crashed_agent(self, agent_id: str):
        # Restart with hook persistence
        self.agent_manager.restart(agent_id)
```

**Benefits**:
- Automatic crash recovery
- Stuck agent detection
- Health visibility

**Dependencies**: Agent Session Management (4.2)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 4.8 Work Queue with Claiming

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Shared work queue where workers claim items

**Implementation**:
```python
class WorkQueue:
    def __init__(self, queue_id: str, storage_dir: Path):
        self.queue_id = queue_id
        self.queue_dir = storage_dir / "queues" / queue_id

    def add_work(self, item: WorkItem):
        """Add item to queue."""
        item_file = self.queue_dir / f"{item.id}.json"
        item_file.write_text(item.json())

    def claim_work(self, agent_id: str) -> Optional[WorkItem]:
        """Claim next available item."""
        for item_file in sorted(self.queue_dir.glob("*.json")):
            item = WorkItem.parse_file(item_file)
            if not item.claimed_by:
                item.claimed_by = agent_id
                item.claimed_at = datetime.now()
                item_file.write_text(item.json())
                return item
        return None

    def release_claim(self, item_id: str):
        """Release claimed item back to queue."""
        # Reset claimed_by field
```

**Benefits**:
- Load balancing
- Automatic work distribution
- Fault tolerance (unclaim on crash)

**Dependencies**: Agent Identity (1.1)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 4.9 Handoff Command (implemented earlier as 1.10)

See section 1.10 - already covered in architecture patterns.

---

### 4.10 Agent Roles & Responsibilities

**Status**: Partial (has initializer/coder)
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Define clear responsibilities per agent role

**Proposed Roles for Workspace Manager**:

| Role | Responsibilities | Persistence |
|------|------------------|-------------|
| **Coordinator** | Cross-workspace task allocation, conflict resolution | Persistent |
| **Supervisor** | Per-project monitoring, agent health checks | Persistent |
| **Worker** | Feature implementation, task execution | Ephemeral |
| **Specialist** | Domain-specific (testing, deployment, code review) | On-demand |
| **Refinery** | Merge queue, PR management | Persistent |

**Implementation**: See Agent Taxonomy (1.2)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ ESSENTIAL

---

### 4.11 Attribution in Git Commits

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P1

**Description**: Set GIT_AUTHOR_NAME to agent identity

**Implementation**:
```python
# In core/agent.py
async def execute_prompt_async(...):
    # Set git attribution
    env = os.environ.copy()
    env['GIT_AUTHOR_NAME'] = agent_identity.address
    env['GIT_AUTHOR_EMAIL'] = config.owner_email

    # Execute with env
    result = await sdk.execute(..., env=env)
```

**Benefits**:
- Audit trail
- Attribution tracking
- Debugging

**Dependencies**: Agent Identity (1.1)

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 4.12 Action Items in Notes

**Status**: Partial (has notes, not action items)
**Complexity**: 🟢 LOW
**Priority**: P2

**Description**: Extend notes to support actionable items

**Implementation**:
```python
# Extend NoteCategory
class NoteCategory(Enum):
    ...
    ACTION_ITEM = "action_item"  # NEW

class Note(BaseModel):
    ...
    blocking: bool = False  # NEW - workflow waits for resolution
    assigned_to: Optional[str] = None  # NEW - agent assignment
    resolved: bool = False  # NEW - completion tracking

# Usage
notes.add_action_item(
    agent_id="initializer",
    title="Need database choice",
    content="SQLite vs Postgres?",
    blocking=True,  # Workflow pauses
    assigned_to="coordinator"
)
```

**Benefits**:
- Actionable vs informational separation
- Workflow blocking
- Assignment tracking

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

## 5. Testing & Quality Patterns

### 5.1 GitHub Actions CI ⚠️

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P0 (CRITICAL)

**Description**: Automated testing on push/PR

**Implementation**:
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest -m fast

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run ruff check .

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run mypy src/
```

**Benefits**:
- Catch bugs before merge
- Automated quality gates
- CI/CD foundation

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ CRITICAL

---

### 5.2 Test Categorization

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P0

**Description**: Fast/slow/integration/e2e test separation

**Implementation**:
```python
# In test files
@pytest.mark.fast
def test_unit():
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_database():
    pass

@pytest.mark.e2e
def test_dashboard():
    pass

# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "fast: Fast unit tests (default)",
    "slow: Slow tests (integration)",
    "integration: Integration tests",
    "e2e: End-to-end tests"
]
# Default: only fast tests
addopts = "-n 4 -m 'not slow and not e2e'"
```

**Benefits**:
- Faster local development
- Granular CI control
- Parallel test execution

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐ HIGH

---

### 5.3 Security Linting (Bandit)

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P0 (SECURITY)

**Description**: Automated security vulnerability scanning

**Implementation**:
```bash
# Add to pyproject.toml
[dependency-groups]
dev = [..., "bandit>=1.7.0"]

# .bandit config
[bandit]
exclude_dirs = ["/tests"]
skips = ["B101"]  # assert_used (OK in tests)

# Run in CI
uv run bandit -r src/jean_claude
```

**Benefits**:
- Catch security issues
- Automated scanning
- Best practices enforcement

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐⭐⭐ CRITICAL

---

### 5.4 Integration Test Workflow

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Separate CI job for slow tests

**Implementation**:
```yaml
# .github/workflows/integration.yml
name: Integration Tests
on:
  pull_request:
    paths:
      - 'src/jean_claude/core/**'
      - 'src/jean_claude/orchestration/**'

jobs:
  integration:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - run: uv sync
      - run: uv run pytest -m integration
```

**Benefits**:
- Conditional execution (only when needed)
- Parallel with fast tests
- Shorter feedback loop

**Dependencies**: Test Categorization (5.2)

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

### 5.5 E2E Dashboard Tests

**Status**: Not implemented
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Browser automation for dashboard testing

**Implementation**:
```python
# tests/e2e/test_dashboard.py
import pytest
from playwright.sync_api import sync_playwright

@pytest.mark.e2e
def test_dashboard_loads():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:8000")

        assert "Jean Claude Dashboard" in page.title()

        # Check workflows visible
        assert page.locator(".workflow-card").count() > 0

        browser.close()

@pytest.mark.e2e
def test_workflow_detail_page():
    # Test navigation, SSE updates, etc.
    pass
```

**Benefits**:
- Prevent dashboard regressions
- Visual validation
- User flow testing

**Dependencies**: Test Categorization (5.2)

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM (dashboard is important for monitoring)

---

### 5.6 Type Checking in CI

**Status**: Configured but not enforced
**Complexity**: 🟡 MEDIUM
**Priority**: P1

**Description**: Enforce mypy type checking

**Implementation**:
```yaml
# In .github/workflows/ci.yml
type-check:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: astral-sh/setup-uv@v1
    - run: uv sync
    - run: uv run mypy src/

# Fix existing violations gradually
# pyproject.toml
[tool.mypy]
python_version = "3.10"
strict = true
# Allow gradual adoption
warn_return_any = false  # Temporarily
```

**Benefits**:
- Catch type errors
- Better IDE support
- Code quality

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐⭐ MEDIUM

---

### 5.7 Release Automation

**Status**: Not implemented
**Complexity**: 🟠 HIGH
**Priority**: P3

**Description**: Automated releases with changelogs

**Implementation**: Complex - involves GoReleaser-equivalent for Python

**Applicability to Workspace Manager**: ⭐⭐ LOW (future)

---

### 5.8 Build Validation

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P2

**Description**: Verify generated files are committed

**Implementation**:
```yaml
# In CI
- name: Check generated files
  run: |
    python scripts/generate_skills.py
    git diff --exit-code src/jean_claude/skills/
```

**Benefits**:
- Prevent broken installs
- Catch missing generations

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW

---

### 5.9 Contextual Linting

**Status**: Partial (Ruff configured)
**Complexity**: 🟡 MEDIUM
**Priority**: P2

**Description**: Different rules for tests vs production

**Implementation**:
```toml
# pyproject.toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = [
    "S101",  # assert allowed in tests
    "S106",  # hardcoded passwords OK in tests
]
```

**Benefits**:
- Reduced noise
- Pragmatic linting

**Dependencies**: None

**Applicability to Workspace Manager**: ⭐⭐ LOW

---

### 5.10 Visual Debugging for E2E

**Status**: Not implemented
**Complexity**: 🟢 LOW
**Priority**: P3

**Description**: Watch browser tests run

**Implementation**:
```python
# In E2E tests
import os

headed = os.getenv("HEADLESS", "1") == "0"
browser = p.chromium.launch(headless=not headed)
```

**Benefits**:
- Easier debugging
- See what went wrong

**Dependencies**: E2E Tests (5.5)

**Applicability to Workspace Manager**: ⭐ LOW

---

## Implementation Phases

### Phase 0: Critical Security & Foundations (Week 1)

**Must implement before any multi-agent work**

1. ✅ **Beads Input Validation** (2.1) - Security
2. ✅ **`--no-daemon` Flag** (2.2) - Reliability
3. ✅ **GitHub Actions CI** (5.1) - Quality gate
4. ✅ **Security Linting** (5.3) - Security
5. ✅ **Test Categorization** (5.2) - Speed
6. ✅ **Agent Identity System** (1.1) - Foundation

**Complexity**: 🟢 LOW to 🟡 MEDIUM
**Total Effort**: ~3-4 days with your help

---

### Phase 1: Multi-Agent Infrastructure (Weeks 2-4)

**Core infrastructure for persistent agents**

7. ✅ **Agent Taxonomy** (1.2) - Role definitions
8. ✅ **Hook Persistence** (4.1) - Crash recovery
9. ✅ **Agent Session Management** (4.2) - Spawn/monitor/kill
10. ✅ **State Layer Separation** (1.4) - Clear boundaries
11. ✅ **`BEADS_DIR` Support** (2.3) - Multi-project ready
12. ✅ **Beads Directory Resolution** (2.4) - Redirect support

**Complexity**: 🟡 MEDIUM to 🟠 HIGH
**Total Effort**: ~2-3 weeks

---

### Phase 2: Agent Coordination (Weeks 5-8)

**Enable agents to communicate and coordinate**

13. ✅ **Mailbox Communication** (4.3) - Inter-agent messages
14. ✅ **Protocol Messages** (1.6) - Typed payloads
15. ✅ **Multi-Agent Monitoring** (4.7) - Health checks
16. ✅ **Nudge Protocol** (4.4) - Stuck agent handling
17. ✅ **Context Priming** (4.5) - Dynamic context injection
18. ✅ **Manager Pattern** (1.3) - Centralized operations

**Complexity**: 🟡 MEDIUM to 🟠 HIGH
**Total Effort**: ~3-4 weeks

---

### Phase 3: Workspace Manager (Weeks 9-12)

**Transform into multi-project workspace manager**

19. ✅ **Two-Level Hierarchy** (1.5) - Workspace/project split
20. ✅ **Work Queue** (4.8) - Load balancing
21. ✅ **Handoff System** (1.10) - Session cycling
22. ✅ **Molecule Pattern** (1.7) - Workflow as data
23. ✅ **Formula Support** (2.5) - TOML templates
24. ✅ **Agent Roles & Responsibilities** (4.10) - Complete taxonomy

**Complexity**: 🟠 HIGH
**Total Effort**: ~4-6 weeks

---

### Phase 4: Polish & Advanced Features (Ongoing)

**UX improvements and advanced capabilities**

25. ✅ **Command Grouping** (3.1)
26. ✅ **Style Module** (3.2)
27. ✅ **Status Symbols** (3.3)
28. ✅ **Numeric Shortcuts** (3.4)
29. ✅ **Fuzzy Matching** (3.5)
30. ✅ **JSON Output** (3.6)
31. ✅ **Interactive TUI** (3.7)
32. ✅ **Agent Config Presets** (4.6)
33. ✅ **Integration Tests** (5.4)
34. ✅ **E2E Dashboard Tests** (5.5)

**Complexity**: 🟢 LOW to 🟡 MEDIUM
**Total Effort**: Ongoing as needed

---

## Dependencies Graph

```
Phase 0 (Foundations):
  1.1 Agent Identity ──┐
                       ├── 1.2 Agent Taxonomy
  1.4 State Layers ────┘       │
                               ├── 4.1 Hook Persistence
                               │       │
                               │       ├── 4.2 Agent Sessions
                               │       │       │
                               │       │       ├── 4.3 Mailbox
                               │       │       │       │
                               │       │       │       ├── 4.4 Nudge
                               │       │       │       └── 4.7 Monitoring
                               │       │       │
                               │       │       └── 1.10 Handoff
                               │       │
                               │       └── 4.5 Context Priming
                               │
                               └── 1.6 Protocol Messages

Phase 3 (Workspace):
  1.5 Two-Level Hierarchy ──┐
  1.7 Molecule Pattern ─────┤
  2.5 Formula Support ──────┼── Complete Workspace Manager
  4.8 Work Queue ───────────┤
  4.10 Agent Roles ─────────┘
```

---

## Success Metrics

**Phase 0 Complete When**:
- ✅ All beads commands use input validation
- ✅ CI catches broken commits
- ✅ Tests run in <2 min locally
- ✅ Agent identity tracked in all operations

**Phase 1 Complete When**:
- ✅ Can spawn/kill/monitor persistent agents
- ✅ Agents survive crashes via hook persistence
- ✅ Multi-project beads support works
- ✅ Clear state boundaries (config/operational/runtime/event)

**Phase 2 Complete When**:
- ✅ Agents communicate via mailbox
- ✅ Stuck agents auto-detected and nudged
- ✅ Health monitoring dashboard shows all agents
- ✅ Context priming works on agent restart

**Phase 3 Complete When**:
- ✅ Managing 20-30 concurrent agents
- ✅ Cross-project workflows function
- ✅ Work queue distributes tasks
- ✅ Workflow templates reusable
- ✅ Complete role-based agent taxonomy

---

## Risk Assessment

**High Risk Patterns** (require careful planning):
- 🔴 **Two-Level Hierarchy** (1.5) - Major architectural change
- 🔴 **Agent Session Management** (4.2) - Complex process management
- 🔴 **Multi-Agent Monitoring** (4.7) - Coordination complexity
- 🔴 **Molecule Pattern** (1.7) - Workflow execution changes

**Medium Risk**:
- 🟠 **Manager Pattern** (1.3) - Large refactoring
- 🟠 **Mailbox** (4.3) - Concurrency concerns
- 🟠 **Formula Support** (2.5) - Template complexity

**Low Risk** (straightforward):
- 🟢 Most CLI/UX patterns
- 🟢 Input validation
- 🟢 Style/polish improvements
- 🟢 Test categorization

---

## Notes & Decisions

**2026-01-05**: Initial roadmap created from Gastown analysis

**Key Decision**: Jean Claude is evolving toward Gastown's persistent workspace manager model, not remaining a simple workflow automation tool. This makes many "not applicable" patterns highly relevant.

**Architecture Philosophy**: Follow Gastown's proven patterns for multi-agent coordination while maintaining Python's strengths (Pydantic, async/await, Rich TUIs).

**Testing Strategy**: Adopt Gastown's test categorization early to maintain fast feedback loops as complexity grows.

**Beads Integration**: Deepen integration with security hardening, multi-project support, and formula templates.

---

## References

- **Gastown Analysis**: Five parallel investigator agents analyzed Gastown codebase
  - Architecture & Design (10 patterns)
  - Beads Integration (8 patterns)
  - CLI & UX (10 patterns)
  - Agent Patterns (12 patterns)
  - Testing & Quality (10 patterns)

- **Steve Yegge's Gastown**: https://github.com/steveyegge/gastown

- **Related Jean Claude Docs**:
  - `docs/ARCHITECTURE.md` - Current event-sourced architecture
  - `docs/two-agent-workflow.md` - Existing two-agent pattern
  - `knowledge/doc/implementation/agent-note-taking-completion.md` - Notes system

---

## Next Steps

1. **Review with La Boeuf** - Validate phase priorities
2. **Create Beads tasks for Phase 0** - Security & foundations
3. **Prototype agent identity system** - Test the pattern
4. **Design agent session management** - Core infrastructure
5. **Plan multi-agent dashboard** - Monitoring 20-30 agents

---

**Document Status**: Living roadmap - update as patterns are implemented

**Last Updated**: 2026-01-05
