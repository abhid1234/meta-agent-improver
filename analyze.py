#!/usr/bin/env python3
"""
analyze.py — Meta-agent experience store analysis.

Reads candidate scores from the ml-advisor experience store, compares
baseline vs. best config, and writes results/analysis.md.

Usage:
    python3 analyze.py
"""

import json
import re
import textwrap
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent
CANDIDATES_DIR = REPO_ROOT / "meta-agent/experience/ml-advisor/candidates"
HISTORY_FILE = REPO_ROOT / "meta-agent/experience/ml-advisor/history.json"
RESULTS_DIR = REPO_ROOT / "results"
OUTPUT_FILE = RESULTS_DIR / "analysis.md"


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_scores(candidate_dir: Path) -> dict | None:
    """Load scores.json from a candidate directory. Returns None if missing."""
    path = candidate_dir / "scores.json"
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def load_history() -> dict | None:
    if not HISTORY_FILE.exists():
        return None
    with HISTORY_FILE.open() as f:
        return json.load(f)


def load_config_text(candidate_dir: Path) -> str | None:
    path = candidate_dir / "config.py"
    if not path.exists():
        return None
    return path.read_text()


def sparkline(values: list[float]) -> str:
    """Render a list of 0-1 floats as a text sparkline using block chars."""
    bars = " ▁▂▃▄▅▆▇█"
    if not values:
        return ""
    mn, mx = min(values), max(values)
    span = mx - mn if mx != mn else 1.0
    chars = []
    for v in values:
        idx = round((v - mn) / span * (len(bars) - 1))
        chars.append(bars[idx])
    return "".join(chars)


def diff_configs(base_text: str, other_text: str) -> list[str]:
    """
    Extract meaningful differences between two config.py files.
    Returns a list of human-readable change descriptions.
    """
    changes = []

    # Docstring diff — first triple-quoted string
    def extract_docstring(text):
        m = re.search(r'"""(.*?)"""', text, re.DOTALL)
        return m.group(1).strip() if m else ""

    base_doc = extract_docstring(base_text)
    other_doc = extract_docstring(other_text)
    if base_doc != other_doc:
        # Pull the "Change from baseline:" line if present
        change_line = next(
            (ln.strip() for ln in other_doc.splitlines()
             if ln.strip().lower().startswith("change from baseline")),
            None,
        )
        if change_line:
            changes.append(f"Docstring change summary: {change_line}")
        else:
            changes.append("Docstring updated (no explicit change summary found)")

    # system_prompt type/preset/append
    def extract_sysprompt(text):
        m = re.search(r'system_prompt\s*=\s*(\{.*?\})', text, re.DOTALL)
        return m.group(1) if m else ""

    base_sp = extract_sysprompt(base_text)
    other_sp = extract_sysprompt(other_text)
    if base_sp != other_sp:
        if '"append"' in other_sp and '"append"' not in base_sp:
            changes.append('system_prompt: added "append" key with extra guidance text')
        elif '"preset"' in other_sp:
            changes.append(f"system_prompt: changed to {other_sp[:120].strip()}")
        else:
            changes.append("system_prompt: changed")

    # max_turns
    def extract_int_param(text, param):
        m = re.search(rf'{param}\s*=\s*(\d+)', text)
        return int(m.group(1)) if m else None

    for param in ("max_turns", "max_budget_usd"):
        bv = extract_int_param(base_text, param)
        ov = extract_int_param(other_text, param)
        if bv is not None and ov is not None and bv != ov:
            changes.append(f"{param}: {bv} → {ov}")

    # thinking type
    def extract_thinking(text):
        m = re.search(r'thinking\s*=\s*(\{[^}]+\})', text)
        return m.group(1).strip() if m else ""

    bt = extract_thinking(base_text)
    ot = extract_thinking(other_text)
    if bt != ot:
        changes.append(f"thinking: {bt} → {ot}")

    # Any new top-level string constants (e.g. _ADVISOR_GUIDANCE)
    base_consts = set(re.findall(r'^(_[A-Z_]+)\s*=\s*"""', base_text, re.MULTILINE))
    other_consts = set(re.findall(r'^(_[A-Z_]+)\s*=\s*"""', other_text, re.MULTILINE))
    new_consts = other_consts - base_consts
    if new_consts:
        changes.append(f"New module-level prompt constants added: {', '.join(sorted(new_consts))}")

    if not changes:
        changes.append("No structural differences detected between configs")

    return changes


