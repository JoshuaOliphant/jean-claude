# Session Management

Sessions track work context across Claude Code restarts and provide continuity for long-running development tasks.

## Session Lifecycle

1. **Session Start** - Session start hook creates new session in `active/`
2. **During Work** - Context accumulates in session directory
3. **Session End** - Session end hook archives completed session to `archive/`

## Session Structure

Each session directory contains:

```
sessions/active/{session_id}/
├── context.md           # Session-specific context
├── progress.md          # What was accomplished
├── next_steps.md        # What to do next
└── discoveries/         # Things learned during session
    ├── patterns/        # Patterns discovered
    └── issues/          # Issues encountered
```

## Session ID Format

Session IDs use the format: `YYYY-MM-DD-HHMMSS-{topic_slug}`

Example: `2026-01-01-213000-knowledge-init`

## Using Sessions

### At Session Start

The session start hook will:
1. Create new session directory
2. Load previous session context if available
3. Update `knowledge/context/CONTEXT.md` with session info

### During Session

Agents and coordinators can:
- Write discoveries to `discoveries/`
- Update `progress.md` with what's been done
- Update `next_steps.md` with remaining work

### At Session End

The session end hook will:
1. Ensure all session files are saved
2. Move session from `active/` to `archive/`
3. Update knowledge indexes

## Session Context Recovery

If Claude Code restarts mid-session:
1. Session start hook detects incomplete session in `active/`
2. Loads `context.md`, `progress.md`, and `next_steps.md`
3. Coordinator can resume work seamlessly

## Integration with Beads

For Beads workflows:
- Session context includes Beads task ID
- Session archives are linked to Beads issues
- Workflow state and session state are complementary
