# ABOUTME: Real-time streaming output display for Claude Code execution
# ABOUTME: Uses Rich Live for smooth terminal updates as messages arrive

"""Streaming output display for Claude Code."""

from typing import Any, AsyncIterator, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

try:
    from claude_agent_sdk import AssistantMessage, TextBlock, ToolResultMessage
except ImportError:
    # Graceful fallback if SDK not installed
    AssistantMessage = None
    TextBlock = None
    ToolResultMessage = None


class StreamingDisplay:
    """Manages real-time display of streaming Claude output."""

    def __init__(self, console: Console, show_thinking: bool = False):
        """Initialize streaming display.

        Args:
            console: Rich console for output
            show_thinking: Whether to show internal thinking/tool uses
        """
        self.console = console
        self.show_thinking = show_thinking
        self.text_blocks: list[str] = []
        self.tool_uses: list[tuple[str, str]] = []  # (tool_name, status)
        self.current_tool: Optional[str] = None

    def _create_display(self) -> Group:
        """Create the current display renderable."""
        items = []

        # Show accumulated text
        if self.text_blocks:
            text = "\n".join(self.text_blocks)
            try:
                items.append(Markdown(text))
            except Exception:
                # Fall back to plain text if markdown parsing fails
                items.append(Text(text))

        # Show tool uses if enabled
        if self.show_thinking and self.tool_uses:
            tool_text = Text()
            for tool_name, status in self.tool_uses[-3:]:  # Show last 3
                if status == "running":
                    tool_text.append(f"⚙️  {tool_name}...\n", style="cyan")
                elif status == "done":
                    tool_text.append(f"✓ {tool_name}\n", style="green dim")
            if tool_text:
                items.append(Panel(tool_text, title="[cyan]Tools[/cyan]", border_style="cyan"))

        return Group(*items) if items else Text("[dim]Waiting for response...[/dim]")

    def add_text(self, text: str) -> None:
        """Add a text block to the display."""
        self.text_blocks.append(text)

    def start_tool(self, tool_name: str) -> None:
        """Mark a tool as running."""
        self.current_tool = tool_name
        self.tool_uses.append((tool_name, "running"))

    def finish_tool(self) -> None:
        """Mark the current tool as done."""
        if self.tool_uses and self.tool_uses[-1][1] == "running":
            tool_name = self.tool_uses[-1][0]
            self.tool_uses[-1] = (tool_name, "done")
        self.current_tool = None

    def render(self) -> Group:
        """Render the current display."""
        return self._create_display()

    def get_full_output(self) -> str:
        """Get the complete accumulated output."""
        return "\n".join(self.text_blocks) if self.text_blocks else "No response received"


async def stream_output(
    message_stream: AsyncIterator,
    console: Console,
    show_thinking: bool = False,
) -> str:
    """Stream messages to console in real-time.

    Args:
        message_stream: Async iterator of messages from Claude SDK
        console: Rich console for output
        show_thinking: Whether to show tool uses and thinking

    Returns:
        Complete accumulated output text
    """
    display = StreamingDisplay(console, show_thinking)

    with Live(display.render(), console=console, refresh_per_second=4) as live:
        try:
            async for message in message_stream:
                # Handle AssistantMessage (text + tool uses)
                if AssistantMessage and isinstance(message, AssistantMessage):
                    for block in message.content:
                        if TextBlock and isinstance(block, TextBlock):
                            display.add_text(block.text)
                        elif show_thinking:
                            # Tool use blocks
                            tool_name = getattr(block, "name", type(block).__name__)
                            display.start_tool(tool_name)

                # Handle ToolResultMessage
                elif ToolResultMessage and isinstance(message, ToolResultMessage):
                    if show_thinking:
                        display.finish_tool()

                # Update the live display
                live.update(display.render())

        except KeyboardInterrupt:
            # Graceful handling of Ctrl+C
            console.print("\n[yellow]Interrupted by user[/yellow]")
            raise

    return display.get_full_output()


async def stream_output_simple(
    message_stream: AsyncIterator,
    console: Console,
) -> str:
    """Simple streaming output without Rich formatting.

    Useful for --raw mode or when minimal output is desired.

    Args:
        message_stream: Async iterator of messages from Claude SDK
        console: Rich console for output

    Returns:
        Complete accumulated output text
    """
    text_blocks: list[str] = []

    try:
        async for message in message_stream:
            if AssistantMessage and isinstance(message, AssistantMessage):
                for block in message.content:
                    if TextBlock and isinstance(block, TextBlock):
                        # Print immediately as it arrives
                        console.print(block.text, end="")
                        text_blocks.append(block.text)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise

    return "\n".join(text_blocks) if text_blocks else "No response received"
