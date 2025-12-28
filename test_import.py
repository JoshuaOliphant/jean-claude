#!/usr/bin/env python3
"""Quick test to verify CommitBodyGenerator works."""

try:
    from jean_claude.core.commit_body_generator import CommitBodyGenerator
    print("✓ Successfully imported CommitBodyGenerator")

    # Test instantiation
    generator = CommitBodyGenerator()
    print(f"✓ Successfully instantiated CommitBodyGenerator: {generator.repo_path}")

    # Test parse_diff
    diff = """diff --git a/src/test.py b/src/test.py
new file mode 100644
--- /dev/null
+++ b/src/test.py
@@ -0,0 +1,3 @@
+def hello():
+    pass
"""
    parsed = generator.parse_diff(diff)
    print(f"✓ Parse diff successful: new_files={parsed['new_files']}, added_functions={parsed['added_functions']}")

    bullets = generator.format_bullets(parsed)
    print(f"✓ Format bullets successful: {bullets}")

    print("\n✅ All imports and basic tests passed!")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
