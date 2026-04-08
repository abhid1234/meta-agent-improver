#!/usr/bin/env python3
"""
eval_openrouter.py — Run ML advisor benchmark tasks via OpenRouter API.

Usage:
    python3 eval_openrouter.py \
        --benchmark benchmarks/ml-advisor/benchmark.yaml \
        --name llama-baseline \
        --model meta-llama/llama-3.1-8b-instruct \
        [--system-append "optional extra system prompt"] \
        [--tasks task_01,task_02] \
        [--fast]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import yaml

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run:", file=sys.stderr)
    print("  uv pip install openai --index-url https://pypi.org/simple/", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

USER_SUFFIX = (
    "\n\nWrite your proposal as a JSON object with fields: parameter, old_value, "
    "new_value, rationale. Output ONLY the JSON, no markdown fences or other text."
)


def build_user_prompt(context: str, results: str, train: str) -> str:
    parts = ["Here are the files in your workspace:"]
    parts.append(f"\n## context.md\n{context}")
    parts.append(f"\n## results.tsv\n{results}")
    parts.append(f"\n## train.py\n{train}")
    parts.append(USER_SUFFIX)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"parameter", "old_value", "new_value", "rationale"}


def extract_json(text: str) -> dict | None:
    """
    Try to extract a JSON object with the required proposal fields from model output.
    Handles markdown fences, preamble text, and bare JSON.
    """
    # 1. Strip ```json ... ``` or ``` ... ``` fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        candidate = fenced.group(1)
        try:
            obj = json.loads(candidate)
            if REQUIRED_FIELDS.issubset(obj.keys()):
                return obj
        except json.JSONDecodeError:
            pass

    # 2. Find all {...} blobs (greedy from first { to last })
    brace_matches = re.findall(r"\{[^{}]*\}", text, re.DOTALL)
    for candidate in brace_matches:
        try:
            obj = json.loads(candidate)
            if REQUIRED_FIELDS.issubset(obj.keys()):
                return obj
        except json.JSONDecodeError:
            continue

    # 3. Try the whole response as JSON
    try:
        obj = json.loads(text.strip())
        if REQUIRED_FIELDS.issubset(obj.keys()):
            return obj
    except json.JSONDecodeError:
        pass

    return None


# ---------------------------------------------------------------------------
# OpenRouter API call with retry
# ---------------------------------------------------------------------------

def call_openrouter(
    client: OpenAI,
    model: str,
    system_prompt: str,
    user_prompt: str,
    retries: int = 2,
    backoff: float = 5.0,
) -> str | None:
    """Call OpenRouter API. Returns response text or None on failure."""
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            status = getattr(e, "status_code", None)
            if attempt < retries and status in (429, 500, None):
                print(f"    [warn] API error ({e}), retrying in {backoff}s …")
                time.sleep(backoff)
            else:
                print(f"    [error] API call failed: {e}")
                return None
    return None


# ---------------------------------------------------------------------------
# Single task runner
# ---------------------------------------------------------------------------

def run_task(
    task: dict,
    benchmark_dir: Path,
    client: OpenAI,
    model: str,
    system_append: str,
) -> tuple[bool, dict | None]:
    """
    Run one benchmark task. Returns (passed, proposal_dict).
    """
    workspace_rel = task["workspace"]
    workspace_abs = (benchmark_dir / workspace_rel).resolve()

    # Read input files
    try:
        context = (workspace_abs / "context.md").read_text()
        results = (workspace_abs / "results.tsv").read_text()
        train = (workspace_abs / "train.py").read_text()
    except FileNotFoundError as e:
        print(f"    [error] Missing workspace file: {e}")
        return False, None

    # Build prompts
    instruction = task["instruction"].strip()
    system_prompt = instruction
    if system_append:
        system_prompt = f"{system_prompt}\n\n{system_append}"

    user_prompt = build_user_prompt(context, results, train)

    # Call API
    response_text = call_openrouter(client, model, system_prompt, user_prompt)
    if response_text is None:
        return False, None

    # Parse JSON
    proposal = extract_json(response_text)
    if proposal is None:
        print(f"    [error] Could not parse JSON from response. Raw output (first 300 chars):")
        print(f"    {repr(response_text[:300])}")
        return False, None

    # Write proposal.json to a temp copy of the workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir) / task["name"]
        shutil.copytree(workspace_abs, work_dir)

        proposal_path = work_dir / "proposal.json"
        proposal_path.write_text(json.dumps(proposal, indent=2))

        # Run verify
        verify_cmd = task["verify"]
        timeout = task.get("timeout", 120)
        try:
            result = subprocess.run(
                verify_cmd,
                cwd=str(work_dir),
                capture_output=True,
                timeout=timeout,
                text=True,
            )
            passed = result.returncode == 0
            if not passed:
                stdout_tail = result.stdout[-500:] if result.stdout else ""
                stderr_tail = result.stderr[-500:] if result.stderr else ""
                print(f"    [verify] FAIL (exit {result.returncode})")
                if stderr_tail:
                    print(f"    [stderr] {stderr_tail.strip()}")
                if stdout_tail:
                    print(f"    [stdout] {stdout_tail.strip()}")
        except subprocess.TimeoutExpired:
            print(f"    [error] verify timed out after {timeout}s")
            passed = False

    return passed, proposal


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run ML advisor benchmark via OpenRouter")
    parser.add_argument("--benchmark", required=True, help="Path to benchmark.yaml")
    parser.add_argument("--name", required=True, help="Run name (used for results file)")
    parser.add_argument("--model", required=True, help="OpenRouter model ID")
    parser.add_argument("--system-append", default="", help="Extra text appended to system prompt")
    parser.add_argument(
        "--tasks",
        default="",
        help="Comma-separated task names to run (default: all)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Only run tasks listed in fast_tasks from benchmark.yaml",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Load benchmark
    benchmark_path = Path(args.benchmark).resolve()
    if not benchmark_path.exists():
        print(f"ERROR: benchmark file not found: {benchmark_path}", file=sys.stderr)
        sys.exit(1)

    with open(benchmark_path) as f:
        benchmark = yaml.safe_load(f)

    benchmark_dir = benchmark_path.parent
    all_tasks = benchmark["tasks"]
    fast_task_names: list[str] = benchmark.get("fast_tasks", [])

    # Filter tasks
    if args.tasks:
        requested = set(args.tasks.split(","))
        tasks = [t for t in all_tasks if t["name"] in requested]
        if not tasks:
            print(f"ERROR: No tasks matched --tasks filter: {args.tasks}", file=sys.stderr)
            sys.exit(1)
    elif args.fast:
        fast_set = set(fast_task_names)
        tasks = [t for t in all_tasks if t["name"] in fast_set]
        print(f"Running {len(tasks)} fast tasks.")
    else:
        tasks = all_tasks

    # OpenRouter client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    # Results directory
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    tasks_passed: list[str] = []
    tasks_failed: list[str] = []

    print(f"\n{'='*60}")
    print(f"Benchmark : {benchmark.get('name', 'unknown')}")
    print(f"Run name  : {args.name}")
    print(f"Model     : {args.model}")
    print(f"Tasks     : {len(tasks)}")
    print(f"{'='*60}\n")

    for task in tasks:
        name = task["name"]
        print(f"[{name}] Running …")
        passed, proposal = run_task(
            task,
            benchmark_dir,
            client,
            args.model,
            args.system_append,
        )
        if passed:
            param = proposal.get("parameter", "?") if proposal else "?"
            old_val = proposal.get("old_value", "?") if proposal else "?"
            new_val = proposal.get("new_value", "?") if proposal else "?"
            print(f"[{name}] PASS — {param}: {old_val} → {new_val}")
            tasks_passed.append(name)
        else:
            print(f"[{name}] FAIL")
            tasks_failed.append(name)

    # Summary
    n_tasks = len(tasks)
    n_passed = len(tasks_passed)
    pass_rate = n_passed / n_tasks if n_tasks > 0 else 0.0

    print(f"\n{'='*60}")
    print(f"Summary: {n_passed}/{n_tasks} passed ({pass_rate:.0%})")
    if tasks_passed:
        print(f"  Passed : {', '.join(tasks_passed)}")
    if tasks_failed:
        print(f"  Failed : {', '.join(tasks_failed)}")
    print(f"{'='*60}\n")

    # Save results JSON
    results_payload = {
        "name": args.name,
        "model": args.model,
        "n_tasks": n_tasks,
        "n_passed": n_passed,
        "pass_rate": round(pass_rate, 4),
        "tasks_passed": tasks_passed,
        "tasks_failed": tasks_failed,
    }
    output_path = results_dir / f"{args.name}.json"
    output_path.write_text(json.dumps(results_payload, indent=2))
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
