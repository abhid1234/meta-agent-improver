# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 11 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens (halving was tried and failed)
- Warmdown ratio: 0.7
- LR floor: 0%
- HEAD_DIM: 128
- n_kv_head: 6 (same as n_head, GQA failed)
- Matrix LR: 0.04
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt on budget GPU (fewer steps > more capacity)
- SSSL window attention helped
- Warmdown 0.7 is sweet spot (0.3 and 0.5 worse)
- Halving batch = noisier gradients, net negative
- GQA too aggressive for 3-head model
- HEAD_DIM 64 worse than 128
- Matrix LR 0.05 marginally worse than 0.04
- Most architecture changes have been exhausted — try optimization/schedule changes

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
