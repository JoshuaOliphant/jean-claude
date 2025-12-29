"""Tests for file_utils module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from jean_claude.core.file_utils import read_jsonl_file


class TestReadJsonlFile:
    """Test cases for read_jsonl_file function."""

    def test_read_valid_jsonl_file(self, tmp_path):
        """Test reading a valid JSONL file with multiple lines."""
        # Arrange
        jsonl_file = tmp_path / "test.jsonl"
        data = [
            {"id": 1, "name": "Alice", "age": 30},
            {"id": 2, "name": "Bob", "age": 25},
            {"id": 3, "name": "Charlie", "age": 35},
        ]

        with open(jsonl_file, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 3
        assert result == data

    def test_read_jsonl_file_with_empty_lines(self, tmp_path):
        """Test reading JSONL file with empty lines."""
        # Arrange
        jsonl_file = tmp_path / "test_empty_lines.jsonl"
        data = [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
        ]

        with open(jsonl_file, "w") as f:
            f.write(json.dumps(data[0]) + "\n")
            f.write("\n")  # Empty line
            f.write(json.dumps(data[1]) + "\n")
            f.write("\n")  # Empty line at end

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 2
        assert result == data

    def test_read_jsonl_file_skips_invalid_json(self, tmp_path):
        """Test that invalid JSON lines are silently skipped."""
        # Arrange
        jsonl_file = tmp_path / "test_invalid.jsonl"

        with open(jsonl_file, "w") as f:
            f.write(json.dumps({"id": 1, "valid": True}) + "\n")
            f.write("{ invalid json }\n")  # Invalid JSON
            f.write(json.dumps({"id": 2, "valid": True}) + "\n")
            f.write("not json at all\n")  # Invalid JSON
            f.write(json.dumps({"id": 3, "valid": True}) + "\n")

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 3
        assert all(item["valid"] is True for item in result)
        assert [item["id"] for item in result] == [1, 2, 3]

    def test_read_jsonl_file_handles_missing_file(self, tmp_path):
        """Test that missing files are handled gracefully."""
        # Arrange
        missing_file = tmp_path / "nonexistent.jsonl"

        # Act
        result = list(read_jsonl_file(missing_file))

        # Assert
        assert result == []

    def test_read_jsonl_file_yields_dictionaries(self, tmp_path):
        """Test that the function yields dictionaries one at a time."""
        # Arrange
        jsonl_file = tmp_path / "test_yield.jsonl"
        data = [{"index": i} for i in range(5)]

        with open(jsonl_file, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        # Act & Assert - Test that it's a generator
        generator = read_jsonl_file(jsonl_file)
        assert hasattr(generator, "__iter__")
        assert hasattr(generator, "__next__")

        # Test yielding one by one
        first = next(generator)
        assert first == {"index": 0}

        second = next(generator)
        assert second == {"index": 1}

        # Consume the rest
        rest = list(generator)
        assert len(rest) == 3

    def test_read_jsonl_file_with_complex_data(self, tmp_path):
        """Test reading JSONL with complex nested data structures."""
        # Arrange
        jsonl_file = tmp_path / "test_complex.jsonl"
        data = [
            {
                "user": {"name": "Alice", "email": "alice@example.com"},
                "tags": ["python", "testing"],
                "metadata": {"created": "2024-01-01", "count": 42},
            },
            {
                "user": {"name": "Bob", "email": "bob@example.com"},
                "tags": ["javascript", "react"],
                "metadata": {"created": "2024-01-02", "count": 100},
            },
        ]

        with open(jsonl_file, "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 2
        assert result == data
        assert result[0]["user"]["name"] == "Alice"
        assert result[1]["tags"] == ["javascript", "react"]

    def test_read_jsonl_file_empty_file(self, tmp_path):
        """Test reading an empty JSONL file."""
        # Arrange
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.touch()  # Create empty file

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert result == []

    def test_read_jsonl_file_accepts_string_path(self, tmp_path):
        """Test that the function accepts string paths."""
        # Arrange
        jsonl_file = tmp_path / "test_string_path.jsonl"
        data = [{"id": 1}]

        with open(jsonl_file, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        # Act - Pass string instead of Path object
        result = list(read_jsonl_file(str(jsonl_file)))

        # Assert
        assert result == data

    def test_read_jsonl_file_accepts_path_object(self, tmp_path):
        """Test that the function accepts Path objects."""
        # Arrange
        jsonl_file = Path(tmp_path) / "test_path_object.jsonl"
        data = [{"id": 1}]

        with open(jsonl_file, "w") as f:
            f.write(json.dumps(data[0]) + "\n")

        # Act - Pass Path object
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert result == data

    def test_read_jsonl_file_with_whitespace_only_lines(self, tmp_path):
        """Test that lines with only whitespace are handled."""
        # Arrange
        jsonl_file = tmp_path / "test_whitespace.jsonl"
        data = [{"id": 1}, {"id": 2}]

        with open(jsonl_file, "w") as f:
            f.write(json.dumps(data[0]) + "\n")
            f.write("   \n")  # Whitespace only
            f.write("\t\n")   # Tab only
            f.write(json.dumps(data[1]) + "\n")

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 2
        assert result == data

    def test_read_jsonl_file_with_unicode(self, tmp_path):
        """Test reading JSONL with Unicode characters."""
        # Arrange
        jsonl_file = tmp_path / "test_unicode.jsonl"
        data = [
            {"text": "Hello 世界", "emoji": "🚀"},
            {"text": "Привет мир", "emoji": "🌍"},
        ]

        with open(jsonl_file, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Act
        result = list(read_jsonl_file(jsonl_file))

        # Assert
        assert len(result) == 2
        assert result == data
        assert result[0]["text"] == "Hello 世界"
        assert result[1]["emoji"] == "🌍"
