# ABOUTME: Jinja2 template rendering for workflow prompts
# ABOUTME: Renders workflow templates with project configuration variables

"""Jinja2 template rendering for workflow prompts."""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape


class TemplateRenderer:
    """Renders Jinja2 templates for workflow prompts."""

    def __init__(self, template_dirs: list[Path]) -> None:
        """Initialize the template renderer.

        Args:
            template_dirs: List of directories to search for templates
        """
        self.env = Environment(
            loader=FileSystemLoader([str(d) for d in template_dirs]),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., "chore.md.j2")
            context: Variables to pass to the template

        Returns:
            Rendered template content
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_string(
        self,
        template_string: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a template string with the given context.

        Args:
            template_string: Template content as a string
            context: Variables to pass to the template

        Returns:
            Rendered content
        """
        template = self.env.from_string(template_string)
        return template.render(**context)
