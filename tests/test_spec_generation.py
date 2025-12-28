# ABOUTME: Test suite for generate_spec_from_beads function
# ABOUTME: Consolidated tests for spec generation from Beads task data

"""Tests for generate_spec_from_beads function.

Consolidated from 32 separate tests to focused tests covering
essential behaviors without per-field or per-character redundancy.
"""

from datetime import datetime
import pytest

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus, generate_spec_from_beads


class TestGenerateSpecFromBeads:
    """Tests for generate_spec_from_beads function."""

    @pytest.fixture
    def basic_task(self):
        """Create a basic BeadsTask for testing."""
        return BeadsTask(
            id="test-123",
            title="Test Task Title",
            description="This is a test task description.",
            acceptance_criteria=["Criterion 1", "Criterion 2", "Criterion 3"],
            status=BeadsTaskStatus.OPEN,
            created_at=datetime(2025, 1, 1, 12, 0, 0),
            updated_at=datetime(2025, 1, 2, 12, 0, 0)
        )

    def test_generate_spec_complete_structure(self, basic_task):
        """Test that generated spec has complete structure with all sections."""
        spec = generate_spec_from_beads(basic_task)

        # Is valid non-empty string
        assert isinstance(spec, str)
        assert len(spec.strip()) > 0

        # Has title as h1
        assert "# Test Task Title" in spec

        # Has Description section with content
        assert "## Description" in spec
        assert "This is a test task description." in spec

        # Has Acceptance Criteria section with all criteria as bullets
        assert "## Acceptance Criteria" in spec
        assert "- Criterion 1" in spec
        assert "- Criterion 2" in spec
        assert "- Criterion 3" in spec

        # Has metadata section with all fields
        assert "## Task Metadata" in spec
        assert "**Task ID**: test-123" in spec
        assert "**Status**: open" in spec
        assert "**Created**: 2025-01-01 12:00:00" in spec
        assert "**Updated**: 2025-01-02 12:00:00" in spec
        assert "---" in spec  # Separator before metadata

        # Proper markdown structure
        lines = spec.split('\n')
        assert any(line.startswith('# ') for line in lines)
        assert any(line.startswith('## ') for line in lines)
        assert '\n\n' in spec  # Has blank lines for readability
        assert spec.endswith('\n')

        # Correct section order
        title_pos = spec.find("# Test Task Title")
        desc_pos = spec.find("## Description")
        ac_pos = spec.find("## Acceptance Criteria")
        assert title_pos < desc_pos < ac_pos

    def test_generate_spec_without_acceptance_criteria(self, mock_beads_task_factory):
        """Test spec generation for task without acceptance criteria."""
        task = mock_beads_task_factory(
            title="Simple Task",
            description="A task without acceptance criteria.",
            acceptance_criteria=[],
            status=BeadsTaskStatus.IN_PROGRESS
        )
        spec = generate_spec_from_beads(task)

        assert isinstance(spec, str)
        assert len(spec.strip()) > 0
        assert "# Simple Task" in spec
        assert "## Description" in spec
        assert "A task without acceptance criteria." in spec

    def test_generate_spec_with_multiline_description(self, mock_beads_task_factory):
        """Test that multi-line descriptions are preserved."""
        task = mock_beads_task_factory(
            title="Complex Task",
            description="Line 1 of description.\nLine 2 of description.\nLine 3 of description.",
            acceptance_criteria=["Must handle multiple lines"]
        )
        spec = generate_spec_from_beads(task)

        assert "Line 1 of description." in spec
        assert "Line 2 of description." in spec
        assert "Line 3 of description." in spec

    def test_generate_spec_with_none_task(self):
        """Test that passing None raises ValueError."""
        with pytest.raises(ValueError, match="task cannot be None"):
            generate_spec_from_beads(None)

    def test_generate_spec_preserves_special_characters_and_unicode(self):
        """Test that special characters, unicode, markdown, and code are preserved."""
        task = BeadsTask(
            id="test-special",
            title="Task with émojis 🚀 and ünïcödé: Special & Chars!",
            description=(
                "Description with **bold**, *italic*, `code`, & < > 'quotes'\n"
                "Unicode: café, naïve, 日本語\n"
                "Code block:\n```python\ndef hello():\n    print('world')\n```"
            ),
            acceptance_criteria=["✓ Handle unicode", "✗ Don't fail"],
            status=BeadsTaskStatus.OPEN
        )
        spec = generate_spec_from_beads(task)

        # Special characters preserved
        assert "& Chars!" in spec
        assert "**bold**" in spec
        assert "*italic*" in spec
        assert "`code`" in spec

        # Unicode preserved
        assert "émojis 🚀" in spec
        assert "café" in spec
        assert "日本語" in spec
        assert "✓ Handle unicode" in spec

        # Code block preserved
        assert "```python" in spec
        assert "def hello():" in spec

    @pytest.mark.parametrize("status", [BeadsTaskStatus.OPEN, BeadsTaskStatus.IN_PROGRESS, BeadsTaskStatus.CLOSED])
    def test_generate_spec_with_different_statuses(self, mock_beads_task_factory, status):
        """Test spec generation with different task statuses."""
        task = mock_beads_task_factory(
            title=f"Task {status.value}",
            description=f"Task with status {status.value}",
            status=status
        )
        spec = generate_spec_from_beads(task)

        assert isinstance(spec, str)
        assert f"# Task {status.value}" in spec
        assert "## Description" in spec

    def test_generate_spec_with_many_criteria(self, mock_beads_task_factory):
        """Test spec generation with many acceptance criteria."""
        criteria = [f"Criterion {i}" for i in range(1, 11)]
        task = mock_beads_task_factory(
            title="Task with Many Criteria",
            description="Test description",
            acceptance_criteria=criteria
        )
        spec = generate_spec_from_beads(task)

        for criterion in criteria:
            assert f"- {criterion}" in spec

    def test_generate_spec_is_idempotent(self, basic_task):
        """Test that calling generate_spec_from_beads multiple times produces same result."""
        spec1 = generate_spec_from_beads(basic_task)
        spec2 = generate_spec_from_beads(basic_task)
        assert spec1 == spec2


class TestGenerateSpecIntegration:
    """Integration tests for spec generation workflow."""

    def test_generate_spec_from_json_to_spec(self):
        """Test complete workflow: JSON -> BeadsTask -> Spec."""
        task_dict = {
            "id": "workflow-123",
            "title": "Implement Feature X",
            "description": "Add new feature to the application",
            "acceptance_criteria": [
                "Feature works as expected",
                "Tests pass",
                "Documentation updated"
            ],
            "status": "in_progress"
        }

        task = BeadsTask.from_dict(task_dict)
        spec = generate_spec_from_beads(task)

        assert "# Implement Feature X" in spec
        assert "## Description" in spec
        assert "Add new feature to the application" in spec
        assert "## Acceptance Criteria" in spec
        assert "- Feature works as expected" in spec
        assert "- Tests pass" in spec
        assert "- Documentation updated" in spec

    def test_spec_can_be_written_to_file(self, tmp_path, mock_beads_task_factory):
        """Test that generated spec can be written to a file."""
        task = mock_beads_task_factory(
            title="Test Task Title",
            description="Description",
            acceptance_criteria=["Criterion"]
        )
        spec = generate_spec_from_beads(task)

        spec_file = tmp_path / "test_spec.md"
        spec_file.write_text(spec)

        assert spec_file.exists()
        content = spec_file.read_text()
        assert content == spec
        assert "# Test Task Title" in content
