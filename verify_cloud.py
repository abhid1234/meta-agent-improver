#!/usr/bin/env python3
"""Deterministic verifier for Cloud Infrastructure Sizing proposals.

Checks whether a proposal.json in the current workspace matches
known-good sizing recommendations from ground_truth_cloud.json.

Proposal format:
  {
    "machine_type": "n2-standard-8",
    "num_nodes": 3,          # for GKE cluster tasks
    "num_instances": 20,     # for VM fleet tasks (use one of num_nodes or num_instances)
    "rationale": "..."
  }

Exit 0 = pass (reasonable machine type choice)
Exit 1 = fail (wrong machine family, clearly bad choice, missing rationale)
"""

import json
import sys
from pathlib import Path


def normalize_machine_type(mt: str) -> str:
    """Normalize machine type string for comparison."""
    return mt.strip().lower()


def extract_family(machine_type: str) -> str:
    """Extract the machine family prefix from a machine type.

    Examples:
      n2-standard-8        -> n2
      n2-highmem-16        -> n2-highmem
      e2-standard-4        -> e2
      a2-highgpu-4g        -> a2
      c3-standard-22       -> c3
      n1-standard-4        -> n1
      g2-standard-8        -> g2
      m1-megamem-96        -> m1
      m3-ultramem-32       -> m3
      n2d-standard-8       -> n2d
    """
    mt = normalize_machine_type(machine_type)
    # Split on '-' and take the first one or two parts
    parts = mt.split("-")
    if len(parts) == 0:
        return mt

    # Handle families like n2-highmem, n2-standard, e2-highmem, m1-megamem etc.
    # The "family" for ground truth matching is the series prefix before the size
    # e.g. "n2-highmem" is a sub-family of "n2"
    # We check both the top-level prefix and the full sub-family
    return parts[0]


def extract_subfamilies(machine_type: str) -> list[str]:
    """Return all possible family prefixes for matching.

    For 'n2-highmem-16' returns: ['n2-highmem', 'n2']
    For 'e2-standard-4' returns: ['e2-standard', 'e2']
    For 'a2-highgpu-4g' returns: ['a2-highgpu', 'a2']
    """
    mt = normalize_machine_type(machine_type)
    parts = mt.split("-")
    families = []
    # Build progressively from full sub-family down to top-level
    # e.g. n2-highmem-16 -> ["n2-highmem", "n2"]
    if len(parts) >= 2:
        families.append(f"{parts[0]}-{parts[1]}")
    if len(parts) >= 1:
        families.append(parts[0])
    return families


def check_family_match(proposed_mt: str, acceptable_families: list[str]) -> bool:
    """Check if the proposed machine type belongs to an acceptable family."""
    proposed_families = extract_subfamilies(proposed_mt)
    for family in acceptable_families:
        family_normalized = family.strip().lower()
        for pf in proposed_families:
            if pf == family_normalized:
                return True
    return False


def check_exact_match(proposed_mt: str, acceptable_machine_types: list[str]) -> bool:
    """Check if the proposed machine type is in the acceptable list."""
    proposed_normalized = normalize_machine_type(proposed_mt)
    for mt in acceptable_machine_types:
        if normalize_machine_type(mt) == proposed_normalized:
            return True
    return False


def check_bad_choice(proposed_mt: str, bad_choices: list[str]) -> bool:
    """Check if the proposed machine type is a known-bad choice."""
    proposed_normalized = normalize_machine_type(proposed_mt)
    for bad in bad_choices:
        if normalize_machine_type(bad) == proposed_normalized:
            return True
    return False


def check_gpu_requirement(proposed_mt: str, requires_gpu: bool) -> tuple[bool, str]:
    """Check if GPU requirement is met."""
    gpu_keywords = ["gpu", "g2-", "a2-", "a3-"]
    has_gpu = any(kw in normalize_machine_type(proposed_mt) for kw in gpu_keywords)

    if requires_gpu and not has_gpu:
        return False, f"Task requires GPU but proposed machine '{proposed_mt}' has no GPU"
    if not requires_gpu and has_gpu:
        return False, f"Task does not need GPU but proposed machine '{proposed_mt}' includes GPU (massive overkill)"
    return True, ""


def check_local_ssd_requirement(proposed_mt: str, requires_local_ssd: bool) -> tuple[bool, str]:
    """Warn if local SSD is required but machine may not support it.

    Note: local SSD support is configuration-level, not embedded in machine type name.
    We check for known machine types that do NOT support local SSD (e.g., e2, m1, m2).
    """
    if not requires_local_ssd:
        return True, ""

    no_local_ssd_families = ["e2", "m1", "m2"]
    top_family = extract_family(proposed_mt)
    if top_family in no_local_ssd_families:
        return False, (
            f"Task requires local SSD but '{proposed_mt}' ({top_family} family) "
            f"does not support local SSD. Use n2, c2, c3, or n1 series instead."
        )
    return True, ""


