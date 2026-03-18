# ABOUTME: Analyzes per-test coverage contexts to find zero-unique and low-unique tests
# ABOUTME: Produces a coverage seed file ranking tests by their unique coverage contribution

"""Per-test coverage analyzer for autoloop test reduction.

Reads coverage.json with dynamic_context=test_function data and identifies:
- Zero-unique tests: every line they cover is also covered by another test (safe to delete)
- Low-unique tests: <10% of lines they cover are unique (likely safe)

Usage:
    uv run python auto/analyze_coverage.py /tmp/cov_contexts.json auto/coverage_seed.md
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def analyze(coverage_json_path: str, output_path: str) -> None:
    with open(coverage_json_path) as f:
        data = json.load(f)

    # Build mappings: which tests cover which lines, and which lines are covered by which tests
    test_lines: dict[str, set[tuple[str, int]]] = defaultdict(set)  # test -> set of (file, line)
    line_tests: dict[tuple[str, int], set[str]] = defaultdict(set)  # (file, line) -> set of tests

    for file_path, file_data in data.get("files", {}).items():
        contexts = file_data.get("contexts", {})
        for line_str, ctx_list in contexts.items():
            line_num = int(line_str)
            loc = (file_path, line_num)
            for ctx in ctx_list:
                if ctx and ctx != "":  # skip empty context (module-level)
                    test_lines[ctx].add(loc)
                    line_tests[loc].add(ctx)

    # Calculate unique coverage per test
    results = []
    for test, lines in test_lines.items():
        total = len(lines)
        unique = sum(1 for loc in lines if len(line_tests[loc]) == 1)
        pct = (unique / total * 100) if total > 0 else 0
        results.append((test, total, unique, pct))

    # Sort: zero-unique first, then by unique percentage ascending
    results.sort(key=lambda r: (r[2], r[3]))

    zero_unique = [r for r in results if r[2] == 0]
    low_unique = [r for r in results if 0 < r[3] < 10]

    # Write seed file
    with open(output_path, "w") as f:
        f.write("# Coverage Seed\n\n")
        f.write(f"Total tests analyzed: {len(results)}\n")
        f.write(f"Zero-unique tests (safe to delete): {len(zero_unique)}\n")
        f.write(f"Low-unique tests (<10%): {len(low_unique)}\n\n")

        f.write("## Zero-Unique Tests\n\n")
        f.write("Every line these tests cover is also covered by at least one other test.\n")
        f.write("Deleting these will NOT change coverage.\n\n")
        f.write("| Test | Lines Covered | Unique Lines |\n")
        f.write("|------|--------------|-------------|\n")
        for test, total, unique, pct in zero_unique:
            f.write(f"| `{test}` | {total} | {unique} |\n")

        f.write(f"\n## Low-Unique Tests (<10% unique)\n\n")
        f.write("| Test | Lines Covered | Unique Lines | Unique % |\n")
        f.write("|------|--------------|-------------|----------|\n")
        for test, total, unique, pct in low_unique:
            f.write(f"| `{test}` | {total} | {unique} | {pct:.1f}% |\n")

        # Module priority table
        f.write("\n## Module Priority\n\n")
        f.write("Files with the most zero-unique test coverage (best consolidation targets):\n\n")
        module_zeros: dict[str, int] = defaultdict(int)
        for test, total, unique, pct in zero_unique:
            # Extract test file from test name
            parts = test.split("::")
            if parts:
                module_zeros[parts[0]] += 1

        sorted_modules = sorted(module_zeros.items(), key=lambda x: -x[1])
        f.write("| Test File | Zero-Unique Tests |\n")
        f.write("|-----------|------------------|\n")
        for mod, count in sorted_modules[:20]:
            f.write(f"| `{mod}` | {count} |\n")

    print(f"Coverage seed written to {output_path}")
    print(f"  Zero-unique: {len(zero_unique)} tests (safe to delete)")
    print(f"  Low-unique:  {len(low_unique)} tests (likely safe)")
    print(f"  Total:       {len(results)} tests analyzed")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <coverage.json> <output.md>")
        sys.exit(1)
    analyze(sys.argv[1], sys.argv[2])
