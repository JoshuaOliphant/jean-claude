"""Utility to map all barrel imports from jean_claude.core.

This module searches the codebase for all files that import from jean_claude.core
and creates a comprehensive mapping of which files use which exports.
"""

import ast
import json
from pathlib import Path
from typing import Any


class BarrelImportMapper:
    """Maps all barrel imports from jean_claude.core in the codebase."""

    def __init__(self, root_dir: Path | None = None):
        """Initialize the mapper.

        Args:
            root_dir: Root directory of the project. Defaults to current directory.
        """
        self.root_dir = root_dir or Path.cwd()
        self.src_dir = self.root_dir / "src"
        self.tests_dir = self.root_dir / "tests"

    def find_python_files(self, directory: Path) -> list[Path]:
        """Find all Python files in a directory recursively.

        Args:
            directory: Directory to search

        Returns:
            List of Python file paths
        """
        if not directory.exists():
            return []
        return list(directory.rglob("*.py"))

    def extract_imports_from_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract all jean_claude.core imports from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of import dictionaries with module and items
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    # Check if importing from jean_claude.core or its submodules
                    if node.module and node.module.startswith("jean_claude.core"):
                        import_items = []
                        for alias in node.names:
                            import_items.append(alias.name)

                        imports.append({
                            "module": node.module,
                            "items": import_items
                        })

            return imports

        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files that can't be parsed
            print(f"Warning: Could not parse {file_path}: {e}")
            return []

    def map_all_imports(self) -> dict[str, Any]:
        """Map all barrel imports in the codebase.

        Returns:
            Dictionary with file paths and their imports, plus summary statistics
        """
        all_files_data = []

        # Process src directory
        src_files = self.find_python_files(self.src_dir)
        for file_path in src_files:
            imports = self.extract_imports_from_file(file_path)
            if imports:  # Only include files that have imports
                relative_path = file_path.relative_to(self.root_dir)
                all_files_data.append({
                    "path": str(relative_path),
                    "imports": imports
                })

        # Process tests directory
        test_files = self.find_python_files(self.tests_dir)
        for file_path in test_files:
            imports = self.extract_imports_from_file(file_path)
            if imports:  # Only include files that have imports
                relative_path = file_path.relative_to(self.root_dir)
                all_files_data.append({
                    "path": str(relative_path),
                    "imports": imports
                })

        # Calculate summary statistics
        total_files = len(all_files_data)
        total_imports = sum(len(f["imports"]) for f in all_files_data)
        src_files_count = len([f for f in all_files_data if f["path"].startswith("src/")])
        test_files_count = len([f for f in all_files_data if f["path"].startswith("tests/")])

        return {
            "summary": {
                "total_files": total_files,
                "total_imports": total_imports,
                "src_files": src_files_count,
                "test_files": test_files_count
            },
            "files": all_files_data
        }

    def generate_mapping_file(self, output_path: Path | None = None) -> Path:
        """Generate the barrel import mapping file.

        Args:
            output_path: Path to write the mapping file. Defaults to barrel_imports_mapping.json

        Returns:
            Path to the generated mapping file
        """
        if output_path is None:
            output_path = self.root_dir / "barrel_imports_mapping.json"

        mapping_data = self.map_all_imports()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(mapping_data, f, indent=2)

        return output_path


def main():
    """Main entry point for the barrel import mapper."""
    mapper = BarrelImportMapper()
    output_file = mapper.generate_mapping_file()
    print(f"Barrel import mapping generated: {output_file}")

    # Print summary
    with open(output_file, "r") as f:
        data = json.load(f)

    summary = data["summary"]
    print("\nSummary:")
    print(f"  Total files with barrel imports: {summary['total_files']}")
    print(f"  Total import statements: {summary['total_imports']}")
    print(f"  Source files: {summary['src_files']}")
    print(f"  Test files: {summary['test_files']}")


if __name__ == "__main__":
    main()
