# Documentation and Planning

This directory contains documentation, planning artifacts, and implementation notes.

## Structure

### plans/
Implementation plans and specifications created before starting work.

**When to create a plan:**
- Major features
- Architectural changes
- Multi-file refactoring

**Plan contents:**
- Feature overview
- Implementation steps
- Files to modify
- Testing approach
- Success criteria

### research/
Investigation results and technology exploration.

**Contents:**
- Library comparisons
- API exploration
- Design alternatives
- Proof of concepts

### implementation/
Notes created during or after implementation.

**Contents:**
- Implementation challenges
- Solutions discovered
- Integration points
- Performance considerations
- Future improvements

## Workflow Integration

### Before Implementation
1. Create plan in `plans/`
2. Research unknowns in `research/`
3. Reference during implementation

### During Implementation
1. Document discoveries in `implementation/`
2. Update plan if scope changes
3. Record decisions in `../decisions/`

### After Implementation
1. Document final approach in `implementation/`
2. Extract patterns to `../patterns/`
3. Update context in `../context/CONTEXT.md`

## File Naming

Use descriptive names with dates:

- `plans/2026-01-15-knowledge-system.md`
- `research/2026-01-10-sdk-mcp-integration.md`
- `implementation/2026-01-20-event-models-refactor.md`
