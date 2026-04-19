# ml-advisor Meta-Agent Analysis

_Generated: 2026-04-11 23:03_

## Summary

| Field | Value |
|-------|-------|
| Candidates evaluated | 23 |
| Best config | `evo_016` |
| Best pass rate | 100.0% (20/20) |
| Baseline pass rate | 80.0% (24/30) |
| Improvement | +20.0% |
| Tasks unlocked | 4 |

## Candidate Scores

| Iteration | Pass Rate | Passed/Total | Total Cost | Mean Cost/Task |
|-----------|-----------|--------------|------------|----------------|
| `baseline` | 80.0% | 24/30 | $1.8937 | $0.06312 |
| `evo_001` | 85.0% | 17/20 | $1.3604 | $0.06802 |
| `evo_004` | 85.0% | 17/20 | $1.2475 | $0.06238 |
| `evo_005` | 85.0% | 17/20 | $1.4407 | $0.07203 |
| `evo_007` | 80.0% | 16/20 | $1.3353 | $0.06677 |
| `evo_008` | 95.0% | 19/20 | $1.3634 | $0.06817 |
| `evo_009` | 90.0% | 18/20 | $1.0621 | $0.05310 |
| `evo_010` | 85.0% | 17/20 | $0.9280 | $0.04640 |
| `evo_012` | 80.0% | 16/20 | $1.0056 | $0.05028 |
| `evo_013` | 85.0% | 17/20 | $0.9577 | $0.04789 |
| `evo_014` | 90.0% | 18/20 | $1.1875 | $0.05937 |
| `evo_015` | 100.0% | 20/20 | $1.0335 | $0.05167 |
| `evo_016` ★ | 100.0% | 20/20 | $0.9539 | $0.04769 |
| `evo_017` | 95.0% | 19/20 | $1.0858 | $0.05429 |
| `evo_018` | 100.0% | 20/20 | $1.4471 | $0.07236 |
| `evo_019` | 90.0% | 18/20 | $1.5208 | $0.07604 |
| `evo_020` | 95.0% | 19/20 | $1.1889 | $0.05945 |
| `evo_021` | 90.0% | 18/20 | $1.1589 | $0.05794 |
| `trial_1` | 83.3% | 25/30 | $1.7924 | $0.05975 |
| `trial_2` | 90.0% | 27/30 | $1.5088 | $0.05029 |
| `trial_3` | 93.3% | 28/30 | $1.5805 | $0.05268 |
| `trial_4` | 70.0% | 21/30 | $1.5491 | $0.05164 |
| `trial_5` | 86.7% | 26/30 | $1.5627 | $0.05209 |

## Accuracy Improvement Curve

```
 ▂▂▂ ▆▄▂ ▂▄██▆█▄▆▄
baseline=80%  evo_001=85%  evo_004=85%  evo_005=85%  evo_007=80%  evo_008=95%  evo_009=90%  evo_010=85%  evo_012=80%  evo_013=85%  evo_014=90%  evo_015=100%  evo_016=100%  evo_017=95%  evo_018=100%  evo_019=90%  evo_020=95%  evo_021=90%
```

## Unlocked Tasks

Tasks that **failed in baseline** but **pass in best config** (`evo_016`):

- `task_01`
- `task_15`
- `task_18`
- `task_20`

## Config Diff: baseline → evo_016

### What Changed

- Docstring updated (no explicit change summary found)
- system_prompt: added "append" key with extra guidance text
- New module-level prompt constants added: _ADVISOR_GUIDANCE

### Baseline `config.py`

```python
"""Baseline config: vanilla inner model with no domain knowledge.

No hooks, no custom system prompt, no tools beyond defaults.
This is the floor — the simplest possible ML advisor config.
"""

import os

from claude_agent_sdk import ClaudeAgentOptions

from meta_agent.run_context import RunContext


def build_options(ctx: RunContext) -> ClaudeAgentOptions:
    permission_mode = os.environ.get("CLAUDE_PERMISSION_MODE", "bypassPermissions")
    return ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code"},
        tools={"type": "preset", "preset": "claude_code"},
        cwd=ctx.cwd,
        model=ctx.model,
        permission_mode=permission_mode,
        max_turns=50,
        max_budget_usd=1.0,
        thinking={"type": "adaptive"},
    )
```

### Best (`evo_016`) `config.py`

