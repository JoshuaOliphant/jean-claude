# ABOUTME: FastAPI application for the workflow monitoring dashboard
# ABOUTME: Provides REST API endpoints and SSE streaming for real-time updates

"""FastAPI application for workflow monitoring dashboard."""

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from jean_claude.core.state import WorkflowState


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent / "templates"


def create_app(project_root: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI dashboard application.

    Args:
        project_root: Root directory of the project (defaults to cwd)

    Returns:
        Configured FastAPI application
    """
    if project_root is None:
        project_root = Path.cwd()

    app = FastAPI(
        title="Jean Claude Dashboard",
        description="Real-time workflow monitoring dashboard",
        version="0.1.0",
    )

    templates = Jinja2Templates(directory=get_templates_dir())

    # Store project_root in app state
    app.state.project_root = project_root

    def get_all_workflows() -> list[dict]:
        """Get all workflows from agents directory."""
        agents_dir = project_root / "agents"
        if not agents_dir.exists():
            return []

        workflows = []
        for workflow_dir in agents_dir.iterdir():
            if not workflow_dir.is_dir():
                continue

            state_file = workflow_dir / "state.json"
            if state_file.exists():
                try:
                    with open(state_file) as f:
                        state = json.load(f)
                    workflows.append(state)
                except (json.JSONDecodeError, IOError):
                    continue

        # Sort by updated_at descending
        workflows.sort(
            key=lambda w: w.get("updated_at", ""),
            reverse=True
        )
        return workflows

    def get_workflow_state(workflow_id: str) -> dict | None:
        """Get workflow state by ID."""
        state_file = project_root / "agents" / workflow_id / "state.json"
        if not state_file.exists():
            return None

        try:
            with open(state_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def get_workflow_events(workflow_id: str) -> list[dict] | None:
        """Get events for a workflow."""
        events_file = project_root / "agents" / workflow_id / "events.jsonl"
        if not events_file.exists():
            return None

        events = []
        try:
            with open(events_file) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except IOError:
            return None

        return events

    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, workflow: str | None = None):
        """Render the main dashboard page."""
        workflows = get_all_workflows()

        # Select workflow to display
        selected_workflow = None
        if workflow:
            selected_workflow = get_workflow_state(workflow)
        elif workflows:
            # Default to most recent
            selected_workflow = workflows[0]

        # Get events for selected workflow
        events = []
        if selected_workflow:
            events = get_workflow_events(selected_workflow["workflow_id"]) or []

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "workflows": workflows,
                "selected_workflow": selected_workflow,
                "events": events[-50:],  # Last 50 events
            }
        )

    @app.get("/api/workflows")
    async def api_workflows():
        """Get list of all workflows."""
        return get_all_workflows()

    @app.get("/api/status/{workflow_id}")
    async def api_status(workflow_id: str):
        """Get workflow status by ID."""
        state = get_workflow_state(workflow_id)
        if state is None:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        return state

    @app.get("/api/events/{workflow_id}")
    async def api_events(workflow_id: str):
        """Get events for a workflow."""
        events = get_workflow_events(workflow_id)
        if events is None:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
        return events

    @app.get("/api/events/{workflow_id}/stream")
    async def api_events_stream(workflow_id: str):
        """SSE stream for real-time events."""
        events_file = project_root / "agents" / workflow_id / "events.jsonl"

        if not events_file.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        async def event_generator() -> AsyncGenerator[dict, None]:
            """Generate SSE events from events.jsonl file."""
            last_position = 0

            # First, send existing events
            try:
                with open(events_file) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                event = json.loads(line)
                                yield {
                                    "event": "log",
                                    "data": json.dumps(event)
                                }
                            except json.JSONDecodeError:
                                continue
                    last_position = f.tell()
            except IOError:
                return

            # Then, watch for new events
            while True:
                try:
                    with open(events_file) as f:
                        f.seek(last_position)
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    event = json.loads(line)
                                    yield {
                                        "event": "log",
                                        "data": json.dumps(event)
                                    }
                                except json.JSONDecodeError:
                                    continue
                        last_position = f.tell()
                except IOError:
                    break

                await asyncio.sleep(0.5)

        return EventSourceResponse(event_generator())

    # HTMX partial endpoints for polling updates
    @app.get("/partials/progress/{workflow_id}", response_class=HTMLResponse)
    async def partial_progress(request: Request, workflow_id: str):
        """HTMX partial for progress bar update."""
        state = get_workflow_state(workflow_id)
        if state is None:
            return HTMLResponse("<div>Workflow not found</div>", status_code=404)

        return templates.TemplateResponse(
            "partials/progress.html",
            {"request": request, "workflow": state}
        )

    @app.get("/partials/features/{workflow_id}", response_class=HTMLResponse)
    async def partial_features(request: Request, workflow_id: str):
        """HTMX partial for features list update."""
        state = get_workflow_state(workflow_id)
        if state is None:
            return HTMLResponse("<div>Workflow not found</div>", status_code=404)

        return templates.TemplateResponse(
            "partials/features.html",
            {"request": request, "workflow": state}
        )

    @app.get("/partials/logs/{workflow_id}", response_class=HTMLResponse)
    async def partial_logs(request: Request, workflow_id: str):
        """HTMX partial for logs panel update."""
        events = get_workflow_events(workflow_id)
        if events is None:
            return HTMLResponse("<div>No logs</div>", status_code=404)

        return templates.TemplateResponse(
            "partials/logs.html",
            {"request": request, "events": events[-30:]}
        )

    return app
