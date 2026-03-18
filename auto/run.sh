#!/usr/bin/env bash
# ABOUTME: Autoloop runner — tiered quality gates + structured METRIC output
# ABOUTME: Measures test count and coverage for test consolidation optimization
# This script is IMMUTABLE. The agent must never modify it.
# Exit code 0 = all gates passed, non-zero = broken (agent should revert)
set -euo pipefail

cd "$(dirname "$0")/.."

# ── Gate 1: All tests pass ────────────────────────────────────────
echo "=== Gate 1: Tests ==="
uv run pytest -n 4 --tb=short -q > run_tests.log 2>&1
TEST_EXIT=$?
if [ $TEST_EXIT -ne 0 ]; then
    echo "FAIL: Tests failed (exit $TEST_EXIT)"
    cat run_tests.log
    exit 1
fi

# Extract test count from pytest output (e.g. "1467 passed")
TEST_COUNT=$(grep -oE '[0-9]+ passed' run_tests.log | grep -oE '[0-9]+')
SKIP_COUNT=$(grep -oE '[0-9]+ skipped' run_tests.log | grep -oE '[0-9]+' || echo "0")
echo "Tests: ${TEST_COUNT} passed, ${SKIP_COUNT} skipped"

# ── Gate 2: Coverage check ────────────────────────────────────────
echo ""
echo "=== Gate 2: Coverage ==="
uv run pytest -n 4 --cov=jean_claude --cov-report=term -q > run_cov.log 2>&1
COV_EXIT=$?
if [ $COV_EXIT -ne 0 ]; then
    echo "FAIL: Coverage run failed (exit $COV_EXIT)"
    cat run_cov.log
    exit 1
fi

# Extract total coverage percentage (last TOTAL line)
COVERAGE=$(grep '^TOTAL' run_cov.log | awk '{print $NF}' | tr -d '%')
echo "Coverage: ${COVERAGE}%"

# Hard floor: coverage must not drop below 72%
if [ "$COVERAGE" -lt 72 ]; then
    echo "FAIL: Coverage dropped below 72% floor (got ${COVERAGE}%)"
    exit 1
fi

# ── Structured METRIC output ────────────────────────────────────────
echo ""
echo "METRIC test_count=${TEST_COUNT}"
echo "METRIC coverage_pct=${COVERAGE}"
echo "METRIC skip_count=${SKIP_COUNT}"
