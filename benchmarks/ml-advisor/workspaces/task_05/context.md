# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 15 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% (FINAL_LR_FRAC=0.05) — best single improvement
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04
- Best val_bpb so far: 1.0949

## Key Learnings
- Depth changes hurt on budget GPU
- SSSL > L > S for window attention
- Warmdown 0.7 is sweet spot
- LR floor 5% prevents over-annealing (best discovery)
- LR floor 10% too high
- MLP ratio 3 lost too much capacity
- Most obvious hyperparameters explored — need creative ideas
- Budget GPU constraint means "more compute-efficient" > "more capacity"

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json. This is a late-stage task — most obvious changes have been tried.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
