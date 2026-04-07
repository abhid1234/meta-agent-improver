# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 9 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 0%
- n_kv_head: 6 (GQA with n_kv_head=1 was tried and failed)
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt in both directions
- SSSL window attention helped
- Warmdown 0.7 is the sweet spot
- Halving batch size failed (noisier gradients)
- GQA (n_kv_head=1) was too aggressive for this small model — hurt attention quality

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Architecture and batch changes look exhausted. The LR floor (FINAL_LR_FRAC) hasn't been explored.
Don't repeat failed directions.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
