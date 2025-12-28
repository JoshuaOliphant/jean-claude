#!/usr/bin/env python
"""Quick verification for GitFileStager implementation."""

from pathlib import Path

# Check that the implementation file exists
impl_file = Path("src/jean_claude/core/git_file_stager.py")
test_file = Path("tests/test_git_file_stager.py")

print("Verifying GitFileStager feature...")
print()

# Check files exist
if impl_file.exists():
    print(f"✅ Implementation file exists: {impl_file}")
else:
    print(f"❌ Implementation file missing: {impl_file}")
    exit(1)

if test_file.exists():
    print(f"✅ Test file exists: {test_file}")
else:
    print(f"❌ Test file missing: {test_file}")
    exit(1)

# Try importing the module
try:
    from jean_claude.core.git_file_stager import GitFileStager
    print("✅ GitFileStager can be imported")
except Exception as e:
    print(f"❌ Failed to import GitFileStager: {e}")
    exit(1)

# Test basic instantiation
try:
    stager = GitFileStager()
    print("✅ GitFileStager can be instantiated")
except Exception as e:
    print(f"❌ Failed to instantiate GitFileStager: {e}")
    exit(1)

# Test with custom path
try:
    stager = GitFileStager(repo_path="/tmp")
    print("✅ GitFileStager accepts custom repo_path")
except Exception as e:
    print(f"❌ Failed to create GitFileStager with custom path: {e}")
    exit(1)

# Test exclusion logic
try:
    stager = GitFileStager()
    assert stager.is_excluded(".env") == True
    assert stager.is_excluded("src/main.py") == False
    print("✅ Exclusion logic works correctly")
except Exception as e:
    print(f"❌ Exclusion logic failed: {e}")
    exit(1)

# Test filter_relevant_files
try:
    stager = GitFileStager()
    files = ["src/main.py", ".env", "tests/test_main.py"]
    filtered = stager.filter_relevant_files(files, "main feature")
    assert "src/main.py" in filtered
    assert ".env" not in filtered
    print("✅ filter_relevant_files works correctly")
except Exception as e:
    print(f"❌ filter_relevant_files failed: {e}")
    exit(1)

print()
print("="*60)
print("✅ ALL BASIC VERIFICATIONS PASSED!")
print("="*60)
print()
print("GitFileStager implementation is ready.")
print("Run full test suite with: python run_git_file_stager_tests.py")
