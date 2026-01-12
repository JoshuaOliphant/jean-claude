# Test Suite Duplication - Executive Summary

**Quick Facts**:
- 119 test files, 1,284 test functions
- 1 duplicate test function (found in 2 files)
- 3 duplicate fixture definitions (appearing in 2+ conftest.py files)
- 7 test file groups with overlapping names (but mostly complementary functions)
- **Estimated removals**: 125-150 lines of code, 0-2 test files, 2-10 duplicate test functions

---

## Critical Findings

### 1. Duplicate Subprocess Fixtures (EASY FIX)
**Status**: Identical fixtures defined in both root and core conftest.py
**Files**:
- `tests/conftest.py` (lines 352-372)
- `tests/core/conftest.py` (lines 99-120)
**Fix**: Delete core version (22 lines), tests automatically inherit root version
**Effort**: 30 minutes
**Risk**: VERY LOW

### 2. Duplicate Test Function (EASY FIX)
**Status**: `test_function_signatures_are_compatible()` in 2 orchestration files
**Files**:
- `tests/orchestration/test_two_agent_execution.py`
- `tests/orchestration/test_auto_continue_execution.py`
**Fix**: Create single parameterized test
**Effort**: 1 hour
**Risk**: LOW

### 3. Duplicate Factory Fixtures (EASY FIX)
**Status**: Two factory fixtures with same purpose but different names
**Items**:
- `beads_task_factory` vs `mock_beads_task_factory`
- `workflow_state_factory` (defined in 2 conftest files)
**Fix**: Keep root versions, remove subdirectory duplicates
**Effort**: 1-2 hours
**Risk**: LOW-MEDIUM

---

## By the Numbers

| Category | Count | Confidence |
|----------|-------|------------|
| Duplicate Fixtures | 3 | HIGH |
| Duplicate Test Functions | 1 | HIGH |
| Test Files with Similar Names | 7 groups | HIGH |
| Safe Lines to Remove | 75-100 | HIGH |
| Estimated Test Impact | 2-10 tests affected | HIGH |

---

## Priority Fixes

### Phase 1 (1-2 hours) - No Test Changes Needed
1. Delete duplicate subprocess mocks from core/conftest.py (22 lines)
2. Delete duplicate beads_task_factory from core/conftest.py (28 lines)
3. **Result**: Cleaner fixture hierarchy, same test results

### Phase 2 (2-3 hours) - Standardize Naming
1. Rename `mock_beads_task_factory` → `beads_task_factory`
2. Consolidate factory fixture naming across conftest files
3. **Result**: Better fixture discoverability

### Phase 3 (1-2 hours) - Consolidate Tests
1. Create parameterized signature test for both orchestration modules
2. Remove duplicate signature tests
3. **Result**: Cleaner test organization

---

## Files to Review

### Consolidation Candidates (Remove)
- `tests/core/conftest.py` (lines 99-120) - duplicate subprocess mocks
- `tests/core/conftest.py` (lines 63-90) - duplicate beads_task_factory
- `tests/orchestration/test_two_agent_execution.py` - duplicate signature test
- `tests/orchestration/test_auto_continue_execution.py` - duplicate signature test

### Keep (Well-Organized)
- `test_two_agent.py` - functional tests
- `test_two_agent_imports.py` - import verification
- `test_auto_continue.py` - core logic
- `test_auto_continue_integration.py` - E2E workflows
- `test_auto_continue_notes.py` - note-taking features
- `test_workflow_utils*.py` - layered testing (functional, structural, edge cases)
- `test_dashboard*.py` - comprehensive + refactoring validation

---

## No Action Needed

These file groups are WELL-ORGANIZED with NO DUPLICATION:
- **Workflow Utils**: 3 files testing different aspects (function, structure, edge cases)
- **Two-Agent**: 3 files testing different concerns (functional, signatures, imports)
- **Auto-Continue**: 5 files with distinct purposes
- **Dashboard**: 2 files (comprehensive + refactoring specific)

---

## Next Steps

1. **This week**: Implement Phase 1 (remove obvious duplicates)
2. **Next week**: Implement Phase 2 (fixture naming standardization)
3. **Follow-up**: Document fixture organization in CLAUDE.md

**Total effort**: ~4-5 hours
**Expected impact**: Cleaner codebase, easier maintenance, no test coverage loss

---

## Contact

For detailed analysis, see: `/Users/joshuaoliphant/Library/CloudStorage/Dropbox/python_workspace/jean_claude/knowledge/capture/research/test-suite-duplication-analysis-2026-01-06.md`
