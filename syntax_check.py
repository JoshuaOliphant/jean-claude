#!/usr/bin/env python
"""Check syntax of the new files."""

import ast
import sys

files_to_check = [
    "src/jean_claude/core/interactive_prompt_handler.py",
    "tests/test_interactive_prompt.py"
]

all_ok = True

for filepath in files_to_check:
    print(f"Checking {filepath}...")
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        ast.parse(code)
        print(f"  ✓ Syntax OK")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        all_ok = False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        all_ok = False

if all_ok:
    print("\n✓ All files have valid syntax!")
else:
    print("\n✗ Some files have syntax errors!")
    sys.exit(1)
