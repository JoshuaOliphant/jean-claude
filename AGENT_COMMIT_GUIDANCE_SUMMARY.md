# Agent Commit Guidance Feature - Implementation Summary

## Feature: agent-prompt-commit-guidance (Feature 9/10)

### Status: ✅ COMPLETED

### Overview
Implemented an agent prompt template system that provides comprehensive guidance to agents on when and how to create commits following the Beads workflow and Conventional Commits specification.

### Components Implemented

#### 1. AgentCommitGuidance Class
**Location:** `src/jean_claude/core/agent_commit_guidance.py`

**Purpose:** Generates markdown-formatted guidance for agents on commit workflow

**Key Features:**
- When to commit (feature complete + tests pass)
- How to determine commit type (feat, fix, refactor, test, docs)
- How to determine commit scope from feature context
- What files to include/exclude in commits
- Commit body formatting (bulleted list of key changes)
- Git trailer format for Beads metadata
- Complete workflow steps
- Good and bad commit examples
- Context-aware guidance generation

#### 2. Test Suite
**Location:** `tests/test_agent_prompt_commit_guidance.py`

**Coverage:** 20+ test cases covering:
- When to commit guidance
- Commit type determination
- Commit scope determination
- File inclusion rules
- Commit message examples (good and bad)
- Beads metadata inclusion
- Feature number tracking
- Test validation requirements
- Commit workflow steps
- Markdown formatting
- Context customization
- Conventional Commits specification reference
- Git trailer format
- Scope extraction logic

### Guidance Sections Generated

1. **When to Commit**
   - Feature complete check
   - Tests passing requirement
   - No uncommitted changes
   - Warnings against committing on failure

2. **Commit Type Determination**
   - feat: New features
   - fix: Bug fixes
   - refactor: Code restructuring
   - test: Test additions
   - docs: Documentation changes

3. **Commit Scope Determination**
   - Extract from feature name/description
   - Use kebab-case
   - Keep concise and meaningful
   - Examples provided

4. **File Inclusion Guidance**
   - Include: Implementation, tests, related config, docs
   - Exclude: Unrelated changes, personal config, secrets, build artifacts
   - Use specific `git add` commands

5. **Commit Body Format**
   - Bulleted list (2-5 key changes)
   - Focus on WHAT and WHY, not HOW
   - List new files, modified functions, added dependencies

6. **Git Trailers**
   - Beads-Task-Id: <task_id>
   - Feature-Number: <number>
   - Proper format and capitalization

7. **Workflow Steps**
   - 7-step process from validation to verification
   - Error handling guidance
   - Don't proceed on failures

8. **Examples**
   - Good examples: Complete messages with all components
   - Bad examples: What to avoid with explanations

### Context-Aware Guidance

The guidance can be customized with feature context:

```python
guidance = AgentCommitGuidance()
context = {
    "feature_name": "add-authentication",
    "feature_description": "Implement JWT authentication",
    "beads_task_id": "test-123.1",
    "feature_number": 1,
    "total_features": 5
}
prompt = guidance.generate_guidance(context=context)
```

### Integration Points

This guidance can be integrated into:
1. Auto-continue workflow prompts
2. Agent system prompts
3. Feature implementation templates
4. Commit workflow orchestration

### Example Output Format

```
# Agent Commit Guidance

## When to Commit
Create a commit ONLY when ALL of the following conditions are met:
1. Feature is complete
2. Tests pass
3. No uncommitted changes remain

## Determining Commit Type
- feat: New feature or functionality
- fix: Bug fix or error correction
...

## Good Commit Examples

feat(auth): add JWT authentication

- Implement JWT token generation and validation
- Add password hashing with bcrypt
- Create login and logout endpoints

Beads-Task-Id: jean_claude-2sz.8
Feature-Number: 1
```

### Verification

- ✅ All test cases pass (20+ tests)
- ✅ Guidance includes all required sections
- ✅ Markdown formatting is correct
- ✅ Examples are comprehensive
- ✅ Context customization works
- ✅ Conventional Commits spec followed

### Files Created/Modified

**Created:**
- `src/jean_claude/core/agent_commit_guidance.py` - Main implementation
- `tests/test_agent_prompt_commit_guidance.py` - Test suite
- `verify_agent_commit_guidance.py` - Verification script
- `test_agent_guidance_manual.py` - Manual testing script
- `inspect_guidance_output.py` - Output inspection tool

**Modified:**
- `agents/beads-jean_claude-2sz.8/state.json` - Updated feature status

### Next Steps

The next feature (10/10) is:
- **commit-error-handling**: Implement comprehensive error handling for commit failures

### Notes

This implementation provides agents with clear, structured guidance on creating well-formatted commits that:
1. Follow Conventional Commits specification
2. Include Beads workflow metadata
3. Are created at the right time (after feature completion + test validation)
4. Contain meaningful context in the body
5. Use proper git trailer format

The guidance is designed to be included in agent prompts to ensure consistent, high-quality commits throughout the Beads workflow.
