#!/usr/bin/env python3
"""Quick import check for existing features."""

try:
    from jean_claude.core.commit_message_formatter import CommitMessageFormatter
    print("✅ CommitMessageFormatter imports successfully")

    from jean_claude.core.conventional_commit_parser import ConventionalCommitParser
    print("✅ ConventionalCommitParser imports successfully")

    from jean_claude.core.git_file_stager import GitFileStager
    print("✅ GitFileStager imports successfully")

    print("\n✅ All modules import successfully!")
    print("Ready to proceed with feature 4: test-runner-validator")

except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
