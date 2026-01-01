# ABOUTME: Implementation of the 'jc init' command
# ABOUTME: Initializes Jean Claude infrastructure in the current project

"""Initialize Jean Claude in the current project."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from jean_claude.config.models import ProjectConfig

console = Console()

# Directories to create
INIT_DIRECTORIES = [
    "specs",
    "agents",
    "trees",
    ".jc",
    ".jc/temp",
    ".jc/reports",
    ".jc/verification",
    ".claude/commands",
]

# Entries to add to .gitignore
GITIGNORE_ENTRIES = [
    "",
    "# Jean Claude CLI",
    "agents/",
    "trees/",
    ".jc/",
]

# Slash command templates to create
SLASH_COMMANDS = {
    "prime.md": """\
# Prime

Gather project context using the prime subagent for context-efficient exploration.

## Execute

Run the following command to gather project context:

```bash
jc prime --raw
```

The prime subagent will:
1. Explore the codebase structure using Haiku (fast and cheap)
2. Identify tech stack, entry points, and testing setup
3. Return a condensed ~500 word summary

This keeps file exploration out of your main context window.
""",
    "cleanup.md": """\
# Cleanup Jean Claude Temporary Files

Clean up temporary verification scripts, status reports, and agent work directories.

## Instructions

1. Check for the existence of `.jc/` directory
2. Clean up temporary files based on user preferences
3. Report what was cleaned

## Implementation

```bash
# Run the cleanup command
jc cleanup --dry-run

# Show user what will be deleted and ask for confirmation
# Then run actual cleanup
jc cleanup

# For more aggressive cleanup (including agent directories)
jc cleanup --agents --all
```

## Cleanup Targets

The following directories contain temporary files:
- `.jc/temp/` - Temporary check/demo scripts (check_*.py, demo_*.py, verify_*.py)
- `.jc/reports/` - Status and verification reports (*_COMPLETE.md, *_VERIFICATION.md)
- `.jc/verification/` - Test outputs and logs
- `agents/` - Old agent work directories (optional with --agents flag)

## Options

- `--age N` - Remove files older than N days (default: 7)
- `--all` - Remove all temporary files regardless of age
- `--agents` - Also clean up old agent work directories
- `--dry-run` - Show what would be deleted without actually deleting

## Report

Display:
- Number of files that will be/were deleted
- Total size of files
- Breakdown by directory
""",
}


def detect_project_name(project_root: Path) -> str:
    """Detect project name from directory or pyproject.toml."""
    # Try pyproject.toml first
    pyproject = project_root / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib

            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
                name = data.get("project", {}).get("name")
                if name:
                    return name
        except Exception:
            pass

    # Fall back to directory name
    return project_root.name


def detect_source_directory(project_root: Path) -> str:
    """Detect the source code directory."""
    candidates = ["src", "app", "lib", project_root.name.replace("-", "_")]
    for candidate in candidates:
        if (project_root / candidate).is_dir():
            return f"{candidate}/"
    return "src/"


def detect_test_directory(project_root: Path) -> str:
    """Detect the test directory."""
    candidates = ["tests", "test", "spec"]
    for candidate in candidates:
        if (project_root / candidate).is_dir():
            return f"{candidate}/"
    return "tests/"


def detect_test_command(project_root: Path) -> str:
    """Detect the test command based on project structure."""
    if (project_root / "pyproject.toml").exists():
        return "uv run pytest"
    if (project_root / "package.json").exists():
        return "npm test"
    if (project_root / "Cargo.toml").exists():
        return "cargo test"
    if (project_root / "go.mod").exists():
        return "go test ./..."
    return "uv run pytest"


def update_gitignore(project_root: Path) -> bool:
    """Update .gitignore with Jean Claude entries.

    Returns:
        True if .gitignore was modified, False if entries already exist
    """
    gitignore_path = project_root / ".gitignore"

    # Read existing content
    existing_content = ""
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text()

    # Check if already initialized
    if "# Jean Claude CLI" in existing_content:
        return False

    # Append new entries
    new_content = existing_content.rstrip() + "\n" + "\n".join(GITIGNORE_ENTRIES) + "\n"
    gitignore_path.write_text(new_content)
    return True


def update_claude_md(project_root: Path) -> bool:
    """Update or create CLAUDE.md with Jean Claude section.

    Checks both root CLAUDE.md and .claude/CLAUDE.md locations.

    Returns:
        True if CLAUDE.md was created or updated, False if section already exists
    """
    # Check both possible locations
    claude_md_locations = [
        project_root / "CLAUDE.md",
        project_root / ".claude" / "CLAUDE.md",
    ]

    # Find existing CLAUDE.md or use default location
    claude_md_path = None
    for location in claude_md_locations:
        if location.exists():
            claude_md_path = location
            break

    if claude_md_path is None:
        # Create at root if neither exists
        claude_md_path = claude_md_locations[0]

    # Read existing content
    existing_content = ""
    if claude_md_path.exists():
        existing_content = claude_md_path.read_text()

    # Check if already initialized
    if "## Jean Claude AI Workflows" in existing_content:
        return False

    # Prepare section content
    section = f"""
