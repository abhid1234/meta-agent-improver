#!/usr/bin/env python3
"""Deterministic verifier for ML Experiment Advisor proposals.

Checks whether a proposal.json in the current workspace matches
known-good experiment directions from ground truth data.

Exit 0 = good proposal (matches a known-improving direction)
Exit 1 = bad proposal (matches a known-failing direction or repeats past experiment)

Scoring tiers:
- Tasks 01-13 (early/mid): Must propose the BEST remaining change (ranked by expected improvement)
- Tasks 14-21 (late): Must propose FINAL_LR_FRAC=0.05 specifically (the historically correct next step)
- Tasks 22-30 (very late/synthetic): Must propose a novel untried parameter (not repeat any failure)
"""

import json
import sys
from pathlib import Path


def normalize_value(val):
    """Normalize values for comparison."""
    if isinstance(val, str):
        return val.strip().upper()
    if isinstance(val, list):
        return tuple(val)
    if isinstance(val, (int, float)):
        return float(val)
    return val


def values_match(proposed, reference):
    """Check if a proposed value matches a reference value (fuzzy for numbers)."""
    p = normalize_value(proposed)
    r = normalize_value(reference)

    if isinstance(p, float) and isinstance(r, float):
        if r == 0:
            return p == 0
        return abs(p - r) / abs(r) < 0.15
    return p == r


def check_repeats_failed(proposal, results_tsv):
    """Check if the proposal repeats a previously-failed experiment."""
    if not results_tsv.exists():
        return False

    param = proposal.get("parameter", "").upper()
    new_val = str(proposal.get("new_value", "")).upper()
    lines = results_tsv.read_text().strip().split("\n")

    for line in lines[1:]:
        cols = line.split("\t")
        if len(cols) < 5:
            continue
        status = cols[3].strip()
        desc = cols[4].strip().upper()

        if status in ("discard", "crash"):
            if param in desc and new_val in desc:
                return True
    return False


def main():
    workspace = Path.cwd()
    proposal_path = workspace / "proposal.json"

    if not proposal_path.exists():
        print("FAIL: proposal.json not found in workspace")
        sys.exit(1)

    try:
        proposal = json.loads(proposal_path.read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL: Invalid JSON in proposal.json: {e}")
        sys.exit(1)

    required_fields = ["parameter", "new_value", "rationale"]
    missing = [f for f in required_fields if f not in proposal]
    if missing:
        print(f"FAIL: proposal.json missing fields: {missing}")
        sys.exit(1)

    if not proposal.get("rationale", "").strip():
        print("FAIL: rationale is empty — must explain reasoning")
        sys.exit(1)

    task_name = workspace.name
    gt_path = Path(__file__).parent / "ground_truth.json"
    if not gt_path.exists():
        print("FAIL: ground_truth.json not found")
        sys.exit(1)

    ground_truth = json.loads(gt_path.read_text())
    task_gt = ground_truth.get(task_name)
    if task_gt is None:
        print(f"FAIL: No ground truth for {task_name}")
        sys.exit(1)

    param = proposal["parameter"]
    new_val = proposal["new_value"]
    task_num = int(task_name.split("_")[1])

    # Check 1: Does it repeat a known-failed experiment?
    results_tsv = workspace / "results.tsv"
    if check_repeats_failed(proposal, results_tsv):
        print(f"FAIL: Proposal repeats a previously-failed experiment direction")
        sys.exit(1)

    # Check 2: Does it match a known-bad proposal?
    for bad in task_gt.get("bad_proposals", []):
        if param.upper() == bad["parameter"].upper():
            if values_match(new_val, bad["new_value"]):
                print(f"FAIL: {param}={new_val} is a known-bad change ({bad['why']})")
                sys.exit(1)

    # === TIER 1: Early/mid tasks (01-13) — must pick the BEST proposal ===
    if task_num <= 13:
        # Only the first good proposal (ranked by importance) is accepted
        # The ranking in ground_truth.json is: best first
        best_proposals = task_gt.get("good_proposals", [])
        if not best_proposals:
            print(f"FAIL: No good proposals defined for {task_name}")
            sys.exit(1)

        # Accept only the top-ranked good proposal(s) — first one in the list
        best = best_proposals[0]
        if param.upper() == best["parameter"].upper():
            print(f"PASS: {param}={new_val} matches the best proposal ({best['why']})")
            sys.exit(0)

        # Also accept the second-best if there are multiple good options
        if len(best_proposals) >= 2:
            second = best_proposals[1]
            if param.upper() == second["parameter"].upper():
                print(f"PASS: {param}={new_val} matches a top-2 proposal ({second['why']})")
                sys.exit(0)

        # Wrong parameter chosen — fail
        best_params = [p["parameter"] for p in best_proposals[:2]]
        print(f"FAIL: {param} is not the best proposal. Expected one of: {best_params}")
        sys.exit(1)

    # === TIER 2: Late tasks (14-21) — must find FINAL_LR_FRAC=0.05 ===
    if 14 <= task_num <= 21:
        # The historically correct answer is FINAL_LR_FRAC → 0.05
        if param.upper() == "FINAL_LR_FRAC":
            val = normalize_value(new_val)
            if isinstance(val, float) and 0.02 <= val <= 0.08:
                print(f"PASS: {param}={new_val} — correct LR floor direction")
                sys.exit(0)
            else:
                print(f"FAIL: {param}={new_val} — LR floor value out of range (need 0.02-0.08)")
                sys.exit(1)

        # Also accept novel untried parameters as secondary win
        tried_params = {b["parameter"].upper() for b in task_gt.get("bad_proposals", [])}
        good_params = {g["parameter"].upper() for g in task_gt.get("good_proposals", [])}
        all_known = tried_params | good_params

        if param.upper() not in all_known:
            print(f"PASS: Novel parameter {param} — acceptable but not the best answer")
            sys.exit(0)

        print(f"FAIL: {param} is not the best proposal for late stage. Expected FINAL_LR_FRAC or novel param.")
        sys.exit(1)

    # === TIER 3: Very late / synthetic (22-30) — novel untried params only ===
    if task_num >= 22:
        # Check if it matches a known-good direction
        for good in task_gt.get("good_proposals", []):
            if param.upper() == good["parameter"].upper():
                print(f"PASS: {param}={new_val} is a known-good direction ({good['why']})")
                sys.exit(0)

        # Accept truly novel parameters not in any list
        tried_params = {b["parameter"].upper() for b in task_gt.get("bad_proposals", [])}
        good_params = {g["parameter"].upper() for g in task_gt.get("good_proposals", [])}
        all_known = tried_params | good_params

        if param.upper() not in all_known:
            print(f"PASS: Novel parameter {param} — hasn't been tried before")
            sys.exit(0)

        print(f"FAIL: {param}={new_val} is not novel and not a known-good direction")
        sys.exit(1)

    print(f"FAIL: {param}={new_val} — no matching rule")
    sys.exit(1)


if __name__ == "__main__":
    main()
