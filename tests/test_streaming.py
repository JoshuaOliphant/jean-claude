# ABOUTME: Tests for real-time streaming output functionality
# ABOUTME: Validates streaming display, message handling, and graceful interruption

"""Tests for streaming output functionality."""

import pytest
from rich.console import Console
from io import StringIO

from jean_claude.cli.streaming import StreamingDisplay, stream_output


class TestStreamingDisplay:
    """Test the StreamingDisplay class."""

    def test_initialization(self):
        """Test that StreamingDisplay initializes correctly."""
        console = Console()
        display = StreamingDisplay(console, show_thinking=False)

        assert display.console == console
        assert display.show_thinking is False
        assert display.text_blocks == []
        assert display.tool_uses == []
        assert display.current_tool is None

    def test_add_text(self):
        """Test adding text blocks to the display."""
        console = Console()
        display = StreamingDisplay(console)

        display.add_text("First block")
        display.add_text("Second block")

        assert len(display.text_blocks) == 2
        assert display.text_blocks[0] == "First block"
        assert display.text_blocks[1] == "Second block"

    def test_get_full_output(self):
        """Test getting the complete accumulated output."""
        console = Console()
        display = StreamingDisplay(console)

        display.add_text("Line 1")
        display.add_text("Line 2")
        display.add_text("Line 3")

        output = display.get_full_output()
        assert output == "Line 1\nLine 2\nLine 3"

    def test_get_full_output_empty(self):
        """Test getting output when no text has been added."""
        console = Console()
        display = StreamingDisplay(console)

        output = display.get_full_output()
        assert output == "No response received"

    def test_tool_tracking(self):
        """Test tool use tracking."""
        console = Console()
        display = StreamingDisplay(console, show_thinking=True)

        # Start a tool
        display.start_tool("Read")
        assert len(display.tool_uses) == 1
        assert display.tool_uses[0] == ("Read", "running")
        assert display.current_tool == "Read"

        # Finish the tool
        display.finish_tool()
        assert display.tool_uses[0] == ("Read", "done")
        assert display.current_tool is None

        # Start another tool
        display.start_tool("Write")
        assert len(display.tool_uses) == 2
        assert display.tool_uses[1] == ("Write", "running")

    def test_tool_tracking_disabled(self):
        """Test that tool tracking works even when not showing thinking."""
        console = Console()
        display = StreamingDisplay(console, show_thinking=False)

        display.start_tool("Read")
        assert len(display.tool_uses) == 1


class MockMessage:
    """Mock message for testing."""

    def __init__(self, msg_type, content=None):
        self.msg_type = msg_type
        self.content = content or []


class MockTextBlock:
    """Mock text block for testing."""

    def __init__(self, text):
        self.text = text


@pytest.mark.asyncio
async def test_stream_output_empty():
    """Test streaming with no messages."""
    console = Console(file=StringIO())

    async def empty_stream():
        # Yield nothing
        return
        yield  # Make it a generator

    # Should handle empty stream gracefully
    result = await stream_output(empty_stream(), console, show_thinking=False)
    assert result == "No response received"


@pytest.mark.asyncio
async def test_stream_output_interrupt():
    """Test that KeyboardInterrupt is handled gracefully."""
    console = Console(file=StringIO())

    async def interrupt_stream():
        yield MockMessage("text")
        raise KeyboardInterrupt()

    # Should raise KeyboardInterrupt but not crash
    with pytest.raises(KeyboardInterrupt):
        await stream_output(interrupt_stream(), console, show_thinking=False)