## Jean Claude AI Workflows

This project uses [Jean Claude](https://github.com/JoshuaOliphant/jean-claude) for AI-powered development workflows.

### Quick Start

```bash
bd ready                      # Find available Beads tasks
jc work <task-id>            # Execute a Beads task
jc workflow "description"    # Ad-hoc workflow without Beads
jc status                    # Check workflow status
```

### Workflow Artifacts

Jean Claude stores workflow data in:
- `specs/` - Workflow specifications and feature plans
- `agents/{{workflow-id}}/state.json` - Workflow state and progress
- `.jc/events.db` - Event history for monitoring

### Getting Help

For comprehensive Jean Claude documentation, ask me (Claude):
- "How do I use jc workflow?"
- "What's the two-agent pattern?"
- "How does Beads integration work?"

The `jean-claude-cli` skill (installed by `jc init`) provides detailed command guides.

### Configuration

Project settings: `.jc-project.yaml`
"""

    # Append or create
    if existing_content:
        new_content = existing_content.rstrip() + "\n" + section + "\n"
    else:
        new_content = section.lstrip() + "\n"

    claude_md_path.write_text(new_content)
    return True


def install_skill(project_root: Path) -> bool:
    """Install jean-claude-cli skill to .claude/skills/.

    Returns:
        True if skill was installed, False if already exists
    """
    skills_dir = project_root / ".claude" / "skills" / "jean-claude-cli"
    skill_md_path = skills_dir / "SKILL.md"

    if skill_md_path.exists():
        return False

    # Create skills directory
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Get skill content from package
    import importlib.resources
    try:
        # Python 3.9+
        skill_content = (
            importlib.resources.files("jean_claude")
            .joinpath("skills/jean-claude-cli/SKILL.md")
            .read_text()
        )
    except AttributeError:
        # Fallback for older Python
        import pkg_resources
        skill_content = pkg_resources.resource_string(
            "jean_claude", "skills/jean-claude-cli/SKILL.md"
        ).decode("utf-8")

    # Write skill file
    skill_md_path.write_text(skill_content)
    return True


def create_slash_commands(project_root: Path) -> list[str]:
    """Create slash command templates in .claude/commands/.

    Returns:
        List of created command file names
    """
    commands_dir = project_root / ".claude" / "commands"
    created = []

    for filename, content in SLASH_COMMANDS.items():
        command_path = commands_dir / filename
        if not command_path.exists():
            command_path.write_text(content)
            created.append(filename)

    return created


@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration",
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Create minimal configuration without auto-detection",
)
def init(force: bool, minimal: bool) -> None:
    """Initialize Jean Claude in the current project.

    Creates the necessary directories and configuration files for
    AI-powered development workflows.

    \b
    Creates:
      - .jc-project.yaml       Project configuration
      - specs/                 Workflow specifications
      - agents/                Agent working directories
      - trees/                 Git worktrees for isolation
      - .jc/                   Internal state (events.db)
      - .claude/commands/      Slash command templates (e.g., /prime)

    Also updates .gitignore to exclude generated directories.
    """
    project_root = Path.cwd()
    config_path = project_root / ".jc-project.yaml"

    # Check if already initialized
    if config_path.exists() and not force:
        console.print(
            Panel(
                "[yellow]Project already initialized.[/yellow]\n\n"
                f"Configuration exists at: [cyan]{config_path}[/cyan]\n\n"
                "Use [bold]--force[/bold] to overwrite.",
                title="[yellow]Already Initialized[/yellow]",
                border_style="yellow",
            )
        )
        raise SystemExit(1)

    console.print()
    console.print("[bold blue]Initializing Jean Claude...[/bold blue]")
    console.print()

    # Create directories
    created_dirs = []
    for dir_name in INIT_DIRECTORIES:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            created_dirs.append(dir_name)

    # Detect or use minimal config
    if minimal:
        config = ProjectConfig()
    else:
        config = ProjectConfig(
            name=detect_project_name(project_root),
            directories=ProjectConfig.model_fields["directories"].default_factory(),
            tooling=ProjectConfig.model_fields["tooling"].default_factory(),
            workflows=ProjectConfig.model_fields["workflows"].default_factory(),
            vcs=ProjectConfig.model_fields["vcs"].default_factory(),
        )
        # Apply detected values
        config.directories.source = detect_source_directory(project_root)
        config.directories.tests = detect_test_directory(project_root)
        config.tooling.test_command = detect_test_command(project_root)

    # Save configuration
    config.save(config_path)

    # Update .gitignore
    gitignore_updated = update_gitignore(project_root)

    # Create slash commands
    created_commands = create_slash_commands(project_root)

    # Install jean-claude-cli skill
    skill_installed = install_skill(project_root)

    # Update or create CLAUDE.md
    claude_md_updated = update_claude_md(project_root)

    # Display results
    results_table = Table(show_header=False, box=None, padding=(0, 2))
    results_table.add_column(style="green")
    results_table.add_column()

    results_table.add_row("✓", f"Created [cyan].jc-project.yaml[/cyan]")

    for dir_name in created_dirs:
        results_table.add_row("✓", f"Created [cyan]{dir_name}/[/cyan]")

    for cmd_name in created_commands:
        results_table.add_row("✓", f"Created [cyan].claude/commands/{cmd_name}[/cyan]")

    if skill_installed:
        results_table.add_row("✓", "Installed [cyan].claude/skills/jean-claude-cli/[/cyan] skill")

    if gitignore_updated:
        results_table.add_row("✓", "Updated [cyan].gitignore[/cyan]")

    if claude_md_updated:
        results_table.add_row("✓", "Updated [cyan]CLAUDE.md[/cyan] with Jean Claude section")

    console.print(results_table)
    console.print()

    # Show detected configuration
    if not minimal:
        config_table = Table(title="Detected Configuration", box=None)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="green")

        config_table.add_row("Project Name", config.name or "(not detected)")
        config_table.add_row("Source Directory", config.directories.source)
        config_table.add_row("Test Directory", config.directories.tests)
        config_table.add_row("Test Command", config.tooling.test_command or "(none)")
        config_table.add_row("Default Model", config.workflows.default_model)

        console.print(config_table)
        console.print()

    console.print(
        Panel(
            "[bold green]Jean Claude initialized successfully![/bold green]\n\n"
            "Next steps:\n"
            "  • Edit [cyan].jc-project.yaml[/cyan] to customize settings\n"
            "  • Run [cyan]jc prime[/cyan] or [cyan]/prime[/cyan] to gather project context\n"
            "  • Run [cyan]jc prompt \"your prompt\"[/cyan] to execute prompts\n"
            "  • Run [cyan]jc run chore \"task\"[/cyan] to start workflows",
            title="[bold green]Success[/bold green]",
            border_style="green",
        )
    )
