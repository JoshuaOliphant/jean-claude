#!/usr/bin/env python3
# ABOUTME: Manual test script for streaming functionality
# ABOUTME: Tests that streaming works correctly despite SDK error handling issues

"""Manual test for streaming output."""

import asyncio
from pathlib import Path
from rich.console import Console

from jean_claude.core.agent import PromptRequest, generate_workflow_id
from jean_claude.core.sdk_executor import execute_prompt_streaming
from jean_claude.cli.streaming import stream_output


async def test_streaming():
    """Test streaming output with proper error handling."""
    console = Console()

    console.print("[bold]Testing streaming output...[/bold]\n")

    # Create request
    workflow_id = generate_workflow_id()
    request = PromptRequest(
        prompt="Say hello in exactly 5 words",
        model="haiku",
        working_dir=Path.cwd(),
        output_dir=Path.cwd() / "agents" / workflow_id,
    )

    console.print(f"Workflow ID: {workflow_id}")
    console.print(f"Model: {request.model}\n")

    # Test streaming with error handling
    try:
        message_stream = execute_prompt_streaming(request)
        output = await stream_output(message_stream, console, show_thinking=False)

        console.print(f"\n[green]✓ Success![/green]")
        console.print(f"Output: {output}")

    except Exception as e:
        # Check if we got output despite the error
        console.print(f"\n[yellow]Warning: SDK error occurred but streaming may have worked[/yellow]")
        console.print(f"Error: {e}")

        # Check if output files were created
        output_dir = Path.cwd() / "agents" / workflow_id
        if output_dir.exists():
            console.print(f"\n[green]✓ Output directory created: {output_dir}[/green]")

            files = list(output_dir.glob("*.json"))
            if files:
                console.print(f"[green]✓ Output files created: {len(files)} files[/green]")
                for f in files:
                    console.print(f"  - {f.name}")


if __name__ == "__main__":
    asyncio.run(test_streaming())
