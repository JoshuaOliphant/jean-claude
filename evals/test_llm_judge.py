#!/usr/bin/env python3
# ABOUTME: Test script to verify LLMJudge is actually making API calls
# ABOUTME: Measures timing and prints detailed output

"""Test LLMJudge to verify it's actually calling the API."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

print("=" * 60)
print("LLMJudge API Call Verification")
print("=" * 60)

# Check API key
api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"\nAPI Key present: {bool(api_key)}")
if api_key:
    print(f"API Key prefix: {api_key[:12]}...")
else:
    print("ERROR: No ANTHROPIC_API_KEY found!")
    exit(1)

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import LLMJudge, IsInstance

# Create a simple test case
dataset = Dataset(
    cases=[
        Case(
            name='greeting_test',
            inputs='Say hello',
            expected_output='A friendly greeting',
        )
    ],
    evaluators=[
        IsInstance(type_name='str'),
        LLMJudge(
            rubric='The output is a friendly, polite greeting',
            model='anthropic:claude-sonnet-4-5',
            score={'include_reason': True},
            assertion={'include_reason': True},
        ),
    ],
)


def simple_task(inputs: str) -> str:
    """A simple task that returns a greeting."""
    return 'Hello there! How can I help you today?'


print("\n" + "-" * 60)
print("Running evaluation...")
print("-" * 60)

start = time.time()
report = dataset.evaluate_sync(simple_task)
elapsed = time.time() - start

print(f"\n⏱️  Total evaluation time: {elapsed:.2f} seconds")
print(f"   (If < 1 second, LLM was likely NOT called)")

print("\n" + "-" * 60)
print("Results")
print("-" * 60)

for case in report.cases:
    print(f"\nCase: {case.name}")
    print(f"  Output: {case.output}")
    print(f"  Scores: {case.scores}")
    print(f"  Assertions: {case.assertions}")

    # Try to get reasons if available
    if hasattr(case, 'score_reasons'):
        print(f"  Score Reasons: {case.score_reasons}")

print("\n" + "=" * 60)
if elapsed > 1.0:
    print("✅ LLM was likely called (took > 1 second)")
else:
    print("⚠️  WARNING: Evaluation was too fast - LLM may not have been called!")
print("=" * 60)
