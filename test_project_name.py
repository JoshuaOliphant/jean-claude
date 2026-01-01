#!/usr/bin/env python3
"""Test project name appears in escalation notifications."""

import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.tools.mailbox_tools import escalate_to_human
from rich.console import Console

console = Console()

# Test 1: Auto-detected project name
console.print("[cyan]Test 1: Auto-detected project name[/cyan]")
console.print(f"Current directory: {Path.cwd().name}")
console.print()

escalate_to_human(
    title="Test: Auto-detected Project",
    message="This is a test with auto-detected project name from Path.cwd().name",
    priority=3,
    tags=["test", "construction"]
)

console.print("[green]✅ Sent escalation with auto-detected project name[/green]")
console.print(f"   Title should be: [{Path.cwd().name}] Test: Auto-detected Project")
console.print()

# Test 2: Explicit project name
console.print("[cyan]Test 2: Explicit project name[/cyan]")

escalate_to_human(
    title="Test: Explicit Project",
    message="This is a test with explicitly set project name",
    priority=3,
    tags=["test", "construction"],
    project_name="my-api-server"
)

console.print("[green]✅ Sent escalation with explicit project name[/green]")
console.print("   Title should be: [my-api-server] Test: Explicit Project")
console.print()

console.print("[bold green]Check your ntfy app for both notifications![/bold green]")
console.print()
console.print("Expected titles:")
console.print(f"  1. [{Path.cwd().name}] Test: Auto-detected Project")
console.print("  2. [my-api-server] Test: Explicit Project")
