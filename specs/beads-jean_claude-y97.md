# Extract duplicate mailbox validation and JSONL reading utilities

## Description

## Problem
Two patterns duplicated across multiple files:

### Pattern 1: Mailbox Validation (15+ lines in 2 files)
- message_reader.py:60-76
- message_writer.py:74-92

### Pattern 2: JSONL Reading (15+ lines in 3 files)
- status.py
- dashboard/app.py
- logs.py

## Files to Modify
### Create New File
- src/jean_claude/core/file_utils.py (NEW)

### Modify Existing Files
- src/jean_claude/core/message_reader.py
- src/jean_claude/core/message_writer.py
- src/jean_claude/cli/commands/status.py
- src/jean_claude/cli/commands/logs.py
- src/jean_claude/dashboard/app.py

## Implementation

### file_utils.py (NEW)
```python
# ABOUTME: File I/O utility functions
# ABOUTME: Shared functions for JSONL reading and path resolution

import json
from pathlib import Path
from typing import Any, Iterator

def read_jsonl_file(file_path: Path) -> Iterator[dict[str, Any]]:
    """Read JSONL file line by line, yielding parsed dictionaries.
    
    Skips invalid JSON lines silently.
    """
    if not file_path.exists():
        return
    
    try:
        with open(file_path) as f:
            for line in f:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except (OSError, IOError):
        return
```

### mailbox_storage.py (add utility)
```python
from jean_claude.core.message_writer import MessageBox
from jean_claude.core.mailbox_paths import MailboxPaths

def resolve_mailbox_path(mailbox: MessageBox, paths: MailboxPaths) -> Path:
    """Resolve MessageBox enum to file path.
    
    Raises:
        ValueError: If mailbox is invalid type or value
    """
    if not isinstance(mailbox, MessageBox):
        raise ValueError(
            f'mailbox must be a MessageBox enum value, got {type(mailbox).__name__}'
        )
    
    if mailbox == MessageBox.INBOX:
        return paths.inbox_path
    elif mailbox == MessageBox.OUTBOX:
        return paths.outbox_path
    else:
        raise ValueError(f'Invalid mailbox type: {mailbox}')
```

## Acceptance Criteria
- [ ] file_utils.py created with read_jsonl_file()
- [ ] Mailbox path resolution extracted
- [ ] All 5 files updated to use utilities
- [ ] ~75 lines of duplicate code removed
- [ ] Tests pass: uv run pytest -v
- [ ] Add tests/test_file_utils.py

## Test Requirements
Create tests/test_file_utils.py:
```python
def test_read_jsonl_file_valid_data(tmp_path):
def test_read_jsonl_file_skips_invalid_json(tmp_path):
def test_read_jsonl_file_missing_file(tmp_path):
def test_resolve_mailbox_path_inbox():
def test_resolve_mailbox_path_outbox():
def test_resolve_mailbox_path_invalid_type():
```

## Dependencies
None - can work in parallel

## Agent Notes
🟠 HIGH PRIORITY
📬 Message when extraction complete
🧪 Add comprehensive tests
✅ Break into features: 1) Create utils 2) Update readers 3) Update commands 4) Add tests
⚡ 75+ lines removed

## Time Estimate
Agent: ~2.5 hours

## Acceptance Criteria



---

## Task Metadata

- **Task ID**: jean_claude-y97
- **Status**: in_progress
- **Created**: 2025-12-28 17:15:51
- **Updated**: 2025-12-28 17:31:18
