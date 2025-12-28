#!/usr/bin/env python3
"""Manually verify the beads_spec.md template meets all requirements."""

from pathlib import Path


def verify_template():
    """Verify the beads_spec.md template exists and is properly formatted."""

    # Get template path
    project_root = Path(__file__).parent
    template_path = project_root / "src" / "jean_claude" / "templates" / "beads_spec.md"

    print("=" * 60)
    print("VERIFYING BEADS_SPEC.MD TEMPLATE")
    print("=" * 60)

    # Check 1: File exists
    print("\n✓ CHECK 1: File exists")
    if not template_path.exists():
        print(f"  ❌ FAIL: Template file not found at {template_path}")
        return False
    print(f"  ✅ PASS: File exists at {template_path}")

    # Check 2: Read content
    print("\n✓ CHECK 2: File is readable")
    try:
        content = template_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ❌ FAIL: Could not read file: {e}")
        return False
    print(f"  ✅ PASS: File is readable as UTF-8")

    # Check 3: Not empty
    print("\n✓ CHECK 3: File is not empty")
    if not content.strip():
        print(f"  ❌ FAIL: Template file is empty")
        return False
    print(f"  ✅ PASS: File has content ({len(content)} characters)")

    # Check 4: Has markdown extension
    print("\n✓ CHECK 4: File has .md extension")
    if template_path.suffix != ".md":
        print(f"  ❌ FAIL: File extension is {template_path.suffix}, not .md")
        return False
    print(f"  ✅ PASS: File has .md extension")

    # Check 5: Has title section
    print("\n✓ CHECK 5: Has title section with placeholder")
    if "# " not in content:
        print(f"  ❌ FAIL: No markdown H1 header found")
        return False
    if "{{title}}" not in content:
        print(f"  ❌ FAIL: No {{title}} placeholder found")
        return False
    print(f"  ✅ PASS: Has title section with {{title}} placeholder")

    # Check 6: Has description section
    print("\n✓ CHECK 6: Has description section with placeholder")
    if "## Description" not in content:
        print(f"  ❌ FAIL: No '## Description' section found")
        return False
    if "{{description}}" not in content:
        print(f"  ❌ FAIL: No {{description}} placeholder found")
        return False
    print(f"  ✅ PASS: Has description section with {{description}} placeholder")

    # Check 7: Has acceptance criteria section
    print("\n✓ CHECK 7: Has acceptance criteria section with placeholder")
    if "## Acceptance Criteria" not in content:
        print(f"  ❌ FAIL: No '## Acceptance Criteria' section found")
        return False
    if "{{acceptance_criteria}}" not in content:
        print(f"  ❌ FAIL: No {{acceptance_criteria}} placeholder found")
        return False
    print(f"  ✅ PASS: Has acceptance criteria section with {{acceptance_criteria}} placeholder")

    # Check 8: Correct order
    print("\n✓ CHECK 8: Sections in correct order")
    title_pos = content.find("#")
    desc_pos = content.find("## Description")
    ac_pos = content.find("## Acceptance Criteria")

    if title_pos == -1 or desc_pos == -1 or ac_pos == -1:
        print(f"  ❌ FAIL: Missing required sections")
        return False

    if not (title_pos < desc_pos < ac_pos):
        print(f"  ❌ FAIL: Sections not in correct order")
        print(f"     Title at {title_pos}, Description at {desc_pos}, AC at {ac_pos}")
        return False
    print(f"  ✅ PASS: Sections in correct order (title → description → criteria)")

    # Check 9: Consistent placeholder style
    print("\n✓ CHECK 9: Uses Jinja2-style placeholders consistently")
    jinja2_count = content.count("{{") + content.count("}}")
    if jinja2_count < 6:  # Should have at least 3 placeholders (6 braces)
        print(f"  ❌ FAIL: Not enough Jinja2 placeholders found")
        return False
    print(f"  ✅ PASS: Uses Jinja2 {{}} style placeholders")

    # Check 10: Has empty lines for readability
    print("\n✓ CHECK 10: Has empty lines for readability")
    lines = content.split("\n")
    empty_lines = [line for line in lines if line.strip() == ""]
    if len(empty_lines) < 2:
        print(f"  ❌ FAIL: Not enough empty lines for readability")
        return False
    print(f"  ✅ PASS: Has {len(empty_lines)} empty lines for readability")

    # Print actual content
    print("\n" + "=" * 60)
    print("TEMPLATE CONTENT:")
    print("=" * 60)
    print(content)
    print("=" * 60)

    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    import sys
    success = verify_template()
    sys.exit(0 if success else 1)
