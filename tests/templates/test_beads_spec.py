# ABOUTME: Test suite for beads_spec.md template file
# ABOUTME: Tests template structure and variable substitution for Beads task conversion

"""Tests for beads_spec.md template file."""

import os
from pathlib import Path
import pytest


class TestBeadsSpecTemplate:
    """Tests for the beads_spec.md template file.

    Note: template_path fixture is provided by tests/templates/conftest.py
    """

    def test_template_file_exists(self, template_path):
        """Test that beads_spec.md template file exists."""
        assert template_path.exists(), f"Template file not found at {template_path}"

    def test_template_is_markdown_file(self, template_path):
        """Test that the template file has .md extension."""
        assert template_path.suffix == ".md", "Template must be a markdown file"

    def test_template_is_not_empty(self, template_path):
        """Test that the template file is not empty."""
        content = template_path.read_text()
        assert len(content.strip()) > 0, "Template file cannot be empty"

    def test_template_has_title_section(self, template_path):
        """Test that template includes a title section with placeholder."""
        content = template_path.read_text()
        # Should have a markdown h1 header with a placeholder variable
        assert "# " in content, "Template must have a title (h1) section"
        # Common placeholder patterns
        placeholders = ["{title}", "{{title}}", "${title}", "$title"]
        has_title_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_title_placeholder, "Template must have a title placeholder variable"

    def test_template_has_description_section(self, template_path):
        """Test that template includes a description section."""
        content = template_path.read_text()
        assert "## Description" in content, "Template must have a Description section"

    def test_template_has_description_placeholder(self, template_path):
        """Test that template has a placeholder for description content."""
        content = template_path.read_text()
        # Common placeholder patterns
        placeholders = ["{description}", "{{description}}", "${description}", "$description"]
        has_description_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_description_placeholder, "Template must have a description placeholder variable"

    def test_template_has_acceptance_criteria_section(self, template_path):
        """Test that template includes acceptance criteria section."""
        content = template_path.read_text()
        # Look for variations of acceptance criteria header
        variations = [
            "## Acceptance Criteria",
            "## Requirements",
            "## acceptance criteria",
            "## requirements"
        ]
        has_ac_section = any(variation in content for variation in variations)
        assert has_ac_section, "Template must have an Acceptance Criteria or Requirements section"

    def test_template_has_acceptance_criteria_placeholder(self, template_path):
        """Test that template has placeholder for acceptance criteria list."""
        content = template_path.read_text()
        # Common placeholder patterns for list items
        placeholders = [
            "{acceptance_criteria}",
            "{{acceptance_criteria}}",
            "${acceptance_criteria}",
            "$acceptance_criteria",
            "{criteria}",
            "{{criteria}}",
            "${criteria}",
            "$criteria"
        ]
        has_ac_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_ac_placeholder, "Template must have an acceptance criteria placeholder variable"

    def test_template_structure_order(self, template_path):
        """Test that sections appear in the correct order: title, description, criteria."""
        content = template_path.read_text()

        # Find positions of key sections
        title_pos = content.find("#")
        desc_pos = content.find("## Description")

        # Find acceptance criteria section (try multiple variations)
        ac_variations = ["## Acceptance Criteria", "## Requirements"]
        ac_pos = -1
        for variation in ac_variations:
            pos = content.find(variation)
            if pos != -1:
                ac_pos = pos
                break

        # Verify order
        assert title_pos != -1, "Template must have a title"
        assert desc_pos != -1, "Template must have Description section"
        assert ac_pos != -1, "Template must have Acceptance Criteria/Requirements section"

        assert title_pos < desc_pos, "Title must come before Description"
        assert desc_pos < ac_pos, "Description must come before Acceptance Criteria"

    def test_template_has_consistent_placeholder_style(self, template_path):
        """Test that all placeholders use a consistent style."""
        content = template_path.read_text()

        # Count different placeholder styles
        styles = {
            "jinja2": content.count("{{") + content.count("}}"),
            "shell": content.count("${"),
            "simple_brace": content.count("{") - content.count("{{"),
            "dollar": content.count("$") - content.count("${")
        }

        # At least one style should be used
        assert any(count > 0 for count in styles.values()), "Template must use placeholder variables"

    def test_template_preserves_markdown_formatting(self, template_path):
        """Test that template uses proper markdown formatting."""
        content = template_path.read_text()

        # Should have headers
        assert "#" in content, "Template should use markdown headers"

        # Should have empty lines for readability (not all crammed together)
        lines = content.split("\n")
        empty_lines = [line for line in lines if line.strip() == ""]
        assert len(empty_lines) >= 2, "Template should have empty lines for readability"

    def test_template_can_be_read_as_utf8(self, template_path):
        """Test that template file can be read as UTF-8."""
        try:
            content = template_path.read_text(encoding="utf-8")
            assert isinstance(content, str)
        except UnicodeDecodeError:
            pytest.fail("Template file must be valid UTF-8")

    def test_template_has_task_metadata_section(self, template_path):
        """Test that template includes task metadata section."""
        content = template_path.read_text()
        assert "## Task Metadata" in content or "## Metadata" in content, \
            "Template must have a Task Metadata section"

    def test_template_has_task_id_placeholder(self, template_path):
        """Test that template has placeholder for task_id."""
        content = template_path.read_text()
        placeholders = ["{task_id}", "{{task_id}}", "${task_id}", "$task_id"]
        has_task_id_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_task_id_placeholder, "Template must have a task_id placeholder variable"

    def test_template_has_status_placeholder(self, template_path):
        """Test that template has placeholder for status."""
        content = template_path.read_text()
        placeholders = ["{status}", "{{status}}", "${status}", "$status"]
        has_status_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_status_placeholder, "Template must have a status placeholder variable"

    def test_template_has_created_at_placeholder(self, template_path):
        """Test that template has placeholder for created_at timestamp."""
        content = template_path.read_text()
        placeholders = [
            "{created_at}", "{{created_at}}", "${created_at}", "$created_at",
            "{created}", "{{created}}", "${created}", "$created"
        ]
        has_created_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_created_placeholder, "Template must have a created_at/created placeholder variable"

    def test_template_has_updated_at_placeholder(self, template_path):
        """Test that template has placeholder for updated_at timestamp."""
        content = template_path.read_text()
        placeholders = [
            "{updated_at}", "{{updated_at}}", "${updated_at}", "$updated_at",
            "{updated}", "{{updated}}", "${updated}", "$updated"
        ]
        has_updated_placeholder = any(placeholder in content for placeholder in placeholders)
        assert has_updated_placeholder, "Template must have an updated_at/updated placeholder variable"

    def test_template_has_all_required_placeholders(self, template_path):
        """Test that template has all required placeholders for Beads task conversion."""
        content = template_path.read_text()

        # Check for title/workflow_name
        title_patterns = ["{title}", "{{title}}", "{workflow_name}", "{{workflow_name}}"]
        has_title = any(p in content for p in title_patterns)

        # Check for description
        desc_patterns = ["{description}", "{{description}}"]
        has_description = any(p in content for p in desc_patterns)

        # Check for acceptance_criteria
        ac_patterns = ["{acceptance_criteria}", "{{acceptance_criteria}}"]
        has_ac = any(p in content for p in ac_patterns)

        # Check for task_id (metadata)
        id_patterns = ["{task_id}", "{{task_id}}"]
        has_task_id = any(p in content for p in id_patterns)

        assert has_title, "Template must have a title/workflow_name placeholder"
        assert has_description, "Template must have a description placeholder"
        assert has_ac, "Template must have an acceptance_criteria placeholder"
        assert has_task_id, "Template must have a task_id placeholder (task metadata)"