def check_node_count(proposal: dict, task_gt: dict) -> tuple[bool, str]:
    """Check if num_nodes or num_instances is within acceptable range."""
    node_range = task_gt.get("num_nodes_range")
    instance_range = task_gt.get("num_instances_range")

    # Get the proposed count — accept either field name
    proposed_nodes = proposal.get("num_nodes")
    proposed_instances = proposal.get("num_instances")
    proposed_count = proposed_nodes if proposed_nodes is not None else proposed_instances

    if node_range is not None:
        if proposed_count is None:
            return False, "GKE cluster task requires 'num_nodes' field in proposal"
        lo, hi = node_range
        if not (lo <= proposed_count <= hi):
            return False, (
                f"num_nodes={proposed_count} is outside acceptable range [{lo}, {hi}]"
            )

    if instance_range is not None:
        if proposed_count is None:
            # If there's an instance range defined but no count given, still pass
            # (some tasks don't strictly require the count)
            return True, ""
        lo, hi = instance_range
        if not (lo <= proposed_count <= hi):
            return False, (
                f"num_instances={proposed_count} is outside acceptable range [{lo}, {hi}]"
            )

    return True, ""


def check_budget(proposal: dict, task_gt: dict) -> tuple[bool, str]:
    """Check if budget constraint is respected (if applicable)."""
    max_cost = task_gt.get("max_monthly_cost_usd")
    if max_cost is None:
        return True, ""

    # We can't easily compute cost from machine type alone without pricing API
    # Instead check that the proposed machine isn't obviously expensive
    # This is a heuristic check based on known family costs
    proposed_mt = normalize_machine_type(proposal.get("machine_type", ""))
    expensive_for_budget = ["n2-standard-32", "n2-highmem-32", "c2-standard-30", "a2-"]
    for exp in expensive_for_budget:
        if exp in proposed_mt:
            return False, (
                f"Machine '{proposed_mt}' is likely too expensive for the ${max_cost}/month budget. "
                f"Choose a smaller instance type."
            )
    return True, ""


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

    # Required fields
    required_fields = ["machine_type", "rationale"]
    missing = [f for f in required_fields if f not in proposal]
    if missing:
        print(f"FAIL: proposal.json missing required fields: {missing}")
        sys.exit(1)

    if not proposal.get("rationale", "").strip():
        print("FAIL: rationale is empty — must explain the sizing reasoning")
        sys.exit(1)

    if len(proposal["rationale"].strip()) < 20:
        print("FAIL: rationale is too short — must provide meaningful justification")
        sys.exit(1)

    machine_type = proposal["machine_type"]
    if not machine_type or not machine_type.strip():
        print("FAIL: machine_type is empty")
        sys.exit(1)

    # Load ground truth
    task_name = workspace.name
    gt_path = Path(__file__).parent / "ground_truth_cloud.json"
    if not gt_path.exists():
        print(f"FAIL: ground_truth_cloud.json not found at {gt_path}")
        sys.exit(1)

    ground_truth = json.loads(gt_path.read_text())
    task_gt = ground_truth.get(task_name)
    if task_gt is None:
        print(f"FAIL: No ground truth entry for '{task_name}' in ground_truth_cloud.json")
        sys.exit(1)

    # === Check 1: Known-bad choice ===
    bad_choices = task_gt.get("bad_choices", [])
    if check_bad_choice(machine_type, bad_choices):
        bad_desc = task_gt.get("notes", "clearly wrong for this workload")
        print(f"FAIL: '{machine_type}' is a known-bad choice for this workload. {bad_desc}")
        sys.exit(1)

    # === Check 2: GPU requirement ===
    gpu_ok, gpu_msg = check_gpu_requirement(machine_type, task_gt.get("requires_gpu", False))
    if not gpu_ok:
        print(f"FAIL: {gpu_msg}")
        sys.exit(1)

    # === Check 3: Local SSD requirement ===
    ssd_ok, ssd_msg = check_local_ssd_requirement(machine_type, task_gt.get("requires_local_ssd", False))
    if not ssd_ok:
        print(f"FAIL: {ssd_msg}")
        sys.exit(1)

    # === Check 4: Node/instance count ===
    count_ok, count_msg = check_node_count(proposal, task_gt)
    if not count_ok:
        print(f"FAIL: {count_msg}")
        sys.exit(1)

    # === Check 5: Budget constraint ===
    budget_ok, budget_msg = check_budget(proposal, task_gt)
    if not budget_ok:
        print(f"FAIL: {budget_msg}")
        sys.exit(1)

    # === Check 6: Acceptable family (primary pass/fail gate) ===
    acceptable_families = task_gt.get("acceptable_families", [])
    if not check_family_match(machine_type, acceptable_families):
        top_family = extract_family(machine_type)
        print(
            f"FAIL: '{machine_type}' (family: {top_family}) is not in the acceptable "
            f"families for this task: {acceptable_families}\n"
            f"Notes: {task_gt.get('notes', '')}"
        )
        sys.exit(1)

    # === Check 7: Exact match bonus (pass with distinction) ===
    acceptable_types = task_gt.get("acceptable_machine_types", [])
    if check_exact_match(machine_type, acceptable_types):
        print(
            f"PASS: '{machine_type}' is an exact match for this workload. "
            f"{task_gt.get('notes', '')}"
        )
        sys.exit(0)

    # Family matches but not an exact known-good type — still pass (flexible sizing)
    print(
        f"PASS: '{machine_type}' is in an acceptable family ({extract_family(machine_type)}) "
        f"for this workload. Consider: {acceptable_types[:3]} for optimal sizing. "
        f"{task_gt.get('notes', '')}"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
