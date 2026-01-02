# Project Context

> Last updated: 2026-01-01

## Current Focus

Knowledge management system initialization for Jean Claude project.

## Recent Work

### Knowledge System Setup (2026-01-01)
- Created two-tier knowledge directory structure
- Documented session management approach
- Established context tracking files

## Project State

### Jean Claude v0.7.1
**Status**: Active development

**Recent Changes**:
- SDK integration improvements (event models)
- MCP server support exploration

**Technology Stack**:
- Python 3.10+ with uv package management
- Claude Agent SDK v0.1.18+
- Click CLI framework
- Pydantic v2 for data models
- FastAPI for dashboard
- SQLAlchemy for event storage

### Known Issues
- Check `bd list --status=open` for current Beads issues
- Check `.jc/events.db` for recent errors

### Active Workflows
- Check `agents/` directory for running workflows
- Use `jc status` for workflow state

## Architecture Notes

### Two-Agent Pattern
- Opus plans (initializer agent)
- Sonnet implements (coder agent)
- State in `agents/{workflow-id}/state.json`

### Integration Points
- Beads for issue tracking
- ntfy.sh for coordinator-to-human communication
- Git hooks for session management
- Event store for telemetry

## Development Patterns

### Testing
- Mock external dependencies (Beads CLI, SDK)
- Test real business logic
- Use fixtures from conftest.py hierarchy
- Follow TDD when adding features

### Code Style
- ABOUTME comments in every file
- Pydantic for all models
- Click for CLI commands
- AsyncMock for async functions

## Next Steps

See `TODO.md` for immediate tasks.

For workflow planning, use Beads tasks or `jc workflow` command.
