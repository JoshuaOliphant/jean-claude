# ABOUTME: CLI command for upgrading Jean Claude to the latest version
# ABOUTME: Checks PyPI for updates and upgrades using uv or pip

import subprocess
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from jean_claude import __version__

console = Console()


def get_latest_version() -> Optional[str]:
    """Fetch the latest version from PyPI JSON API."""
    import json
    from urllib import request
    from urllib.error import URLError

    try:
        with request.urlopen(
            "https://pypi.org/pypi/jean-claude/json", timeout=10
        ) as response:
            data = json.loads(response.read().decode())
            return data["info"]["version"]
    except (URLError, KeyError, json.JSONDecodeError):
        return None


def upgrade_with_uv() -> bool:
    """Upgrade using uv."""
    try:
        result = subprocess.run(
            ["uv", "pip", "install", "--upgrade", "jean-claude"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def upgrade_with_pip() -> bool:
    """Upgrade using pip."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "jean-claude"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


@click.command()
@click.option(
    "--check",
    is_flag=True,
    help="Check for updates without installing",
)
def upgrade(check: bool) -> None:
    """Upgrade Jean Claude to the latest version.

    Checks PyPI for the latest release and upgrades the installed
    package using uv (preferred) or pip.

    Examples:
        jc upgrade              # Upgrade to latest version
        jc upgrade --check      # Check for updates only
    """
    console.print()
    console.print("[bold blue]Jean Claude Upgrade[/bold blue]")
    console.print()

    # Show current version
    console.print(f"Current version: [cyan]{__version__}[/cyan]")

    # Fetch latest version
    console.print("Checking PyPI for updates...", end="")
    latest = get_latest_version()

    if not latest:
        console.print(" [red]✗[/red]")
        console.print()
        console.print(
            Panel(
                "[yellow]Could not check for updates.[/yellow]\n\n"
                "Try manually upgrading:\n"
                "  [cyan]uv pip install --upgrade jean-claude[/cyan]\n"
                "  [dim]or[/dim]\n"
                "  [cyan]pip install --upgrade jean-claude[/cyan]",
                title="[yellow]Update Check Failed[/yellow]",
                border_style="yellow",
            )
        )
        raise SystemExit(1)

    console.print(" [green]✓[/green]")
    console.print(f"Latest version:  [green]{latest}[/green]")
    console.print()

    # Compare versions
    if latest == __version__:
        console.print(
            Panel(
                f"[green]You're running the latest version ({__version__})![/green]",
                title="[green]Up to Date[/green]",
                border_style="green",
            )
        )
        return

    # Just check, don't upgrade
    if check:
        console.print(
            Panel(
                f"[yellow]Update available: {__version__} → {latest}[/yellow]\n\n"
                f"Run [cyan]jc upgrade[/cyan] to install.",
                title="[yellow]Update Available[/yellow]",
                border_style="yellow",
            )
        )
        return

    # Confirm upgrade
    console.print(
        f"[yellow]Update available: {__version__} → {latest}[/yellow]"
    )
    console.print()

    if not click.confirm("Proceed with upgrade?"):
        console.print("[yellow]Upgrade cancelled[/yellow]")
        return

    console.print()
    console.print("Upgrading...", end="")

    # Try uv first, fall back to pip
    success = upgrade_with_uv() or upgrade_with_pip()

    if success:
        console.print(" [green]✓[/green]")
        console.print()
        console.print(
            Panel(
                f"[green]Successfully upgraded to {latest}![/green]\n\n"
                "Restart your terminal or run:\n"
                "  [cyan]hash -r[/cyan]  (bash/zsh)\n"
                "  [dim]or[/dim]\n"
                "  [cyan]rehash[/cyan]  (fish)",
                title="[green]Upgrade Complete[/green]",
                border_style="green",
            )
        )
    else:
        console.print(" [red]✗[/red]")
        console.print()
        console.print(
            Panel(
                "[red]Upgrade failed.[/red]\n\n"
                "Try manually upgrading:\n"
                "  [cyan]uv pip install --upgrade jean-claude[/cyan]\n"
                "  [dim]or[/dim]\n"
                "  [cyan]pip install --upgrade jean-claude[/cyan]",
                title="[red]Upgrade Failed[/red]",
                border_style="red",
            )
        )
        raise SystemExit(1)
