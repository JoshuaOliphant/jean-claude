#!/usr/bin/env python3
"""Verify CommitBodyGenerator implementation."""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from jean_claude.core.commit_body_generator import CommitBodyGenerator

def test_basic_functionality():
    """Test basic CommitBodyGenerator functionality."""
    print("Testing CommitBodyGenerator initialization...")

    # Test initialization
    generator = CommitBodyGenerator()
    assert generator.repo_path == Path.cwd()
    print("✓ Initialization works")

    # Test with custom path
    generator = CommitBodyGenerator(repo_path="/tmp/test")
    assert generator.repo_path == Path("/tmp/test")
    print("✓ Custom path works")

    # Test parse_diff with empty input
    parsed = generator.parse_diff("")
    assert parsed["new_files"] == []
    assert parsed["modified_files"] == []
    print("✓ Parse empty diff works")

    # Test parse_diff with new file
    diff = """diff --git a/src/feature.py b/src/feature.py
new file mode 100644
index 0000000..abcd123
--- /dev/null
+++ b/src/feature.py
@@ -0,0 +1,5 @@
+def new_function():
+    pass
"""
    parsed = generator.parse_diff(diff)
    assert "src/feature.py" in parsed["new_files"]
    assert "new_function" in parsed["added_functions"]
    print("✓ Parse new file works")

    # Test format_bullets
    bullets = generator.format_bullets(parsed)
    assert isinstance(bullets, list)
    assert len(bullets) > 0
    print("✓ Format bullets works")
    print(f"  Generated bullets: {bullets}")

    # Test with modified file
    diff2 = """diff --git a/src/main.py b/src/main.py
index 1234567..abcdefg 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,2 +1,4 @@
 import os
+import sys
+
+class NewClass:
+    pass
"""
    parsed2 = generator.parse_diff(diff2)
    assert "src/main.py" in parsed2["modified_files"]
    assert "NewClass" in parsed2["added_classes"]
    assert "sys" in parsed2["added_imports"]
    print("✓ Parse modified file works")

    bullets2 = generator.format_bullets(parsed2)
    assert len(bullets2) > 0
    print("✓ Format bullets for modified file works")
    print(f"  Generated bullets: {bullets2}")

    # Test with deleted file
    diff3 = """diff --git a/src/old.py b/src/old.py
deleted file mode 100644
index 1234567..0000000
"""
    parsed3 = generator.parse_diff(diff3)
    assert "src/old.py" in parsed3["deleted_files"]
    print("✓ Parse deleted file works")

    # Test with dependencies
    diff4 = """diff --git a/requirements.txt b/requirements.txt
index 1234567..abcdefg 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 requests==2.28.0
+fastapi==0.95.0
"""
    parsed4 = generator.parse_diff(diff4)
    assert "fastapi==0.95.0" in parsed4["added_dependencies"]
    print("✓ Parse dependencies works")

    print("\n✅ All basic functionality tests passed!")
    return True

def test_complex_diff():
    """Test with complex multi-file diff."""
    print("\nTesting complex multi-file diff...")

    generator = CommitBodyGenerator()

    diff = """diff --git a/src/auth/login.py b/src/auth/login.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/src/auth/login.py
@@ -0,0 +1,10 @@
+from typing import Optional
+import jwt
+
+class LoginHandler:
+    def authenticate(self, username: str, password: str) -> bool:
+        return True
+
+async def verify_token(token: str):
+    pass
diff --git a/requirements.txt b/requirements.txt
index 2222222..3333333 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
 requests==2.28.0
+pyjwt==2.6.0
diff --git a/tests/test_login.py b/tests/test_login.py
new file mode 100644
index 0000000..4444444
--- /dev/null
+++ b/tests/test_login.py
@@ -0,0 +1,8 @@
+def test_authenticate():
+    assert True
+
+def test_verify_token():
+    pass
"""

    parsed = generator.parse_diff(diff)

    assert "src/auth/login.py" in parsed["new_files"]
    assert "tests/test_login.py" in parsed["new_files"]
    assert "requirements.txt" in parsed["modified_files"]
    assert "LoginHandler" in parsed["added_classes"]
    assert "authenticate" in parsed["added_functions"]
    assert "verify_token" in parsed["added_functions"]
    assert "pyjwt==2.6.0" in parsed["added_dependencies"]
    assert "jwt" in parsed["added_imports"]

    print("✓ Complex diff parsing works")

    bullets = generator.format_bullets(parsed)
    assert len(bullets) > 0

    print("✓ Complex diff formatting works")
    print(f"  Generated {len(bullets)} bullets:")
    for bullet in bullets:
        print(f"    - {bullet}")

    print("\n✅ Complex diff test passed!")
    return True

if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_complex_diff()
        print("\n" + "="*60)
        print("✅ ALL VERIFICATION TESTS PASSED!")
        print("="*60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
