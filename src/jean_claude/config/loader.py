# ABOUTME: Configuration loader for Jean Claude CLI
# ABOUTME: Discovers and loads .jc-project.yaml from project root

"""Configuration loader."""

from pathlib import Path
from typing import Optional

from jean_claude.config.models import ProjectConfig

CONFIG_FILENAME = ".jc-project.yaml"


def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find the project root by looking for .jc-project.yaml or .git.

    Args:
        start_path: Directory to start searching from (default: cwd)

    Returns:
        Path to project root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        # Check for Jean Claude config
        if (current / CONFIG_FILENAME).exists():
            return current
        # Check for git root as fallback
        if (current / ".git").exists():
            return current
        current = current.parent

    return None


def load_config(project_root: Optional[Path] = None) -> ProjectConfig:
    """Load project configuration.

    Args:
        project_root: Project root directory (auto-detected if not provided)

    Returns:
        ProjectConfig with loaded or default values
    """
    if project_root is None:
        project_root = find_project_root()
        if project_root is None:
            return ProjectConfig()

    config_path = project_root / CONFIG_FILENAME
    return ProjectConfig.load(config_path)
