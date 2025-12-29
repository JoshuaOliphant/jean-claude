#!/usr/bin/env python3
"""Script to generate the barrel import mapping."""

import sys
from pathlib import Path

# Add src to path so we can import our module
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.utils.barrel_import_mapper import BarrelImportMapper

if __name__ == "__main__":
    mapper = BarrelImportMapper()
    output_file = mapper.generate_mapping_file()
    print(f"Barrel import mapping generated: {output_file}")

    # Print summary
    import json
    with open(output_file, "r") as f:
        data = json.load(f)

    summary = data["summary"]
    print("\nSummary:")
    print(f"  Total files with barrel imports: {summary['total_files']}")
    print(f"  Total import statements: {summary['total_imports']}")
    print(f"  Source files: {summary['src_files']}")
    print(f"  Test files: {summary['test_files']}")
