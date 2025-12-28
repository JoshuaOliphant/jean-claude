# BeadsConfig Model Addition

## Summary

Added `BeadsConfig` model to complement the existing `BeadsTask` model in the Beads integration module.

## Changes Made

### 1. Added BeadsConfig Model (`src/jean_claude/core/beads.py`)

```python
class BeadsConfig(BaseModel):
    """Configuration model for Beads integration.

    Attributes:
        cli_path: Path to the beads CLI executable (defaults to "bd")
        config_options: Dictionary of configuration options for beads CLI
    """

    cli_path: str = Field(default="bd", description="Path to the beads CLI executable")
    config_options: dict = Field(default_factory=dict, description="Configuration options for beads CLI")
```

**Features:**
- Default CLI path of "bd"
- Configurable options dictionary for extensibility
- Validation for empty cli_path
- `from_dict()` and `to_dict()` methods for serialization

### 2. Created Comprehensive Tests (`tests/core/test_beads_data_model.py`)

Created new test file with:
- **TestBeadsTaskModel**: 14 tests covering BeadsTask functionality
- **TestBeadsConfigModel**: 16 tests covering BeadsConfig functionality
- **TestBeadsTaskAndConfigIntegration**: 2 integration tests

**Test Coverage:**
- Model creation with required and optional fields
- Validation (empty fields, whitespace, missing fields)
- Serialization (`to_dict()` and `from_dict()`)
- Roundtrip conversions
- Special characters preservation
- Nested configuration options
- Status enum values
- Integration between models

### 3. Updated Exports (`src/jean_claude/core/__init__.py`)

Added to module exports:
- `BeadsConfig`
- `BeadsTaskStatus`

## Models Overview

### BeadsTask
- **Purpose**: Represents a Beads task
- **Fields**: id, title, description, status, acceptance_criteria, created_at, updated_at
- **Already existed**: Yes (from beads-task-model feature)

### BeadsConfig
- **Purpose**: Stores configuration for Beads CLI integration
- **Fields**: cli_path, config_options
- **Added in this session**: Yes

## Test File

Location: `tests/core/test_beads_data_model.py`
- 32 total test cases
- Covers both BeadsTask and BeadsConfig models
- Tests validation, serialization, and integration

## Implementation Status

✅ BeadsConfig model implemented
✅ Comprehensive tests created
✅ Models exported in __init__.py
✅ Validation added for required fields
✅ Documentation added

## Notes

- BeadsConfig complements BeadsTask by providing configuration settings
- Both models use Pydantic for validation and serialization
- BeadsConfig supports flexible configuration options via dictionary
- Default CLI path is "bd" (the Beads CLI command)
