# ABOUTME: FastAPI application for the workflow monitoring dashboard
# ABOUTME: Provides REST API endpoints and SSE streaming for real-time updates

"""FastAPI application for workflow monitoring dashboard."""

import asyncio
import json
import logging
import uuid
from collections import deque
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from jean_claude.core.state import WorkflowState
from jean_claude.core.workflow_utils import get_all_workflows as get_all_workflow_states

# Configure logging for connection monitoring
logger = logging.getLogger(__name__)


def get_templates_dir() -> Path:
    """Get the path to the templates directory."""
    return Path(__file__).parent / "templates"


def get_recent_events(events_file: Path, max_events: int = 1000) -> list[dict]:
    """Get only the most recent events to limit memory usage.

    Uses collections.deque with maxlen for memory-efficient loading of recent events.
    This prevents loading entire large event files into memory.

    Args:
        events_file: Path to the events.jsonl file
        max_events: Maximum number of recent events to load (default: 1000)

    Returns:
        List of most recent events, or empty list if file doesn't exist/has errors
    """
    if not events_file.exists():
        return []

    events = []
    try:
        with open(events_file) as f:
            # Use deque with maxlen for memory efficiency - automatically discards old items
            recent_lines = deque(f, maxlen=max_events)

        for line in recent_lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except IOError:
        return []

    return events


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

    # Track active SSE connections per workflow to prevent memory leaks
    # Format: {workflow_id: connection_count}
    app.state.active_connections: dict[str, int] = {}

    def get_all_workflows() -> list[dict]:
        """Get all workflows from agents directory."""
        workflow_states = get_all_workflow_states(project_root)
        # Convert WorkflowState objects to dict format for API compatibility
        return [workflow.model_dump() for workflow in workflow_states]

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

    def get_workflow_events(workflow_id: str, max_events: int = 1000) -> list[dict] | None:
        """Get recent events for a workflow (memory-efficient).

        Args:
            workflow_id: Workflow ID to get events for
            max_events: Maximum number of recent events to load (default: 1000)

        Returns:
            List of recent events, or None if workflow not found
        """
        events_file = project_root / "agents" / workflow_id / "events.jsonl"
        if not events_file.exists():
            return None

        # Use memory-efficient loading to prevent loading huge files into memory
        events = get_recent_events(events_file, max_events)
        return events if events else None

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
    async def api_events_stream(workflow_id: str, request: Request):
        """SSE stream for real-time events with memory leak protection.

        Features:
        - Connection timeout (1 hour max)
        - Connection limits (max 5 per workflow)
        - Memory-efficient event loading (recent 1000 events only)
        - Proper lifecycle logging and cleanup
        """
        events_file = project_root / "agents" / workflow_id / "events.jsonl"

        if not events_file.exists():
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        # Enforce connection limit to prevent memory exhaustion
        MAX_CONNECTIONS_PER_WORKFLOW = 5
        current_connections = app.state.active_connections.get(workflow_id, 0)

        if current_connections >= MAX_CONNECTIONS_PER_WORKFLOW:
            logger.warning(
                f"SSE connection limit reached for workflow {workflow_id}: "
                f"{current_connections}/{MAX_CONNECTIONS_PER_WORKFLOW}"
            )
            raise HTTPException(
                status_code=429,
                detail=f"Too many active connections for workflow {workflow_id}. "
                       f"Maximum {MAX_CONNECTIONS_PER_WORKFLOW} concurrent streams allowed."
            )

        # Increment connection counter
        app.state.active_connections[workflow_id] = current_connections + 1
        connection_id = str(uuid.uuid4())[:8]

        logger.info(
            f"SSE connection opened: {connection_id} for workflow {workflow_id} "
            f"(active: {app.state.active_connections[workflow_id]}/{MAX_CONNECTIONS_PER_WORKFLOW})"
        )

        async def event_generator() -> AsyncGenerator[dict, None]:
            """Generate SSE events with timeout and memory protection."""
            try:
                start_time = asyncio.get_event_loop().time()
                max_duration = 3600  # 1 hour maximum connection duration
                last_position = 0

                # First, send only recent events (not entire history) to limit memory usage
                # Load max 1000 recent events instead of entire file
                recent_events = get_recent_events(events_file, max_events=1000)

                for event in recent_events:
                    yield {
                        "event": "log",
                        "data": json.dumps(event)
                    }

                # Get file position after loading recent events
                try:
                    with open(events_file) as f:
                        f.seek(0, 2)  # Seek to end of file
                        last_position = f.tell()
                except IOError:
                    logger.warning(f"Could not seek to end of {events_file}")
                    return

                # Then, watch for new events with timeout protection
                while True:
                    # Check connection timeout to prevent infinite loops
                    elapsed = asyncio.get_event_loop().time() - start_time
                    if elapsed > max_duration:
                        logger.info(
                            f"SSE connection timeout: {connection_id} after {elapsed:.0f}s "
                            f"(max: {max_duration}s)"
                        )
                        yield {
                            "event": "close",
                            "data": json.dumps({
                                "reason": "max_duration_exceeded",
                                "message": "Connection closed after 1 hour. Please refresh to reconnect."
                            })
                        }
                        break

                    # Check if client disconnected
                    if await request.is_disconnected():
                        logger.info(f"SSE client disconnected: {connection_id}")
                        break

                    # Poll for new events
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
                                        logger.warning(f"Invalid JSON in events file: {line[:100]}")
                                        continue
                            last_position = f.tell()
                    except IOError as e:
                        logger.error(f"Error reading events file: {e}")
                        break

                    # Sleep between polls (500ms)
                    await asyncio.sleep(0.5)

            finally:
                # CRITICAL: Always decrement connection counter, even on error/disconnect
                current = app.state.active_connections.get(workflow_id, 0)
                app.state.active_connections[workflow_id] = max(0, current - 1)

                logger.info(
                    f"SSE connection closed: {connection_id} for workflow {workflow_id} "
                    f"(remaining: {app.state.active_connections[workflow_id]})"
                )

        # Return SSE response with proper HTTP headers
        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        }

        return EventSourceResponse(event_generator(), headers=headers)

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
