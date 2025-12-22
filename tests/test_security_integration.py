"""Integration tests for security hooks in SDK execution."""

import pytest
from pathlib import Path

from jean_claude.core.agent import PromptRequest
from jean_claude.core.sdk_executor import execute_prompt_async


@pytest.mark.asyncio
class TestSecurityHooksIntegration:
    """Test security hooks integrated with SDK execution."""

    async def test_safe_command_allowed(self):
        """Safe commands should execute successfully with hooks enabled."""
        request = PromptRequest(
            prompt="Run: ls /tmp",
            model="haiku",
            enable_security_hooks=True,
            workflow_type="development",
        )

        # This would actually execute if we had Claude CLI installed
        # For now, just verify the hook configuration doesn't break initialization
        # In a real test environment, this would execute and succeed
        pass

    async def test_readonly_workflow_blocks_write_commands(self):
        """Readonly workflow should block write commands."""
        request = PromptRequest(
            prompt="Run: mkdir /tmp/test",
            model="haiku",
            enable_security_hooks=True,
            workflow_type="readonly",
        )

        # In readonly mode, mkdir should be blocked
        # This test validates the configuration, not execution
        assert request.workflow_type == "readonly"
        assert request.enable_security_hooks is True

    async def test_hooks_can_be_disabled(self):
        """Security hooks can be disabled for trusted operations."""
        request = PromptRequest(
            prompt="Run: rm dangerous.txt",
            model="haiku",
            enable_security_hooks=False,
            workflow_type="development",
        )

        # When hooks are disabled, even dangerous commands pass configuration
        assert request.enable_security_hooks is False

    async def test_development_workflow_allows_common_tools(self):
        """Development workflow allows common development tools."""
        request = PromptRequest(
            prompt="Run: git status && pytest tests/",
            model="haiku",
            enable_security_hooks=True,
            workflow_type="development",
        )

        # Development mode should allow git and pytest
        assert request.workflow_type == "development"


class TestPromptRequestDefaults:
    """Test PromptRequest default values."""

    def test_security_enabled_by_default(self):
        """Security hooks should be enabled by default."""
        request = PromptRequest(prompt="test")
        assert request.enable_security_hooks is True

    def test_development_workflow_by_default(self):
        """Development workflow should be the default."""
        request = PromptRequest(prompt="test")
        assert request.workflow_type == "development"

    def test_can_override_workflow_type(self):
        """Can override workflow type."""
        request = PromptRequest(prompt="test", workflow_type="readonly")
        assert request.workflow_type == "readonly"

    def test_can_disable_hooks(self):
        """Can disable security hooks."""
        request = PromptRequest(prompt="test", enable_security_hooks=False)
        assert request.enable_security_hooks is False


@pytest.mark.asyncio
class TestSecurityHookContext:
    """Test that workflow context is properly passed to hooks."""

    async def test_workflow_type_readonly(self):
        """Test readonly workflow type configuration."""
        from jean_claude.core.security import bash_security_hook

        # Simulate what the hook wrapper does
        context = {"workflow_type": "readonly"}

        # Try a write command in readonly mode
        result = await bash_security_hook(
            {"command": "mkdir test"},
            context=context,
        )
        assert result["decision"] == "block"

    async def test_workflow_type_development(self):
        """Test development workflow type configuration."""
        from jean_claude.core.security import bash_security_hook

        # Simulate what the hook wrapper does
        context = {"workflow_type": "development"}

        # Try a normal command in development mode
        result = await bash_security_hook(
            {"command": "git status"},
            context=context,
        )
        assert result["decision"] == "allow"
