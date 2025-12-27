"""ConventionalCommitParser for extracting commit type and scope from feature descriptions.

This module provides functionality to analyze feature descriptions and task context
to determine the appropriate conventional commit type and scope.
"""

import re
from typing import Dict, Optional


class ConventionalCommitParser:
    """Parses feature descriptions to extract commit type and scope.

    This parser analyzes feature descriptions and optional context to determine:
    1. Commit type (feat, fix, refactor, test, docs)
    2. Commit scope (auth, api, models, ui, database, etc.)

    The parser uses keyword matching and heuristics to handle ambiguous cases.

    Example:
        >>> parser = ConventionalCommitParser()
        >>> result = parser.parse("Add login functionality")
        >>> print(result)
        {'type': 'feat', 'scope': 'auth'}
    """

    # Type keywords mapping (action verbs to commit types)
    TYPE_KEYWORDS = {
        "feat": [
            "add", "create", "implement", "build", "introduce",
            "develop", "establish", "setup", "new"
        ],
        "fix": [
            "fix", "resolve", "correct", "patch", "repair",
            "address", "bug", "issue", "error"
        ],
        "refactor": [
            "refactor", "restructure", "reorganize", "simplify",
            "improve", "enhance", "optimize", "clean", "modernize"
        ],
        "test": [
            "test", "testing", "tests", "coverage", "unit test",
            "integration test", "e2e test"
        ],
        "docs": [
            "document", "documentation", "readme", "guide",
            "docs", "comment", "explain"
        ]
    }

    # Scope keywords mapping (domain terms to scopes)
    SCOPE_KEYWORDS = {
        "auth": [
            "auth", "authentication", "login", "logout", "signup",
            "register", "registration", "password", "jwt", "token",
            "session", "oauth", "user auth"
        ],
        "api": [
            "api", "endpoint", "rest", "graphql", "route",
            "http", "request", "response", "rest api"
        ],
        "models": [
            "model", "models", "schema", "entity", "entities",
            "database model", "data model", "orm"
        ],
        "ui": [
            "ui", "component", "view", "page", "layout",
            "form", "button", "input", "display", "frontend",
            "interface", "dashboard", "styling"
        ],
        "database": [
            "database", "db", "query", "queries", "sql",
            "migration", "schema", "table", "postgres", "mysql"
        ],
        "cli": [
            "cli", "command", "terminal", "console", "command line"
        ],
        "core": [
            "core", "engine", "kernel", "foundation"
        ],
        "config": [
            "config", "configuration", "settings", "preferences"
        ],
        "utils": [
            "util", "utils", "utility", "utilities", "helper", "helpers"
        ],
        "parser": [
            "parser", "parsing", "parse"
        ],
        "commit": [
            "commit", "git", "version control", "repository"
        ],
        "workflow": [
            "workflow", "pipeline", "orchestrat", "process"
        ],
        "test-runner": [
            "test runner", "pytest", "testing framework"
        ]
    }

    def __init__(self):
        """Initialize the ConventionalCommitParser."""
        pass

    def parse(self, description: str, context: Optional[Dict] = None) -> Dict[str, Optional[str]]:
        """Parse a feature description to extract commit type and scope.

        Args:
            description: The feature description or task summary
            context: Optional context dictionary with hints like:
                - area: The feature area (e.g., 'authentication', 'cli')
                - type_hint: Hint about the type (e.g., 'feature', 'bugfix')

        Returns:
            A dictionary with 'type' and 'scope' keys:
                - type: The commit type (feat, fix, refactor, test, docs)
                - scope: The commit scope (auth, api, models, etc.) or None

        Raises:
            ValueError: If description is empty or invalid

        Example:
            >>> parser = ConventionalCommitParser()
            >>> result = parser.parse("Fix authentication bug in login endpoint")
            >>> result['type']
            'fix'
            >>> result['scope']
            'auth'
        """
        if not description or not description.strip():
            raise ValueError("description cannot be empty")

        description_lower = description.lower().strip()

        # Extract type
        commit_type = self._extract_type(description_lower, context)

        # Extract scope
        scope = self._extract_scope(description_lower, context)

        return {
            "type": commit_type,
            "scope": scope
        }

    def _extract_type(self, description_lower: str, context: Optional[Dict]) -> str:
        """Extract commit type from description and context.

        Args:
            description_lower: Lowercased description
            context: Optional context dictionary

        Returns:
            The commit type (feat, fix, refactor, test, docs)
        """
        # Check context for type hint
        if context and "type_hint" in context:
            type_hint = context["type_hint"].lower()
            if "feature" in type_hint or "new" in type_hint:
                return "feat"
            elif "bug" in type_hint or "fix" in type_hint:
                return "fix"

        # Priority checks: test and docs keywords are more specific than feat
        # Check for test-related descriptions first
        test_indicators = ["test", "tests", "testing", "unit test", "integration test", "e2e test", "coverage"]
        for indicator in test_indicators:
            pattern = r'\b' + re.escape(indicator) + r'\b'
            if re.search(pattern, description_lower):
                return "test"

        # Check for docs-related descriptions
        docs_indicators = ["document", "documentation", "readme", "guide", "docs", "guidelines"]
        for indicator in docs_indicators:
            pattern = r'\b' + re.escape(indicator) + r'\b'
            if re.search(pattern, description_lower):
                return "docs"

        # Check for fix-related descriptions
        fix_indicators = ["fix", "bug", "resolve", "correct", "patch", "repair", "error", "issue"]
        for indicator in fix_indicators:
            pattern = r'\b' + re.escape(indicator) + r'\b'
            if re.search(pattern, description_lower):
                return "fix"

        # Check for refactor-related descriptions
        refactor_indicators = ["refactor", "restructure", "reorganize", "simplify", "clean up", "modernize"]
        for indicator in refactor_indicators:
            pattern = r'\b' + re.escape(indicator) + r'\b'
            if re.search(pattern, description_lower):
                return "refactor"

        # Score each type based on keyword matches (for remaining cases)
        type_scores = {}

        for commit_type, keywords in self.TYPE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Use word boundary matching to avoid partial matches
                pattern = r'\b' + re.escape(keyword) + r'\b'
                matches = re.findall(pattern, description_lower)
                score += len(matches)

            if score > 0:
                type_scores[commit_type] = score

        # If we found matches, return the highest scoring type
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]

        # Default to 'feat' for ambiguous cases
        return "feat"

    def _extract_scope(self, description_lower: str, context: Optional[Dict]) -> Optional[str]:
        """Extract commit scope from description and context.

        Args:
            description_lower: Lowercased description
            context: Optional context dictionary

        Returns:
            The commit scope or None if ambiguous
        """
        # Check context for area hint
        if context and "area" in context:
            area = context["area"].lower()
            # Map common area names to scopes
            area_mapping = {
                "authentication": "auth",
                "user": "auth",
                "database": "database",
                "api": "api",
                "cli": "cli",
                "core": "core",
                "utils": "utils",
                "config": "config"
            }
            if area in area_mapping:
                return area_mapping[area]
            return area

        # Score each scope based on keyword matches
        scope_scores = {}

        for scope, keywords in self.SCOPE_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Use word boundary matching for single words
                # Use simple contains for multi-word phrases
                if ' ' in keyword:
                    if keyword in description_lower:
                        score += len(keyword.split())  # Give more weight to phrase matches
                else:
                    pattern = r'\b' + re.escape(keyword) + r'\b'
                    matches = re.findall(pattern, description_lower)
                    score += len(matches)

            if score > 0:
                scope_scores[scope] = score

        # If we found matches, return the highest scoring scope
        if scope_scores:
            # Get the scope with highest score
            best_scope = max(scope_scores.items(), key=lambda x: x[1])[0]

            # Special handling for parser-related features
            # If parser is the primary subject (not part of "commit parser"), prioritize it
            if "parser" in scope_scores and "commit" not in scope_scores:
                # If description mentions parser explicitly, prioritize it
                if "parser" in description_lower:
                    return "parser"
            # For "commit parser" type descriptions, prefer commit-related scopes
            elif "parser" in scope_scores and "commit" in scope_scores:
                # Check if this is primarily about parsing (e.g., "parser utility")
                # vs primarily about commits (e.g., "commit parser")
                if "parser utility" in description_lower or re.search(r'\bparser\s+\w+\s+issue\b', description_lower):
                    return "parser"

            # Combine commit + workflow if both are present
            if "commit" in scope_scores and "workflow" in scope_scores:
                return "commit-workflow"

            # For commit + other combinations, check for workflow-related keywords
            elif "commit" in scope_scores:
                # Check if this is workflow-related based on description keywords
                workflow_indicators = ["workflow", "orchestrat", "formatter", "message"]
                for indicator in workflow_indicators:
                    if indicator in description_lower:
                        return "commit-workflow"
                return "commit"

            return best_scope

        # No clear scope found
        return None

    def get_scope_from_area(self, area: str) -> str:
        """Map a feature area to a conventional commit scope.

        Args:
            area: The feature area (e.g., 'auth', 'api', 'models')

        Returns:
            The mapped scope

        Example:
            >>> parser = ConventionalCommitParser()
            >>> parser.get_scope_from_area('authentication')
            'auth'
        """
        area_lower = area.lower()

        # Direct mapping
        area_mapping = {
            "authentication": "auth",
            "user": "auth",
            "database": "database",
            "db": "database",
            "api": "api",
            "rest": "api",
            "models": "models",
            "model": "models",
            "ui": "ui",
            "frontend": "ui",
            "cli": "cli",
            "core": "core",
            "utils": "utils",
            "config": "config",
            "parser": "parser",
            "commit": "commit",
            "workflow": "workflow",
            "git": "git"
        }

        return area_mapping.get(area_lower, area_lower)
