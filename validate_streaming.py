#!/usr/bin/env python3
# ABOUTME: Validation script for streaming implementation
# ABOUTME: Confirms all requirements from jean_claude-n3g are met

"""Validate streaming implementation completeness."""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and report."""
    exists = path.exists()
    status = "[green]✓[/green]" if exists else "[red]✗[/red]"
    console.print(f"{status} {description}: {path}")
    return exists


def check_function_exists(module_path: str, function_name: str) -> bool:
    """Check if a function exists in a module."""
    try:
        parts = module_path.split(".")
        module = __import__(module_path, fromlist=[parts[-1]])
        exists = hasattr(module, function_name)
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"{status} Function {function_name} in {module_path}")
        return exists
    except ImportError as e:
        console.print(f"[red]✗[/red] Could not import {module_path}: {e}")
        return False


def check_cli_flag(flag: str) -> bool:
    """Check if CLI flag exists in prompt command."""
    from jean_claude.cli.commands.prompt import prompt
    import inspect

    # Get the click command's params
    if hasattr(prompt, "params"):
        param_names = [p.name for p in prompt.params]
        exists = flag in param_names
        status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"{status} CLI flag --{flag}")
        return exists
    return False


def main():
    """Run all validation checks."""
    console.print("\n[bold]Jean Claude Streaming Implementation Validation[/bold]\n")

    results = []

    # File existence checks
    console.print("[bold cyan]File Existence Checks:[/bold cyan]")
    results.append(
        check_file_exists(
            Path("src/jean_claude/core/sdk_executor.py"),
            "SDK executor module",
        )
    )
    results.append(
        check_file_exists(
            Path("src/jean_claude/cli/streaming.py"),
            "Streaming display module",
        )
    )
    results.append(
        check_file_exists(
            Path("src/jean_claude/cli/commands/prompt.py"),
            "Prompt command module",
        )
    )
    results.append(
        check_file_exists(
            Path("tests/test_streaming.py"),
            "Streaming tests",
        )
    )

    # Function existence checks
    console.print("\n[bold cyan]Function Existence Checks:[/bold cyan]")
    results.append(
        check_function_exists(
            "jean_claude.core.sdk_executor",
            "execute_prompt_streaming",
        )
    )
    results.append(
        check_function_exists(
            "jean_claude.cli.streaming",
            "StreamingDisplay",
        )
    )
    results.append(
        check_function_exists(
            "jean_claude.cli.streaming",
            "stream_output",
        )
    )

    # CLI flag checks
    console.print("\n[bold cyan]CLI Flag Checks:[/bold cyan]")
    results.append(check_cli_flag("stream"))
    results.append(check_cli_flag("show_thinking"))

    # Test execution
    console.print("\n[bold cyan]Running Tests:[/bold cyan]")
    import subprocess

    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "tests/test_streaming.py", "-v"],
            capture_output=True,
            text=True,
            check=False,
        )
        tests_passed = result.returncode == 0
        status = "[green]✓[/green]" if tests_passed else "[red]✗[/red]"
        console.print(f"{status} Streaming tests")

        if tests_passed:
            # Count passed tests
            import re
            matches = re.findall(r"(\d+) passed", result.stdout)
            if matches:
                console.print(f"  [dim]({matches[0]} tests passed)[/dim]")
        else:
            console.print(f"  [red]Test output:[/red]\n{result.stdout}")

        results.append(tests_passed)
    except Exception as e:
        console.print(f"[red]✗[/red] Could not run tests: {e}")
        results.append(False)

    # Summary
    console.print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)

    if passed == total:
        console.print(f"\n[bold green]✅ All Checks Passed ({passed}/{total})[/bold green]")
        console.print("\n[green]Streaming implementation is complete and working![/green]")
        return 0
    else:
        console.print(f"\n[bold red]❌ Some Checks Failed ({passed}/{total})[/bold red]")
        console.print(f"\n[red]{total - passed} check(s) failed[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
