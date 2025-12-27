# ABOUTME: Tests for ConventionalCommitParser class
# ABOUTME: Consolidated tests for commit type and scope parsing

"""Tests for ConventionalCommitParser class.

Consolidated from 23 separate tests to focused tests covering
essential behaviors without per-type or per-scope redundancy.
"""

import pytest

from jean_claude.core.conventional_commit_parser import ConventionalCommitParser


class TestConventionalCommitParserTypes:
    """Test commit type parsing - consolidated from 5 tests to 1."""

    @pytest.mark.parametrize("descriptions,expected_type", [
        # feat type
        (["Add login functionality", "Create user registration form", "Implement JWT auth"], "feat"),
        # fix type
        (["Fix login bug", "Resolve timeout issue", "Patch security vulnerability"], "fix"),
        # refactor type
        (["Refactor authentication module", "Simplify query builder", "Restructure API"], "refactor"),
        # test type
        (["Add tests for login endpoint", "Create unit tests for user model"], "test"),
        # docs type
        (["Update README with installation", "Add API documentation"], "docs"),
    ])
    def test_parse_commit_types(self, descriptions, expected_type):
        """Test parsing all commit types from feature descriptions."""
        parser = ConventionalCommitParser()
        for description in descriptions:
            result = parser.parse(description)
            assert result["type"] == expected_type, f"Expected '{expected_type}' for: {description}"


class TestConventionalCommitParserScopes:
    """Test scope extraction - consolidated from 5 tests to 1."""

    @pytest.mark.parametrize("descriptions,expected_scope", [
        # auth scope
        (["Add login functionality", "Fix authentication bug", "Implement JWT auth"], "auth"),
        # api scope
        (["Add REST API endpoints", "Fix API timeout issue", "Refactor API layer"], "api"),
        # models scope
        (["Update user model schema", "Create database model for posts"], "models"),
        # ui scope
        (["Add dashboard component", "Fix button styling", "Update UI layout"], "ui"),
        # database scope
        (["Optimize database queries", "Add database migration"], "database"),
    ])
    def test_parse_scopes(self, descriptions, expected_scope):
        """Test extracting all scope types from descriptions."""
        parser = ConventionalCommitParser()
        for description in descriptions:
            result = parser.parse(description)
            assert result["scope"] == expected_scope, f"Expected '{expected_scope}' scope for: {description}"


class TestConventionalCommitParserEdgeCases:
    """Test edge cases - consolidated from 9 tests to 3."""

    def test_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        parser = ConventionalCommitParser()

        with pytest.raises(ValueError, match="description cannot be empty"):
            parser.parse("")

        with pytest.raises(ValueError, match="description cannot be empty"):
            parser.parse("   ")

    def test_case_insensitive_and_ambiguous_defaults(self):
        """Test case insensitivity and ambiguous description handling."""
        parser = ConventionalCommitParser()

        # Case insensitive
        test_cases = [
            ("ADD LOGIN FEATURE", "feat"),
            ("Fix Authentication Bug", "fix"),
            ("REFACTOR API LAYER", "refactor"),
        ]
        for description, expected_type in test_cases:
            result = parser.parse(description)
            assert result["type"] == expected_type

        # Ambiguous defaults to feat
        for desc in ["Update system configuration", "Modify settings", "Change default behavior"]:
            result = parser.parse(desc)
            assert result["type"] == "feat", f"Expected default 'feat' for: {desc}"

    def test_parse_returns_required_keys(self):
        """Test that parse returns dict with type and scope keys."""
        parser = ConventionalCommitParser()
        result = parser.parse("Add login feature")

        assert isinstance(result, dict)
        assert "type" in result
        assert "scope" in result


class TestConventionalCommitParserContext:
    """Test context and explicit patterns - consolidated from 4 tests to 2."""

    def test_explicit_context_parameter(self):
        """Test parsing with explicit context parameter."""
        parser = ConventionalCommitParser()

        result = parser.parse(
            "Add new feature",
            context={"area": "authentication", "type_hint": "feature"}
        )
        assert result["type"] == "feat"
        assert result["scope"] == "auth"

        # Feature area context
        for context, expected_scope in [
            ({"area": "cli"}, "cli"),
            ({"area": "core"}, "core"),
            ({"area": "utils"}, "utils"),
        ]:
            result = parser.parse("Add new functionality", context=context)
            assert result["scope"] == expected_scope

    def test_common_action_prefixes(self):
        """Test parsing with common action prefixes."""
        parser = ConventionalCommitParser()

        prefix_cases = [
            ("implement user registration", "feat"),
            ("create new component", "feat"),
            ("build authentication system", "feat"),
            ("resolve bug in login", "fix"),
            ("correct validation error", "fix"),
            ("improve code structure", "refactor"),
            ("enhance performance", "refactor")
        ]

        for description, expected_type in prefix_cases:
            result = parser.parse(description)
            assert result["type"] == expected_type, f"Expected '{expected_type}' for: {description}"


class TestConventionalCommitParserIntegration:
    """Integration tests - consolidated from 4 tests to 1."""

    def test_multiple_scopes_and_scope_mapping(self):
        """Test multiple possible scopes and keyword-to-scope mapping."""
        parser = ConventionalCommitParser()

        # Multiple scope keywords - should pick one
        result = parser.parse("Add API endpoint for user authentication")
        assert result["scope"] in ["api", "auth"]

        # Scope mapping
        scope_mapping_cases = [
            ("Add login form", "auth"),
            ("Fix REST endpoint bug", "api"),
            ("Update User model", "models"),
            ("Add button component", "ui"),
            ("Optimize SQL query", "database")
        ]

        for description, expected_scope in scope_mapping_cases:
            result = parser.parse(description)
            assert result["scope"] == expected_scope, f"Expected '{expected_scope}' for: {description}"

        # Commit workflow features
        workflow_descriptions = [
            "Create CommitMessageFormatter class",
            "Implement conventional commit parser",
            "Add git file stager service"
        ]
        for description in workflow_descriptions:
            result = parser.parse(description)
            assert result["type"] == "feat"
            assert result["scope"] in ["commit", "git", "workflow", "commit-workflow", "core", None]
