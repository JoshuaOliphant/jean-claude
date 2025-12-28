# Cleanup Jean Claude Temporary Files

Clean up temporary verification scripts, status reports, and agent work directories.

## Instructions

1. Check for the existence of `.jc/` directory
2. Clean up temporary files based on user preferences
3. Report what was cleaned

## Implementation

```bash
# Run the cleanup command
jc cleanup --dry-run

# Show user what will be deleted and ask for confirmation
# Then run actual cleanup
jc cleanup

# For more aggressive cleanup (including agent directories)
jc cleanup --agents --all
```

## Cleanup Targets

The following directories contain temporary files:
- `.jc/temp/` - Temporary check/demo scripts (check_*.py, demo_*.py, verify_*.py)
- `.jc/reports/` - Status and verification reports (*_COMPLETE.md, *_VERIFICATION.md)
- `.jc/verification/` - Test outputs and logs
- `agents/` - Old agent work directories (optional with --agents flag)

## Options

- `--age N` - Remove files older than N days (default: 7)
- `--all` - Remove all temporary files regardless of age
- `--agents` - Also clean up old agent work directories
- `--dry-run` - Show what would be deleted without actually deleting

## Report

Display:
- Number of files that will be/were deleted
- Total size of files
- Breakdown by directory
