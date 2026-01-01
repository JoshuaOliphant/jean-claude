# Changelog

All notable changes to Jean Claude will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.1] - 2025-12-31

### Changed

- **`jc migrate` Enhancement**: Now installs missing skill and updates CLAUDE.md
  - Checks for `.claude/skills/jean-claude-cli/` and installs if missing
  - Checks for CLAUDE.md Jean Claude section and adds if missing
  - Updated success message to reflect v0.7.0 features
  - Dry-run mode shows all pending changes including skill/CLAUDE.md

### Documentation

- **README Updates**: Comprehensive documentation of new features
  - Added "One-Command Setup" and "Jean Claude CLI Skill" to Features
  - Expanded Quick Start with detailed `jc init` output
  - New Project Management section explaining `jc init` vs `jc migrate`
  - Clarified `jc migrate` safety (doesn't overwrite existing files)

### Benefits

- Existing projects can now get the skill and CLAUDE.md with `jc migrate`
- README provides clear onboarding path for new users
- Migration process is fully documented and transparent

## [0.7.0] - 2025-12-31

### Added

- **Jean Claude CLI Skill**: Comprehensive Claude Code skill installed by `jc init`
  - 358-line guide covering all jc commands, Beads integration, two-agent pattern
  - Automatically triggers when users ask "How do I use jc workflow?" or similar
  - Reduces CLAUDE.md bloat by moving generic docs to semantically-triggered skill

- **CLAUDE.md Auto-Generation**: `jc init` now creates/updates CLAUDE.md
  - Brief project-specific section (30 lines) added to CLAUDE.md
  - References skill for detailed documentation
  - Workflow artifacts locations and configuration pointers
  - No need to run separate `jc onboard` command

- **Multi-Project Support**: Project names in escalation notifications
  - Auto-detected from `Path.cwd().name` or explicitly set
  - Notification titles: `[project-name] Question from Coordinator`
  - Makes it clear which project is asking when running multiple Jean Claude instances

### Changed

- `jc init` is now a complete onboarding solution (skill + CLAUDE.md + slash commands)
- Skill provides comprehensive docs without bloating every conversation
- Project-specific knowledge stays in CLAUDE.md, generic knowledge in skill

### Benefits

- **One Command Setup**: `jc init` does everything - no manual CLAUDE.md editing
- **Context Efficiency**: Skill only loads when relevant, not every conversation
- **Better Documentation**: 358 lines of comprehensive guides vs 30 lines in CLAUDE.md
- **Multi-Project Clarity**: Immediately see which project sent an escalation

## [0.6.1] - 2025-12-30

### Added

- **Mobile Response Flow**: Fully mobile coordinator pattern with bidirectional ntfy.sh communication
  - `JEAN_CLAUDE_NTFY_RESPONSE_TOPIC` environment variable for response channel
  - `poll_ntfy_responses()` function to fetch responses from ntfy.sh
  - `process_ntfy_responses()` function to write responses to workflow OUTBOX
  - Auto-continue loop polls response topic every iteration (2-second interval)
  - Response format: `{workflow-id}: {response text}`

- **Documentation**:
  - Updated NTFY_SETUP.md with bidirectional setup instructions
  - Added "Option 1: Respond from Your Phone" section
  - test_mobile_response.py script for end-to-end testing

### Changed

- NTFY setup now requires two topics (escalation + response)
- Coordinator can receive responses from phone without SSH access
- Auto-continue loop displays green message when responses received

### Benefits

- **Fully Mobile**: Respond to agent questions from anywhere
- **Zero SSH**: No need for terminal access when on the go
- **Async**: Responses are polled and processed automatically
- **Simple Format**: Plain text messages parsed automatically

## [0.6.0] - 2025-12-30

### Added

- **Coordinator Pattern**: Intelligent agent-to-human communication system
  - Agents can call `ask_user` and `notify_user` tools when they need help
  - Main Claude Code instance (coordinator) triages agent questions
  - 90% of questions answered automatically by coordinator
  - Only critical decisions escalated to human via ntfy push notifications
  - INBOX/OUTBOX directory-based messaging system
  - 30-minute timeout for agent questions with graceful handling

- **ntfy.sh Integration**: Push notifications for critical escalations
  - Cross-platform notifications (iOS, Android, Web)
  - Configurable via `JEAN_CLAUDE_NTFY_TOPIC` environment variable
  - Desktop notifications (macOS) for coordinator alerts
  - `escalate_to_human()` function for coordinator use

- **Mailbox Tools**: MCP-based agent communication toolkit
  - `ask_user` tool - Request help or clarification from coordinator
  - `notify_user` tool - Send progress updates (non-blocking)
  - Workflow pause/resume infrastructure for response waiting
  - Message priority levels (LOW, NORMAL, URGENT)

- **Documentation**:
  - `docs/coordinator-pattern.md` - Complete architecture guide
  - `NTFY_SETUP.md` - Push notification setup instructions
  - `.claude/commands/mailbox.md` - Coordinator slash command guide
  - Updated README with coordinator pattern section

### Changed

- Agent prompts now include "GETTING HELP" section with mailbox tool usage examples
- Orchestration loop monitors INBOX for agent messages at each iteration
- Workflow pauses when unanswered help requests detected
- Features list now highlights coordinator pattern and push notifications

### Technical Details

- Built on Agent SDK's MCP (Model Context Protocol) tools
- Filesystem-based message queue (individual JSON files per message)
- Async/await architecture for non-blocking operation
- Coordinator pattern enables human-in-the-loop without human-in-every-loop

## [0.5.0] - 2025-12-29

### Added

- Event sourcing infrastructure for workflow tracking
- SQLite event store for persistent telemetry
- Real-time dashboard for monitoring workflows

## [0.4.0] - 2025-12-28

### Added

- Two-agent workflow pattern (Opus plans, Sonnet implements)
- Auto-continue orchestration for long-running workflows
- Feature-based workflow state management
- Verification-first pattern for test integrity

## [0.3.0] - 2025-12-27

### Added

- Beads integration for task-based workflows
- Git worktree isolation for parallel development
- Workflow composition and chaining

## [0.2.0] - 2025-12-26

### Added

- Real-time streaming output with `--stream` mode
- Claude Agent SDK integration
- AWS Bedrock authentication support

## [0.1.0] - 2025-12-25

### Added

- Initial release
- Basic CLI with `jc` command
- Simple prompt execution
- Project initialization

[0.6.0]: https://github.com/joshuaoliphant/jean-claude/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/joshuaoliphant/jean-claude/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/joshuaoliphant/jean-claude/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/joshuaoliphant/jean-claude/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/joshuaoliphant/jean-claude/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/joshuaoliphant/jean-claude/releases/tag/v0.1.0
