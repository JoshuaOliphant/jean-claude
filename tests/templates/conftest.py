# ABOUTME: Shared pytest fixtures for tests/templates/ test suite
# ABOUTME: Provides common fixtures for template paths and template content

"""Shared pytest fixtures for template module tests.

These fixtures are automatically available to all tests in tests/templates/.
Import from the root conftest.py for fixtures that should be shared across
all test directories.

USAGE:
    def test_something(beads_spec_template_path):
        content = beads_spec_template_path.read_text()
        assert "# " in content

GUIDELINES:
    1. Use beads_spec_template_path for the beads_spec.md template
    2. Use templates_dir for accessing the templates directory
    3. Add new template path fixtures here as needed
"""

from pathlib import Path

import pytest


# =============================================================================
# Template Directory Fixtures
# =============================================================================


@pytest.fixture
def templates_dir() -> Path:
    """Return the path to the templates directory."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "src" / "jean_claude" / "templates"


# =============================================================================
# Template Path Fixtures
# =============================================================================


@pytest.fixture
def beads_spec_template_path(templates_dir: Path) -> Path:
    """Return the path to the beads_spec.md template.

    This is the primary template used for converting Beads tasks
    to spec files.
    """
    return templates_dir / "beads_spec.md"


# Alias for backward compatibility with existing tests
@pytest.fixture
def template_path(beads_spec_template_path: Path) -> Path:
    """Alias for beads_spec_template_path.

    Provided for backward compatibility with existing tests that
    use 'template_path' fixture.
    """
    return beads_spec_template_path