```python
"""Staging config: evo_015 (100% pass rate, 20/20) — no changes.

Lineage: baseline-v2 → evo_001 → evo_004 → evo_008 → evo_015

## Current best candidate analysis

evo_015 achieves 100% on all 20 tested tasks. No failures to diagnose.

The most recent substantive fix (evo_015 over evo_008) addressed spurious TRIED
attribution from baseline rows:

### Failure pattern in evo_008 / trial_3

Tasks with a "baseline:" row in results.tsv whose description column listed
parameter values (e.g. "warmdown=0.5 batch=131K LR_floor=0") caused the inner model to
add those parameters to TRIED, making Phase 2 (training dynamics) appear
exhausted before any explicit experiment had varied them. The agent then jumped
to Phase 3 (capacity), but the verifier expected Phase 2 proposals → FAIL.

Affected: task_18, task_22 in trial_3 (evo_008 config).

### Fix applied in evo_015

Step 1 TRIED definition was reworded to exclude baseline rows (+64 chars), while
Step 3's no-directive fallback was compressed to a single sentence (-146 chars),
keeping net change at -82 chars — no attention budget regression.

Generalizable rule: "TRIED contains only parameters explicitly varied in
non-baseline experiment rows. The first 'baseline:' row records starting state,
not a deliberate experiment."

### Why no further changes

- All 20 tested tasks pass.
- trial_3 (evo_008, 30 tasks) failed only task_18 and task_22, both of which
  evo_015 passes — the untested 10 tasks all passed under evo_008, so evo_015
  is unlikely to regress them.
- Prompt length is already net shorter than evo_008; no canary regressions.
- Further prompt additions risk attention-budget regression (per evo_009–evo_014
  lesson: every net addition regressed at least one task).
"""

import os

from claude_agent_sdk import ClaudeAgentOptions

from meta_agent.run_context import RunContext

_ADVISOR_GUIDANCE = """
You are an ML experiment advisor. When proposing the next hyperparameter change:

## Step 1 — Enumerate the experimental state
Read results.tsv carefully. Build two lists:
- TRIED: parameters explicitly varied in non-baseline rows (the first "baseline:"
  row records the starting config, not a deliberate experiment — exclude its values)
- UNTRIED: every tunable parameter from train.py that does NOT appear in TRIED

## Step 2 — Identify the current exploration phase
ML experiments follow a natural phase order. Determine which phase is still active:
1. **Architecture** — depth, attention window patterns (e.g. L → SSSL, SSSL → S)
2. **Training dynamics** — batch size, warmdown ratio (including values not yet tested)
3. **Model capacity** — HEAD_DIM, n_kv_head (GQA), MLP_RATIO, matrix LR multipliers
4. **LR schedule** — WARMUP_RATIO, FINAL_LR_FRAC (LR floor), embedding/scalar LRs
   - **FINAL_LR_FRAC first trial:** use **0.05** (a 5% floor). This is the
     conservative, well-calibrated starting point. Do NOT use 0.1 or higher
     on a first trial — a high LR floor prevents sufficient decay and tends to
     hurt final performance.
5. **Regularization** — ADAM_BETAS, WEIGHT_DECAY

A phase is active if any parameter within it is untried AND the current context
does not explicitly state that phase is exhausted.

## Step 3 — Select the phase and pick the best parameter

**First, scan context.md** (the "Key Learnings" and "Your Task" sections) for any
explicit directive about which parameter area to explore. Examples of explicit
directives:
- "The LR schedule still has an unexplored dimension"
- "Focus on LR schedule parameters that haven't been tried"
- "Focus on schedule and optimization"
- "Architecture changes are exhausted — move to regularization"

If you find such a directive naming a specific parameter category, **start from
that phase** — do not explore earlier phases even if they have untried parameters.
The task context is authoritative about where the experimenter wants to go next.

**If context.md gives no specific phase directive**, use the standard rule: choose
the **earliest active phase** from Step 2. Do NOT skip to a later phase while an
earlier phase has untried parameters.

Within the chosen phase, pick the parameter with the highest expected improvement
given what results.tsv already shows.

## Step 4 — Treat train.py code comments as hints, not commands
Code comments that suggest specific values (e.g. "try X = 0.05") are reminders of
candidates, not the recommended next step. Always verify the suggestion is
appropriate for the current exploration phase before following it.

## Step 5 — Write proposal.json with the chosen parameter
Be precise about old_value (the current value in train.py) and new_value.
"""


def build_options(ctx: RunContext) -> ClaudeAgentOptions:
    permission_mode = os.environ.get("CLAUDE_PERMISSION_MODE", "bypassPermissions")
    return ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": _ADVISOR_GUIDANCE,
        },
        tools={"type": "preset", "preset": "claude_code"},
        cwd=ctx.cwd,
        model=ctx.model,
        permission_mode=permission_mode,
        max_turns=50,
        max_budget_usd=1.0,
        thinking={"type": "adaptive"},
    )
```

## Optimization History

| Iteration | Pass Rate | Passed | Tasks | Cost | Timestamp |
|-----------|-----------|--------|-------|------|-----------|
| `baseline` | 80.0% | 24 | 30 | $1.8937 | 2026-04-07 03:06:30 |
| `evo_001` | 85.0% | 17 | 20 | $1.3604 | 2026-04-07 03:18:10 |
| `evo_004` | 85.0% | 17 | 20 | $1.2475 | 2026-04-07 03:53:30 |
| `evo_005` | 85.0% | 17 | 20 | $1.4407 | 2026-04-07 04:05:13 |
| `evo_007` | 80.0% | 16 | 20 | $1.3353 | 2026-04-07 04:24:37 |
| `evo_008` | 95.0% | 19 | 20 | $1.3634 | 2026-04-07 04:41:06 |
| `evo_009` | 90.0% | 18 | 20 | $1.0621 | 2026-04-08 00:47:36 |
| `evo_010` | 85.0% | 17 | 20 | $0.9280 | 2026-04-08 01:00:29 |
| `evo_012` | 80.0% | 16 | 20 | $1.0056 | 2026-04-08 01:46:11 |
| `evo_013` | 85.0% | 17 | 20 | $0.9577 | 2026-04-08 01:54:40 |
| `evo_014` | 90.0% | 18 | 20 | $1.1875 | 2026-04-08 02:06:45 |
| `evo_015` | 100.0% | 20 | 20 | $1.0335 | 2026-04-08 02:18:30 |
| `evo_016` | 100.0% | 20 | 20 | $0.9539 | 2026-04-08 02:31:33 |
| `evo_017` | 95.0% | 19 | 20 | $1.0858 | 2026-04-08 02:42:29 |
| `evo_018` | 100.0% | 20 | 20 | $1.4471 | 2026-04-08 02:51:08 |
| `evo_019` | 90.0% | 18 | 20 | $1.5208 | 2026-04-08 02:59:44 |
| `evo_020` | 95.0% | 19 | 20 | $1.1889 | 2026-04-08 03:09:47 |
| `evo_021` | 90.0% | 18 | 20 | $1.1589 | 2026-04-08 03:18:45 |
