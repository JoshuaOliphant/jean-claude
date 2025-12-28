#!/usr/bin/env python3
"""Inspect the output of AgentCommitGuidance."""

from jean_claude.core.agent_commit_guidance import AgentCommitGuidance


def main():
    """Generate and display guidance output."""
    print("=" * 80)
    print("AgentCommitGuidance Output (First 2000 characters)")
    print("=" * 80)

    guidance = AgentCommitGuidance()
    prompt = guidance.generate_guidance()

    print(prompt[:2000])
    print("\n...")
    print(f"\nTotal length: {len(prompt)} characters")

    print("\n" + "=" * 80)
    print("Key checks:")
    print("=" * 80)

    checks = {
        "Has 'when to commit'": "when to commit" in prompt.lower(),
        "Has 'feature complete'": "feature complete" in prompt.lower(),
        "Has 'tests pass'": "tests pass" in prompt.lower(),
        "Has 'feat'": "feat" in prompt,
        "Has 'fix'": "fix" in prompt,
        "Has 'refactor'": "refactor" in prompt,
        "Has 'test'": "test" in prompt,
        "Has 'docs'": "docs" in prompt,
        "Has 'scope'": "scope" in prompt.lower(),
        "Has 'files'": "files" in prompt.lower(),
        "Has 'beads'": "beads" in prompt.lower(),
        "Has 'example'": "example" in prompt.lower(),
        "Has markdown headers": "#" in prompt,
        "Has lists": "-" in prompt or "*" in prompt,
        "Has code blocks": "```" in prompt,
    }

    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}: {result}")


if __name__ == "__main__":
    main()
