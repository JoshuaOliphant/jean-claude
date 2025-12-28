# ABOUTME: CLI command to start the web dashboard server
# ABOUTME: Launches FastAPI with uvicorn for real-time workflow monitoring

"""Start the workflow monitoring web dashboard."""

import webbrowser
from pathlib import Path

import click
from rich.console import Console

console = Console()


@click.command()
@click.option(
    "--port", "-p",
    type=int,
    default=8765,
    help="Port to run the dashboard server on (default: 8765)",
)
@click.option(
    "--host", "-h",
    type=str,
    default="127.0.0.1",
    help="Host to bind the server to (default: 127.0.0.1)",
)
@click.option(
    "--workflow", "-w",
    type=str,
    default=None,
    help="Workflow ID to open directly",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't automatically open the browser",
)
def dashboard(port: int, host: str, workflow: str | None, no_browser: bool) -> None:
    """Start the workflow monitoring web dashboard.

    Launches a FastAPI server with real-time HTMX updates for monitoring
    workflow progress, features, and activity logs.

    \b
    Examples:
      jc dashboard                   # Start on localhost:8765
      jc dashboard --port 9000       # Use custom port
      jc dashboard --workflow abc123 # Open specific workflow
      jc dashboard --no-browser      # Don't auto-open browser
    """
    import uvicorn

    from jean_claude.dashboard.app import create_app

    project_root = Path.cwd()
    app = create_app(project_root=project_root)

    # Build URL
    url = f"http://{host}:{port}"
    if workflow:
        url += f"?workflow={workflow}"

    console.print(f"\n[bold blue]Jean Claude Dashboard[/bold blue]")
    console.print(f"[dim]Starting server at {url}[/dim]\n")

    # Open browser (unless disabled)
    if not no_browser:
        webbrowser.open(url)

    # Run the server
    console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="warning",  # Reduce uvicorn noise
        )
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped[/dim]")
