# Changelog

All notable changes to Jean Claude will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
