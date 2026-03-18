# Jean Claude Test Consolidation — Phase 3: Coverage-Guided Deletion

This experiment uses per-test coverage analysis to identify and delete tests with zero unique coverage contribution.

## Objective

Phase 1-2 reduced tests from 1467 to 1160 (-20.9%) using structural consolidation. Phase 3 uses **coverage data** to find the remaining waste: 767 tests (79% of analyzed) cover no lines exclusively. Deleting them is mathematically guaranteed not to change coverage.

The optimization target is test_count (lowest is better).
Coverage must never drop below 72% — hard floor.

## Metrics

- **Primary (optimization target)**: `test_count` (count, lowest is better)
- **Secondary (guardrail)**: `coverage_pct` (%, must stay ≥ 72 — hard floor)
- **Secondary (info)**: `skip_count`

## How to Run

Run `./auto/run.sh` — tests + coverage gate. Do NOT modify it.

## The Coverage Seed

Read `auto/coverage_seed.md` — it contains the pre-analyzed coverage data:
- **767 zero-unique tests**: every line they cover is also covered by another test. Safe to delete.
- **93 low-unique tests** (<10% unique lines): likely safe but verify.
- **Module priority table**: which test files have the most zero-unique tests.

**CRITICAL**: The seed goes stale as tests are deleted. Lines that were covered by 2+ tests become covered by 1 test (unique) after you delete the others. **Regenerate the seed every 30-50 deletions** by running:

```bash
cat > /tmp/.coveragerc_jc << 'EOF'
[run]
source = jean_claude
dynamic_context = test_function
data_file = /tmp/.coverage_jc_contexts
EOF
uv run coverage run --rcfile=/tmp/.coveragerc_jc -m pytest tests/ -q -p no:cov -n 0
uv run coverage json --rcfile=/tmp/.coveragerc_jc --show-contexts -o /tmp/cov_contexts.json
uv run python auto/analyze_coverage.py /tmp/cov_contexts.json auto/coverage_seed.md
```

This takes ~70 seconds. Worth it to avoid deleting tests that became uniquely important.

## Files in Scope

- `tests/**/*.py` — All test files (except conftest.py). You CAN delete functions and entire files.
- `auto/coverage_seed.md` — Read this for deletion targets. Regenerate periodically.

For context (read-only):
- `src/jean_claude/` — Source code being tested.

## Off Limits

- `src/**/*.py`, `tests/**/conftest.py`, `pyproject.toml`, `CLAUDE.md`
- `auto/run.sh`, `auto/analyze_coverage.py` — immutable pipeline
- `results.tsv` — append-only

## Setup

1. Create branch `autoloop/mar17c` from current HEAD.
2. Run `./auto/run.sh > run.log 2>&1` for baseline.
3. Record baseline in results.tsv.
4. Read `auto/coverage_seed.md` to understand targets.
5. Begin experiments.

## Experimentation

**What you CAN do:**
- **Delete zero-unique test functions** listed in `auto/coverage_seed.md`
- **Delete entire test files** if all their tests are zero-unique
- **Delete low-unique tests** (<10%) after confirming coverage holds
- **Regenerate the seed** after every 30-50 deletions

**What you CANNOT do:**
- Modify source files, conftest files, or the runner
- Delete tests NOT listed in the coverage seed (they may be uniquely important)
- Skip seed regeneration after large batches of deletions

**Strategy per experiment:**
1. Read coverage_seed.md, pick a test file from the Module Priority table
2. Delete ALL zero-unique tests from that file
3. If the file becomes empty, delete the file
4. git commit, run `./auto/run.sh`, check results
5. If kept, move to next file. After ~30-50 deletions, regenerate seed.

**Resource constraints**: ~60s per experiment. Seed regeneration: ~70s.

**The first run**: Establish baseline without modifications.

## Output format

```bash
./auto/run.sh > run.log 2>&1
grep '^METRIC ' run.log
```

## Logging results

Tab-separated `results.tsv`:
```
commit	test_count	coverage_pct	status	description
```

## The experiment loop

LOOP FOREVER:

1. Read `results.tsv`, Progress Log, and `auto/coverage_seed.md`.
2. State what you learned from past attempts.
3. Pick zero-unique tests from the seed to delete.
4. git commit the deletion.
5. Run: `./auto/run.sh > run.log 2>&1`
6. Extract: `grep '^METRIC ' run.log`
7. If test_count improved AND coverage ≥ 72%, KEEP. Update Progress Log.
8. If coverage dropped, REVERT with `git reset --hard HEAD~1`. This means the seed was stale — regenerate it.
9. **Every 30-50 deletions**: regenerate the coverage seed.

## Baseline

- **Commit**: (establish from first run)
- **test_count**: ~1160 (from Phase 2)
- **coverage_pct**: 72%

## Progress Log

(no experiments yet — Phase 3)

## NEVER STOP

Continue autonomously until manually interrupted. If the seed runs dry (no zero-unique tests left), regenerate it. If regeneration still shows no targets, switch to low-unique tests. If those are exhausted, stop and report.
