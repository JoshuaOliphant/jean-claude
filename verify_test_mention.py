#!/usr/bin/env python
"""Manually verify test mention detection works correctly."""

from jean_claude.core.beads import BeadsTask, BeadsTaskStatus
from jean_claude.core.task_validator import TaskValidator

def test_case(description, expected_warning, test_name):
    """Test a single case."""
    validator = TaskValidator(min_description_length=10)
    task = BeadsTask(
        id="test-1",
        title="Test Task",
        description=description,
        acceptance_criteria=["Criterion 1"],
        status=BeadsTaskStatus.OPEN
    )

    result = validator.validate(task)
    test_warnings = [w for w in result.warnings if "testing or verification" in w.lower()]
    has_warning = len(test_warnings) > 0

    if has_warning == expected_warning:
        print(f"✓ {test_name}")
        return True
    else:
        print(f"✗ {test_name}")
        print(f"  Expected warning: {expected_warning}, Got warning: {has_warning}")
        print(f"  Warnings: {test_warnings}")
        return False

print("Testing test mention detection:")
print("-" * 50)

tests_passed = 0
tests_total = 0

# Test basic keywords
tests_total += 1
if test_case("We need to test this feature", False, "Basic 'test' keyword"):
    tests_passed += 1

tests_total += 1
if test_case("Requires thorough testing", False, "Basic 'testing' keyword"):
    tests_passed += 1

tests_total += 1
if test_case("Verify the implementation", False, "Basic 'verify' keyword"):
    tests_passed += 1

tests_total += 1
if test_case("Add validation logic", False, "Basic 'validation' keyword"):
    tests_passed += 1

# Test false positives (should have warnings)
tests_total += 1
if test_case("Create a contest page", True, "False positive: 'contest'"):
    tests_passed += 1

tests_total += 1
if test_case("Users can attest to authenticity", True, "False positive: 'attest'"):
    tests_passed += 1

tests_total += 1
if test_case("Upgrade to the latest version", True, "False positive: 'latest'"):
    tests_passed += 1

tests_total += 1
if test_case("Implement greatest common divisor", True, "False positive: 'greatest'"):
    tests_passed += 1

# Test additional keywords
tests_total += 1
if test_case("Add unit tests for the feature", False, "Phrase: 'unit tests'"):
    tests_passed += 1

tests_total += 1
if test_case("Ready for QA review", False, "Keyword: 'QA'"):
    tests_passed += 1

tests_total += 1
if test_case("Check that all works", False, "Keyword: 'check'"):
    tests_passed += 1

tests_total += 1
if test_case("Ensure requirements are met", False, "Keyword: 'ensure'"):
    tests_passed += 1

# Test word variations
tests_total += 1
if test_case("All tests should pass", False, "Plural: 'tests'"):
    tests_passed += 1

tests_total += 1
if test_case("Should be tested thoroughly", False, "Past tense: 'tested'"):
    tests_passed += 1

tests_total += 1
if test_case("We are verifying functionality", False, "Present participle: 'verifying'"):
    tests_passed += 1

tests_total += 1
if test_case("System validates inputs", False, "Third person: 'validates'"):
    tests_passed += 1

# Test no mention
tests_total += 1
if test_case("Implement the feature", True, "No test mention"):
    tests_passed += 1

print("-" * 50)
print(f"Results: {tests_passed}/{tests_total} tests passed")

if tests_passed == tests_total:
    print("✓ All manual verification tests passed!")
    exit(0)
else:
    print(f"✗ {tests_total - tests_passed} tests failed")
    exit(1)
