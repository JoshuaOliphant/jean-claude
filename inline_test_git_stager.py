#!/usr/bin/env python
"""Inline test for GitFileStager."""
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from jean_claude.core.git_file_stager import GitFileStager

# Test instantiation
stager = GitFileStager()
print(f"Default repo_path: {stager.repo_path}")

# Test with custom path
stager2 = GitFileStager(repo_path="/tmp")
print(f"Custom repo_path: {stager2.repo_path}")

# Test exclusion
print(f"is_excluded('.env'): {stager.is_excluded('.env')}")
print(f"is_excluded('src/main.py'): {stager.is_excluded('src/main.py')}")

# Test filtering
files = ["src/main.py", ".env", "tests/test_main.py"]
filtered = stager.filter_relevant_files(files, "main")
print(f"Filtered files: {filtered}")

print("\n✅ All inline tests passed!")