def col(text: str, width: int, align: str = "left") -> str:
    """Pad/truncate text to fixed width for table formatting."""
    s = str(text)
    if len(s) > width:
        s = s[: width - 1] + "…"
    if align == "right":
        return s.rjust(width)
    return s.ljust(width)


# ── Main analysis ─────────────────────────────────────────────────────────

def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Discover candidates in iteration order
    candidate_dirs = sorted(
        [d for d in CANDIDATES_DIR.iterdir() if d.is_dir()],
        key=lambda d: (0 if d.name == "baseline" else 1, d.name),
    )

    candidates = []
    for d in candidate_dirs:
        scores = load_scores(d)
        if scores is None:
            continue  # no scores yet — skip (e.g. staging)
        candidates.append({"dir": d, "name": d.name, "scores": scores})

    if not candidates:
        print("No scored candidates found — nothing to analyze.")
        return

    # 2. History
    history = load_history()
    history_iters = history.get("iterations", []) if history else []

    # 3. Identify baseline and best
    baseline = next((c for c in candidates if c["name"] == "baseline"), candidates[0])
    best = max(candidates, key=lambda c: (c["scores"]["pass_rate"], -c["scores"]["total_cost_usd"]))

    # 4. Summary table ──────────────────────────────────────────────────────
    header = (
        f"{'Iteration':<14} {'Pass Rate':>9} {'Passed/Total':>13} "
        f"{'Total Cost':>11} {'Mean Cost':>10}"
    )
    sep = "-" * len(header)

    table_rows = []
    for c in candidates:
        s = c["scores"]
        pr = s.get("pass_rate", 0)
        n_passed = s.get("n_passed", 0)
        n_tasks = s.get("n_tasks", 0)
        total_cost = s.get("total_cost_usd", 0)
        mean_cost = s.get("mean_cost_usd", 0)
        marker = " ★" if c["name"] == best["name"] else ("  " if c["name"] != "baseline" else "  ")
        table_rows.append(
            f"{c['name'] + marker:<14} {pr:>8.1%} {f'{n_passed}/{n_tasks}':>13} "
            f"${total_cost:>10.4f} ${mean_cost:>9.5f}"
        )

    # 5. Accuracy sparkline (from history or from candidates) ───────────────
    if history_iters:
        spark_values = [it["pass_rate"] for it in history_iters]
        spark_labels = [it["name"] for it in history_iters]
    else:
        spark_values = [c["scores"]["pass_rate"] for c in candidates]
        spark_labels = [c["name"] for c in candidates]

    spark = sparkline(spark_values)
    spark_detail = "  ".join(
        f"{lbl}={v:.0%}" for lbl, v in zip(spark_labels, spark_values)
    )

    # 6. Unlocked tasks ────────────────────────────────────────────────────
    baseline_failed = set(baseline["scores"].get("tasks_failed", []))
    best_passed = set(best["scores"].get("tasks_passed", []))
    unlocked = sorted(baseline_failed & best_passed)

    still_failing = sorted(
        set(best["scores"].get("tasks_failed", [])) - baseline_failed
    )
    regressions = sorted(
        set(best["scores"].get("tasks_failed", [])) & set(baseline["scores"].get("tasks_passed", []))
    )

    # 7. Config diff ───────────────────────────────────────────────────────
    baseline_config = load_config_text(baseline["dir"])
    best_config = load_config_text(best["dir"])

    if baseline["name"] == best["name"]:
        config_diff_lines = ["Baseline IS the best config — no diff."]
    elif baseline_config is None or best_config is None:
        config_diff_lines = ["Could not load one or both config files."]
    else:
        config_diff_lines = diff_configs(baseline_config, best_config)

    # 8. Console output ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  META-AGENT EXPERIENCE ANALYSIS — ml-advisor")
    print("=" * 60)
    print(f"\nCandidates found: {len(candidates)}")
    print(f"Best config:      {best['name']}  ({best['scores']['pass_rate']:.1%} pass rate)")
    print(f"Baseline:         {baseline['name']}  ({baseline['scores']['pass_rate']:.1%} pass rate)\n")

    print(header)
    print(sep)
    for row in table_rows:
        print(row)

    print(f"\nAccuracy curve:  {spark}")
    print(f"                 {spark_detail}")

    print(f"\nUnlocked tasks ({len(unlocked)}):")
    if unlocked:
        for t in unlocked:
            print(f"  + {t}")
    else:
        print("  (none — best == baseline or no improvement)")

    if regressions:
        print(f"\nRegressions ({len(regressions)}) — passed in baseline, fail in best:")
        for t in regressions:
            print(f"  - {t}")

    print(f"\nConfig changes (baseline → {best['name']}):")
    for line in config_diff_lines:
        print(f"  • {line}")

    # 9. Write analysis.md ─────────────────────────────────────────────────
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    md_lines = [
        f"# ml-advisor Meta-Agent Analysis",
        f"",
        f"_Generated: {now}_",
        f"",
        f"## Summary",
        f"",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Candidates evaluated | {len(candidates)} |",
        f"| Best config | `{best['name']}` |",
        f"| Best pass rate | {best['scores']['pass_rate']:.1%} ({best['scores']['n_passed']}/{best['scores']['n_tasks']}) |",
        f"| Baseline pass rate | {baseline['scores']['pass_rate']:.1%} ({baseline['scores']['n_passed']}/{baseline['scores']['n_tasks']}) |",
        f"| Improvement | {best['scores']['pass_rate'] - baseline['scores']['pass_rate']:+.1%} |",
        f"| Tasks unlocked | {len(unlocked)} |",
        f"",
        f"## Candidate Scores",
        f"",
        f"| Iteration | Pass Rate | Passed/Total | Total Cost | Mean Cost/Task |",
        f"|-----------|-----------|--------------|------------|----------------|",
    ]

    for c in candidates:
        s = c["scores"]
        pr = s.get("pass_rate", 0)
        n_passed = s.get("n_passed", 0)
        n_tasks = s.get("n_tasks", 0)
        total_cost = s.get("total_cost_usd", 0)
        mean_cost = s.get("mean_cost_usd", 0)
        marker = " ★" if c["name"] == best["name"] else ""
        md_lines.append(
            f"| `{c['name']}`{marker} | {pr:.1%} | {n_passed}/{n_tasks} | ${total_cost:.4f} | ${mean_cost:.5f} |"
        )

    md_lines += [
        f"",
        f"## Accuracy Improvement Curve",
        f"",
        f"```",
        f"{spark}",
        f"{spark_detail}",
        f"```",
        f"",
        f"## Unlocked Tasks",
        f"",
        f"Tasks that **failed in baseline** but **pass in best config** (`{best['name']}`):",
        f"",
    ]

    if unlocked:
        for t in unlocked:
            md_lines.append(f"- `{t}`")
    else:
        md_lines.append("_(none — no improvement over baseline, or best == baseline)_")

    if regressions:
        md_lines += [
            f"",
            f"### Regressions",
            f"",
            f"Tasks that passed in baseline but **fail** in best config:",
            f"",
        ]
        for t in regressions:
            md_lines.append(f"- `{t}`")

    if still_failing:
        md_lines += [
            f"",
            f"### Still Failing in Best Config",
            f"",
        ]
        for t in still_failing:
            md_lines.append(f"- `{t}`")

    md_lines += [
        f"",
        f"## Config Diff: baseline → {best['name']}",
        f"",
    ]

    if baseline_config and best_config and baseline["name"] != best["name"]:
        md_lines += [
            f"### What Changed",
            f"",
        ]
        for line in config_diff_lines:
            md_lines.append(f"- {line}")

        md_lines += [
            f"",
            f"### Baseline `config.py`",
            f"",
            f"```python",
        ]
        md_lines += baseline_config.splitlines()
        md_lines += [
            f"```",
            f"",
            f"### Best (`{best['name']}`) `config.py`",
            f"",
            f"```python",
        ]
        md_lines += best_config.splitlines()
        md_lines.append("```")
    else:
        md_lines.append("_Baseline is the best config — no diff available._")

    if history_iters:
        md_lines += [
            f"",
            f"## Optimization History",
            f"",
            f"| Iteration | Pass Rate | Passed | Tasks | Cost | Timestamp |",
            f"|-----------|-----------|--------|-------|------|-----------|",
        ]
        for it in history_iters:
            ts = it.get("timestamp", "")[:19].replace("T", " ")
            md_lines.append(
                f"| `{it['name']}` | {it['pass_rate']:.1%} | {it['n_passed']} | {it['n_tasks']} | ${it['cost_usd']:.4f} | {ts} |"
            )

    md_content = "\n".join(md_lines) + "\n"

    OUTPUT_FILE.write_text(md_content)
    print(f"\nWrote: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
