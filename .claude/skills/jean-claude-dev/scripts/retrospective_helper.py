#!/usr/bin/env python3
"""
Retrospective Helper Script

Analyzes recent git commits to help with retrospective reflection.
Identifies patterns, changes, and areas of focus to inform skill updates.
"""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_recent_commits(days: int = 7) -> list[dict]:
    """Get commits from the last N days."""
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    result = subprocess.run(
        [
            'git', 'log',
            f'--since={since_date}',
            '--pretty=format:%H|%s|%an|%ad',
            '--date=short'
        ],
        capture_output=True,
        text=True,
        check=True
    )

    commits = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        hash_val, subject, author, date = line.split('|', 3)
        commits.append({
            'hash': hash_val,
            'subject': subject,
            'author': author,
            'date': date
        })

    return commits


def get_commit_stats(commit_hash: str) -> dict:
    """Get file change statistics for a commit."""
    result = subprocess.run(
        ['git', 'show', '--stat', '--format=', commit_hash],
        capture_output=True,
        text=True,
        check=True
    )

    files_changed = []
    for line in result.stdout.strip().split('\n'):
        if '|' in line:
            filename = line.split('|')[0].strip()
            files_changed.append(filename)

    return {
        'files_changed': files_changed,
        'total_files': len(files_changed)
    }


def categorize_changes(files: list[str]) -> dict:
    """Categorize file changes by area."""
    categories = {
        'tests': [],
        'core': [],
        'cli': [],
        'orchestration': [],
        'tools': [],
        'docs': [],
        'config': [],
        'other': []
    }

    for file in files:
        if file.startswith('tests/'):
            categories['tests'].append(file)
        elif file.startswith('src/jean_claude/core/'):
            categories['core'].append(file)
        elif file.startswith('src/jean_claude/cli/'):
            categories['cli'].append(file)
        elif file.startswith('src/jean_claude/orchestration/'):
            categories['orchestration'].append(file)
        elif file.startswith('src/jean_claude/tools/'):
            categories['tools'].append(file)
        elif file.startswith('docs/') or file.endswith('.md'):
            categories['docs'].append(file)
        elif file.endswith(('.yaml', '.yml', '.toml', '.ini')):
            categories['config'].append(file)
        else:
            categories['other'].append(file)

    return {k: v for k, v in categories.items() if v}


def analyze_work_patterns(commits: list[dict]) -> dict:
    """Analyze patterns in recent work."""
    all_files = []
    commit_types = {
        'feat': 0,
        'fix': 0,
        'test': 0,
        'refactor': 0,
        'docs': 0,
        'chore': 0,
        'other': 0
    }

    for commit in commits:
        stats = get_commit_stats(commit['hash'])
        all_files.extend(stats['files_changed'])

        # Categorize commit type
        subject = commit['subject'].lower()
        if subject.startswith('feat'):
            commit_types['feat'] += 1
        elif subject.startswith('fix'):
            commit_types['fix'] += 1
        elif subject.startswith('test'):
            commit_types['test'] += 1
        elif subject.startswith('refactor'):
            commit_types['refactor'] += 1
        elif subject.startswith('docs'):
            commit_types['docs'] += 1
        elif subject.startswith('chore'):
            commit_types['chore'] += 1
        else:
            commit_types['other'] += 1

    categories = categorize_changes(all_files)

    return {
        'total_commits': len(commits),
        'commit_types': commit_types,
        'areas_of_focus': categories,
        'most_changed_files': get_most_changed_files(all_files)
    }


def get_most_changed_files(files: list[str], top_n: int = 5) -> list[tuple]:
    """Get the most frequently changed files."""
    from collections import Counter
    counter = Counter(files)
    return counter.most_common(top_n)


def generate_retrospective_template(analysis: dict, commits: list[dict]) -> str:
    """Generate a retrospective template based on analysis."""
    date_str = datetime.now().strftime('%Y-%m-%d')

    # Find focus area
    focus_areas = analysis['areas_of_focus']
    primary_focus = max(focus_areas.items(), key=lambda x: len(x[1]))[0] if focus_areas else 'general'

    template = f"""# Retrospective: {date_str}

## Work Summary

**Period**: Last 7 days
**Total Commits**: {analysis['total_commits']}
**Primary Focus**: {primary_focus.title()} development

### Commit Breakdown
"""

    for commit_type, count in analysis['commit_types'].items():
        if count > 0:
            template += f"- {commit_type.title()}: {count}\n"

    template += "\n### Areas Modified\n"
    for area, files in focus_areas.items():
        template += f"- {area.title()}: {len(files)} files\n"

    template += "\n### Most Changed Files\n"
    for file, count in analysis['most_changed_files']:
        template += f"- `{file}` ({count} changes)\n"

    template += """
## Key Learnings

[TODO: What did you learn during this work?]

### Technical Insights
- [TODO: What technical patterns or approaches did you discover?]
- [TODO: What worked well?]
- [TODO: What didn't work as expected?]

### Testing Insights
- [TODO: What testing patterns proved useful?]
- [TODO: Any testing challenges encountered?]

## Patterns Discovered

[TODO: Describe any reusable patterns or approaches]

### Code Pattern Example
```python
# TODO: Add example of useful pattern discovered
```

## Common Pitfalls Encountered

[TODO: What mistakes were made and how were they resolved?]

## Skill Updates Suggested

Based on this work, consider updating:

- [ ] **SKILL.md**: [TODO: What sections need updates?]
- [ ] **Testing Patterns**: [TODO: New patterns to document?]
- [ ] **Common Pitfalls**: [TODO: New pitfalls to add?]
- [ ] **Active Experiments**: [TODO: Update experiment status?]

## Future Considerations

[TODO: What should be explored or improved in future work?]

---

*Generated by retrospective_helper.py on {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    return template


def main():
    """Main entry point."""
    print("🔍 Analyzing recent development work...\n")

    # Get recent commits
    try:
        commits = get_recent_commits(days=7)
    except subprocess.CalledProcessError as e:
        print(f"Error getting git commits: {e}")
        sys.exit(1)

    if not commits:
        print("No commits found in the last 7 days.")
        return

    print(f"Found {len(commits)} commits\n")

    # Analyze patterns
    analysis = analyze_work_patterns(commits)

    print("📊 Work Summary:")
    print(f"  Total commits: {analysis['total_commits']}")
    print(f"\n  Commit types:")
    for commit_type, count in analysis['commit_types'].items():
        if count > 0:
            print(f"    - {commit_type}: {count}")

    print(f"\n  Areas of focus:")
    for area, files in analysis['areas_of_focus'].items():
        print(f"    - {area}: {len(files)} files")

    print(f"\n  Most changed files:")
    for file, count in analysis['most_changed_files']:
        print(f"    - {file} ({count} changes)")

    # Generate template
    template = generate_retrospective_template(analysis, commits)

    # Save to file
    date_str = datetime.now().strftime('%Y-%m-%d')
    skill_dir = Path(__file__).parent.parent
    retro_dir = skill_dir / 'references' / 'retrospectives'
    retro_file = retro_dir / f'{date_str}-session.md'

    with open(retro_file, 'w') as f:
        f.write(template)

    print(f"\n✅ Retrospective template created: {retro_file}")
    print("\nNext steps:")
    print("1. Edit the template to add your learnings and insights")
    print("2. Review suggested skill updates")
    print("3. Update SKILL.md as needed")
    print("4. Commit the retrospective file")


if __name__ == '__main__':
    main()
