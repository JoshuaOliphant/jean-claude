"""Tests for barrel import mapping functionality."""

import json
from pathlib import Path

import pytest


def test_barrel_import_mapping_file_exists():
    """Test that the barrel import mapping file is created."""
    mapping_file = Path("barrel_imports_mapping.json")
    assert mapping_file.exists(), "barrel_imports_mapping.json should exist"


def test_barrel_import_mapping_valid_json():
    """Test that the barrel import mapping file contains valid JSON."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)
    assert isinstance(data, dict), "Mapping should be a dictionary"


def test_barrel_import_mapping_has_files_list():
    """Test that the mapping has a files list."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)
    assert "files" in data, "Mapping should contain 'files' key"
    assert isinstance(data["files"], list), "Files should be a list"


def test_barrel_import_mapping_has_summary():
    """Test that the mapping has summary statistics."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    assert "summary" in data, "Mapping should contain 'summary' key"
    assert isinstance(data["summary"], dict), "Summary should be a dictionary"

    # Check summary fields
    summary = data["summary"]
    assert "total_files" in summary, "Summary should contain 'total_files'"
    assert "total_imports" in summary, "Summary should contain 'total_imports'"
    assert "src_files" in summary, "Summary should contain 'src_files'"
    assert "test_files" in summary, "Summary should contain 'test_files'"


def test_barrel_import_mapping_file_structure():
    """Test that each file entry has the correct structure."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    files = data["files"]
    assert len(files) > 0, "Should have at least one file with barrel imports"

    # Check first file structure
    first_file = files[0]
    assert "path" in first_file, "File entry should have 'path'"
    assert "imports" in first_file, "File entry should have 'imports'"
    assert isinstance(first_file["imports"], list), "Imports should be a list"


def test_barrel_import_mapping_import_structure():
    """Test that each import entry has the correct structure."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    # Find a file with imports
    files_with_imports = [f for f in data["files"] if f["imports"]]
    assert len(files_with_imports) > 0, "Should have files with imports"

    # Check first import structure
    first_import = files_with_imports[0]["imports"][0]
    assert "module" in first_import, "Import should have 'module'"
    assert "items" in first_import, "Import should have 'items'"
    assert isinstance(first_import["items"], list), "Items should be a list"


def test_barrel_import_mapping_counts_match():
    """Test that the counts in summary match actual data."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    # Count actual files
    actual_files = len(data["files"])
    assert data["summary"]["total_files"] == actual_files, "total_files should match actual count"

    # Count actual imports across all files
    actual_imports = sum(len(f["imports"]) for f in data["files"])
    assert data["summary"]["total_imports"] == actual_imports, "total_imports should match actual count"

    # Count src vs test files
    actual_src_files = len([f for f in data["files"] if f["path"].startswith("src/")])
    actual_test_files = len([f for f in data["files"] if f["path"].startswith("tests/")])

    assert data["summary"]["src_files"] == actual_src_files, "src_files should match actual count"
    assert data["summary"]["test_files"] == actual_test_files, "test_files should match actual count"


def test_barrel_import_mapping_no_duplicates():
    """Test that there are no duplicate file paths in the mapping."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    file_paths = [f["path"] for f in data["files"]]
    assert len(file_paths) == len(set(file_paths)), "Should have no duplicate file paths"


def test_barrel_import_mapping_has_expected_files():
    """Test that the mapping includes expected files that import from jean_claude.core."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    file_paths = [f["path"] for f in data["files"]]

    # Check for some key files we know should be there
    expected_files = [
        "src/jean_claude/cli/commands/work.py",
        "src/jean_claude/orchestration/auto_continue.py",
        "tests/test_state.py",
    ]

    for expected in expected_files:
        assert expected in file_paths, f"{expected} should be in the mapping"


def test_barrel_import_mapping_module_formats():
    """Test that module names follow expected patterns."""
    mapping_file = Path("barrel_imports_mapping.json")
    with open(mapping_file, "r") as f:
        data = json.load(f)

    # Check that all modules start with jean_claude.core
    for file_data in data["files"]:
        for import_data in file_data["imports"]:
            module = import_data["module"]
            assert module.startswith("jean_claude.core"), \
                f"Module {module} should start with jean_claude.core"
