# Add missing test coverage for orchestration modules

## Description

## Problem
Critical orchestration modules have incomplete test coverage:

### auto_continue.py (CRITICAL GAP)
- Only ~150 lines of tests for ~300 line module
- Missing: Main loop logic, iteration limits, feature advancement, error recovery

### two_agent.py (PARTIAL)
- Only ~100 lines of tests for ~200 line module
- Missing: Error handling, feature extraction edge cases, model variations

## Files to Modify
1. tests/orchestration/test_auto_continue.py (add 100-150 lines)
2. tests/orchestration/test_two_agent.py (add 50-75 lines)

## Required Test Cases

### test_auto_continue.py - Add These Tests

```python
# Main Loop Tests
def test_run_auto_continue_respects_max_iterations(sample_workflow_state):
    """Verify loop stops at max_iterations."""

def test_run_auto_continue_advances_features(sample_workflow_state):
    """Verify features advance on completion."""

def test_run_auto_continue_stops_on_completion(sample_workflow_state):
    """Verify loop exits when all features done."""

# Error Recovery Tests
def test_run_auto_continue_handles_sdk_error(sample_workflow_state):
    """Verify SDK errors are caught and logged."""

def test_run_auto_continue_tracks_cost_on_error(sample_workflow_state):
    """Verify cost tracking continues after errors."""

# Feature Management Tests
def test_run_auto_continue_marks_feature_failed_on_error(sample_workflow_state):
    """Verify failed features marked correctly."""

def test_run_auto_continue_continues_to_next_feature_after_failure(sample_workflow_state):
    """Verify workflow continues despite failures."""

# Signal Handling Tests  
def test_run_auto_continue_graceful_shutdown_on_keyboard_interrupt(sample_workflow_state):
    """Verify clean exit on Ctrl+C."""
```

### test_two_agent.py - Add These Tests

```python
# Error Handling Tests
def test_execute_two_agent_workflow_handles_invalid_json(tmp_path):
    """Verify graceful handling of malformed JSON in spec."""

def test_execute_two_agent_workflow_handles_malformed_yaml(tmp_path):
    """Verify error on invalid YAML frontmatter."""

def test_execute_two_agent_workflow_handles_missing_features_key(tmp_path):
    """Verify error when YAML missing 'features' key."""

# Model Variation Tests
def test_execute_two_agent_workflow_with_haiku_planner(tmp_path):
    """Verify workflow works with haiku as planner model."""

def test_execute_two_agent_workflow_with_opus_implementer(tmp_path):
    """Verify workflow works with opus as implementer."""

# Feature Extraction Tests
def test_extract_features_from_spec_handles_empty_list(tmp_path):
    """Verify empty features list handled correctly."""

def test_extract_features_from_spec_validates_required_fields(tmp_path):
    """Verify features must have name and description."""
```

## Acceptance Criteria
- [ ] test_auto_continue.py has 8+ new test cases
- [ ] test_two_agent.py has 5+ new test cases
- [ ] Main loop logic fully covered
- [ ] Error paths fully covered
- [ ] All tests pass: uv run pytest tests/orchestration/ -v
- [ ] Coverage increased to >85% for both modules

## Coverage Check
```bash
uv run pytest tests/orchestration/ --cov=src/jean_claude/orchestration --cov-report=term-missing
# Should show >85% coverage for auto_continue.py and two_agent.py
```

## Dependencies
None - can work in parallel

## Agent Notes
🟡 MEDIUM PRIORITY - Quality improvement
📬 Message with coverage % before and after
✅ Break into: 1) auto_continue tests 2) two_agent tests
🧪 Use existing fixtures from tests/orchestration/conftest.py
⚡ Focus on CRITICAL PATHS first (main loop, error handling)

## Time Estimate
Agent: ~4 hours

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-kl4
- **Status**: in_progress
- **Created**: 2025-12-28 17:17:42
- **Updated**: 2025-12-28 17:31:19
