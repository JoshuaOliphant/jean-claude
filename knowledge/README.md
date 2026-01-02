# Jean Claude Knowledge Management

This directory contains the two-tier knowledge management system for persistent context and pattern learning.

## Structure

```
knowledge/
├── doc/                      # Documentation and planning
│   ├── plans/               # Implementation plans
│   ├── research/            # Research and exploration notes
│   └── implementation/      # Implementation notes and decisions
├── sessions/                # Session management
│   ├── active/              # Current session contexts
│   └── archive/             # Historical sessions
├── patterns/                # Reusable code patterns and solutions
├── decisions/               # Technical decisions and rationale
├── testing/                 # Test strategies and approaches
└── context/                 # Active context tracking
    ├── TODO.md              # Current tasks and priorities
    └── CONTEXT.md           # Project context and state
```

## Usage

### For Agents

When agents discover patterns, solutions, or make decisions during workflow execution:

1. **Capture raw insights** in appropriate directories:
   - `patterns/` - Reusable code patterns
   - `decisions/` - Architectural/technical decisions
   - `testing/` - Testing strategies that worked

2. **Document learnings** in `doc/implementation/` after completing work

3. **Update context** in `context/TODO.md` and `context/CONTEXT.md` as work progresses

### For Session Management

Sessions track work across Claude Code restarts:

- **Active sessions** in `sessions/active/{session_id}/` contain ongoing work context
- **Archived sessions** in `sessions/archive/` preserve historical context
- Session start hook automatically loads active session context
- Session end hook archives completed sessions

### Knowledge Categories

**doc/plans/** - Implementation plans and specifications
- Created before starting major features
- Referenced during implementation
- Updated as plans evolve

**doc/research/** - Research findings and exploration
- Investigation results
- Technology comparisons
- Design exploration

**doc/implementation/** - Implementation notes
- How features were built
- Challenges encountered and solved
- Integration points and dependencies

**patterns/** - Reusable solutions
- Code patterns that work well in this codebase
- Solution templates
- Best practices discovered

**decisions/** - Technical decisions
- Why specific approaches were chosen
- Trade-offs considered
- Alternatives evaluated

**testing/** - Testing approaches
- Test strategies that work for this project
- Fixture patterns
- Mocking strategies

**context/** - Current state
- `TODO.md` - Active tasks and priorities
- `CONTEXT.md` - Current project state and focus areas

## Integration with Jean Claude Workflows

This knowledge system complements Jean Claude's execution state:

- **Jean Claude state** (`agents/`, `.jc/events.db`) tracks workflow execution
- **Knowledge system** tracks insights, patterns, and learnings

During workflows:
- Agents can reference existing patterns from `patterns/`
- Agents can check decisions made in `decisions/`
- Agents can update TODO and CONTEXT as work progresses
- After completion, agents document learnings for future reference

## Privacy

The following directories are gitignored for privacy:
- `sessions/` - May contain sensitive context
- `context/TODO.md` - Personal task tracking

The following directories are committed to share knowledge:
- `patterns/` - Team benefits from reusable patterns
- `decisions/` - Team needs to understand technical choices
- `doc/` - Documentation is valuable for everyone
