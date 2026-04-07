# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr (NOT an H100)
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment — fixed wall-clock, not fixed steps
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State
- Depth: 6, full attention (L pattern)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0% (decays to zero)
- Only baseline run completed so far

## Hardware Context
This is a **budget A40 GPU** at $0.40/hr, not a high-end H100. The training budget is
**5 minutes wall clock** per experiment. This means:
- More parameters → fewer training steps in the same time window → often hurts
- Compute-efficient changes (reduce flops per step) are usually better than adding capacity
- The model is already at ~26M params; scaling up is risky under a fixed time budget

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Given the hardware constraints, prefer changes that either save compute or improve the LR schedule
over changes that add model capacity.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
