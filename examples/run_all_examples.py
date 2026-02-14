#!/usr/bin/env python3
"""Run all Personaut PDK examples to verify everything works.

This script runs all offline examples and reports their status.
LLM examples are skipped unless API credentials are available.

Usage:
    python run_all_examples.py          # Run offline examples only
    python run_all_examples.py --all    # Run all including LLM examples
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


class ExampleResult(NamedTuple):
    name: str
    success: bool
    message: str


# Examples that don't require API credentials
OFFLINE_EXAMPLES = [
    "01_basic_individual.py",
    "02_emotions.py",
    "03_traits.py",
    "04_persona_prompts.py",
    "07_situations.py",
    "08_masks_and_triggers.py",
    "09_memory.py",
    "10_relationships.py",
    "11_facts.py",
    "12_states.py",
    "13_storage.py",
    "14_simulations.py",
]

# Examples that require API credentials
LLM_EXAMPLES = [
    "05_llm_generation.py",
]


def run_example(example_path: Path) -> ExampleResult:
    """Run a single example and return the result."""
    try:
        result = subprocess.run(
            [sys.executable, str(example_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=example_path.parent,
        )

        if result.returncode == 0:
            # Check for success marker in output
            if "✅" in result.stdout or "completed successfully" in result.stdout.lower():
                return ExampleResult(example_path.name, True, "Passed")
            else:
                return ExampleResult(example_path.name, True, "Completed")
        else:
            error_msg = result.stderr.strip().split('\n')[-1][:100] if result.stderr else "Unknown error"
            return ExampleResult(example_path.name, False, f"Failed: {error_msg}")

    except subprocess.TimeoutExpired:
        return ExampleResult(example_path.name, False, "Timeout (>60s)")
    except Exception as e:
        return ExampleResult(example_path.name, False, f"Error: {str(e)[:100]}")


def main() -> None:
    print("=" * 70)
    print("Personaut PDK - Example Runner")
    print("=" * 70)

    # Determine which examples to run
    run_all = "--all" in sys.argv

    # Check for API credentials
    has_api = bool(
        os.environ.get("GOOGLE_API_KEY") or
        (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))
    )

    # Collect examples to run
    examples_dir = Path(__file__).parent
    examples_to_run = []

    for example_name in OFFLINE_EXAMPLES:
        example_path = examples_dir / example_name
        if example_path.exists():
            examples_to_run.append(example_path)

    if run_all and has_api:
        for example_name in LLM_EXAMPLES:
            example_path = examples_dir / example_name
            if example_path.exists():
                examples_to_run.append(example_path)
    elif run_all and not has_api:
        print("\n⚠️  --all specified but no API credentials found.")
        print("   Skipping LLM examples.")

    print(f"\nRunning {len(examples_to_run)} examples...")
    if not run_all:
        print("(Use --all flag to include LLM examples)")
    print()

    # Run examples
    results: list[ExampleResult] = []
    for example_path in examples_to_run:
        print(f"  Running {example_path.name}...", end=" ", flush=True)
        result = run_example(example_path)
        results.append(result)

        if result.success:
            print("✅")
        else:
            print("❌")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    for result in results:
        status = "✅" if result.success else "❌"
        print(f"  {status} {result.name}: {result.message}")

    print()
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed > 0:
        print("\n❌ Some examples failed!")
        sys.exit(1)
    else:
        print("\n✅ All examples passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
