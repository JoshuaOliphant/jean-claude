# Jean Claude - AI Developer Workflows

Programmatic Claude Code orchestration with Beads issue tracking.

## Quick Reference

| Task | Command |
|------|---------|
| Run tests | `uv run pytest tests/` |
| Find work | `bd ready` |
| Create task | `bd create "Title" --type task --priority 2` |
| Close task | `bd close <id>` |
| Two-agent workflow | `jc workflow "description"` |
| Sync issues | `bd sync` |

For beads context: `bd prime`

## Architecture

**Two-layer design**: Agentic Layer (`adws/`, `.claude/commands/`) operates on Application Layer (`src/jean_claude/`).

```
src/jean_claude/
├── core/           # agent.py, sdk_executor.py, state.py, security.py
├── orchestration/  # two_agent.py, auto_continue.py
├── cli/            # Click commands (main.py, commands/)
└── integrations/   # Git, VCS plugins
```

## Development Patterns

1. **TDD**: Write tests before implementation
2. **ABOUTME**: All files start with 2-line `# ABOUTME:` comment
3. **Fixtures**: Use `tests/conftest.py` fixtures, never nested `with patch()` blocks
4. **AsyncMock**: Use for async functions (not `Mock`)
5. **Click CLI**: All commands use Click framework
6. **Pydantic Models**: All data types use Pydantic v2

## Key Files

| Purpose | Location |
|---------|----------|
| CLI entry point | `src/jean_claude/cli/main.py:14` |
| SDK executor | `src/jean_claude/core/sdk_executor.py` |
| Two-agent workflow | `src/jean_claude/orchestration/two_agent.py` |
| Security hooks | `src/jean_claude/core/security.py` |
| Test fixtures | `tests/conftest.py` |
| Slash commands | `.claude/commands/*.md` |

## Docs (Progressive Disclosure)

- [Testing Patterns](docs/testing.md) - Fixtures, TDD, async mocks
- [Beads Workflow](docs/beads-workflow.md) - Issue tracking integration
- [Two-Agent Workflow](docs/two-agent-workflow.md) - Opus plans, Sonnet codes
- [Security Hooks](docs/security-hooks-implementation.md) - Bash command validation
- [Auto-Continue](docs/auto-continue-workflow.md) - Autonomous continuation
- [Streaming](docs/streaming-implementation-summary.md) - Real-time output

## ADW Scripts

Executable workflow scripts in `adws/`:
- `adw_prompt.py` - Ad-hoc prompts
- `adw_slash_command.py` - Execute slash commands
- `adw_chore_implement.py` - Plan + implement
- `adw_plan_tdd.py` - TDD task breakdown
- `adw_beads_ready.py` - Interactive task picker

## Output Locations

- Agent outputs: `agents/{adw_id}/{agent_name}/`
- Specs/plans: `specs/` and `specs/plans/`
- Worktrees: `trees/` (gitignored)
