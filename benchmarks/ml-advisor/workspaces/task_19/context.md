# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 12 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens (halving was tried and failed)
- Warmdown ratio: 0.7
- LR floor: 0%
- HEAD_DIM: 128
- n_kv_head: 6 (same as n_head, GQA failed)
- Matrix LR: 0.04
- MLP ratio: 4 (ratio=3 tried and failed)
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt on budget GPU (more steps matter more than capacity)
- SSSL window attention improved over full attention
- Warmdown 0.7 is sweet spot (0.3, 0.5 worse; higher not yet tried)
- Halving batch = noisier gradients, net negative
- GQA too aggressive for this model size
- HEAD_DIM 64 worse than 128
- Matrix LR 0.05 marginally worse than 0.04
- MLP ratio 3 slightly worse than 4
- Both larger and smaller MLP tried — MLP ratio is exhausted
- Architecture changes mostly exhausted — focus on schedule and optimization

## Your Task
You are an ML experiment advisor. Most of the obvious changes have already been tried — both architectural and MLP capacity changes failed. Read results.tsv to see the full history, and read train.py for the list of tunable hyperparameters.

Propose the single best next hyperparameter change that has NOT yet been tried. Avoid changes that have already been attempted.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
