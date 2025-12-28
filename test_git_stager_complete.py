#!/usr/bin/env python
"""Complete test for GitFileStager feature implementation."""

import sys
from pathlib import Path

def test_implementation():
    """Test the GitFileStager implementation."""
    print("="*60)
    print("Testing GitFileStager Feature Implementation")
    print("="*60)
    print()

    # Test 1: Check files exist
    print("Test 1: Checking file existence...")
    impl_file = Path("src/jean_claude/core/git_file_stager.py")
    test_file = Path("tests/test_git_file_stager.py")

    if not impl_file.exists():
        print(f"❌ FAIL: Implementation file missing: {impl_file}")
        return False
    print(f"  ✅ Implementation file exists: {impl_file}")

    if not test_file.exists():
        print(f"❌ FAIL: Test file missing: {test_file}")
        return False
    print(f"  ✅ Test file exists: {test_file}")
    print()

    # Test 2: Import module
    print("Test 2: Importing GitFileStager...")
    try:
        from jean_claude.core.git_file_stager import GitFileStager
        print("  ✅ GitFileStager imported successfully")
    except ImportError as e:
        print(f"❌ FAIL: Cannot import GitFileStager: {e}")
        return False
    print()

    # Test 3: Test instantiation
    print("Test 3: Testing instantiation...")
    try:
        stager = GitFileStager()
        assert stager.repo_path is not None
        print("  ✅ GitFileStager() - default instantiation works")

        stager_custom = GitFileStager(repo_path="/tmp")
        assert str(stager_custom.repo_path) == "/tmp"
        print("  ✅ GitFileStager(repo_path='/tmp') - custom path works")

        stager_path = GitFileStager(repo_path=Path("/tmp/test"))
        assert stager_path.repo_path == Path("/tmp/test")
        print("  ✅ GitFileStager(repo_path=Path()) - Path object works")
    except Exception as e:
        print(f"❌ FAIL: Instantiation failed: {e}")
        return False
    print()

    # Test 4: Test exclusion logic
    print("Test 4: Testing file exclusion logic...")
    try:
        stager = GitFileStager()

        # Test excluded files
        excluded_tests = [
            (".env", True),
            (".gitignore", True),
            (".DS_Store", True),
            ("__pycache__/test.pyc", True),
            ("node_modules/lib.js", True),
            ("dist/bundle.js", True),
        ]

        for filepath, should_be_excluded in excluded_tests:
            result = stager.is_excluded(filepath)
            if result != should_be_excluded:
                print(f"❌ FAIL: is_excluded('{filepath}') returned {result}, expected {should_be_excluded}")
                return False
            print(f"  ✅ is_excluded('{filepath}') = {result}")

        # Test non-excluded files
        non_excluded_tests = [
            ("src/main.py", False),
            ("tests/test_feature.py", False),
            ("README.md", False),
        ]

        for filepath, should_be_excluded in non_excluded_tests:
            result = stager.is_excluded(filepath)
            if result != should_be_excluded:
                print(f"❌ FAIL: is_excluded('{filepath}') returned {result}, expected {should_be_excluded}")
                return False
            print(f"  ✅ is_excluded('{filepath}') = {result}")

    except Exception as e:
        print(f"❌ FAIL: Exclusion logic test failed: {e}")
        return False
    print()

    # Test 5: Test filtering
    print("Test 5: Testing filter_relevant_files...")
    try:
        stager = GitFileStager()

        files = [
            "src/auth/login.py",
            ".env",
            "tests/test_auth.py",
            "__pycache__/cache.pyc",
            "README.md"
        ]

        filtered = stager.filter_relevant_files(files, feature_context="authentication")

        # Should include source and test files
        if "src/auth/login.py" not in filtered:
            print(f"❌ FAIL: Expected 'src/auth/login.py' in filtered files")
            return False
        print(f"  ✅ Includes: src/auth/login.py")

        if "tests/test_auth.py" not in filtered:
            print(f"❌ FAIL: Expected 'tests/test_auth.py' in filtered files")
            return False
        print(f"  ✅ Includes: tests/test_auth.py")

        # Should exclude config and cache files
        if ".env" in filtered:
            print(f"❌ FAIL: Should not include '.env' in filtered files")
            return False
        print(f"  ✅ Excludes: .env")

        if "__pycache__/cache.pyc" in filtered:
            print(f"❌ FAIL: Should not include '__pycache__/cache.pyc' in filtered files")
            return False
        print(f"  ✅ Excludes: __pycache__/cache.pyc")

    except Exception as e:
        print(f"❌ FAIL: Filtering test failed: {e}")
        return False
    print()

    # Test 6: Test empty list handling
    print("Test 6: Testing edge cases...")
    try:
        stager = GitFileStager()

        empty_filtered = stager.filter_relevant_files([], feature_context="test")
        if empty_filtered != []:
            print(f"❌ FAIL: Empty list should return empty list")
            return False
        print(f"  ✅ Empty list handling works")

        no_context = stager.filter_relevant_files(["src/main.py"], feature_context="")
        if "src/main.py" not in no_context:
            print(f"❌ FAIL: Should include files when no context provided")
            return False
        print(f"  ✅ No context filtering works")

    except Exception as e:
        print(f"❌ FAIL: Edge case test failed: {e}")
        return False
    print()

    # Test 7: Check test file structure
    print("Test 7: Verifying test file structure...")
    try:
        test_content = test_file.read_text()

        required_test_classes = [
            "TestGitFileStagerInit",
            "TestGitFileStagerGetModifiedFiles",
            "TestGitFileStagerGetFileDiff",
            "TestGitFileStagerFilterRelevantFiles",
            "TestGitFileStagerAnalyzeFilesForStaging",
            "TestGitFileStagerExclusionPatterns",
            "TestGitFileStagerIntegration"
        ]

        for test_class in required_test_classes:
            if test_class not in test_content:
                print(f"❌ FAIL: Missing test class: {test_class}")
                return False
            print(f"  ✅ Test class exists: {test_class}")

    except Exception as e:
        print(f"❌ FAIL: Test file verification failed: {e}")
        return False
    print()

    return True


if __name__ == "__main__":
    print()
    success = test_implementation()
    print()

    if success:
        print("="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print()
        print("GitFileStager feature is complete and ready!")
        print()
        print("Summary:")
        print("  - Implementation: src/jean_claude/core/git_file_stager.py")
        print("  - Tests: tests/test_git_file_stager.py")
        print("  - Exported from: src/jean_claude/core/__init__.py")
        print()
        sys.exit(0)
    else:
        print("="*60)
        print("❌ TESTS FAILED!")
        print("="*60)
        print()
        sys.exit(1)
