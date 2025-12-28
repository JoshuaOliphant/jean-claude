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
INIT_DIRECTORIES = ["specs", "agents", "trees", ".jc", ".claude/commands"]

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

    # Display results
    results_table = Table(show_header=False, box=None, padding=(0, 2))
    results_table.add_column(style="green")
    results_table.add_column()

    results_table.add_row("✓", f"Created [cyan].jc-project.yaml[/cyan]")

    for dir_name in created_dirs:
        results_table.add_row("✓", f"Created [cyan]{dir_name}/[/cyan]")

    for cmd_name in created_commands:
        results_table.add_row("✓", f"Created [cyan].claude/commands/{cmd_name}[/cyan]")

    if gitignore_updated:
        results_table.add_row("✓", "Updated [cyan].gitignore[/cyan]")

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
