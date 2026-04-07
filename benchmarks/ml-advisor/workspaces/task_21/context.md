# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 14 experiments)
- Depth: 6, SSSL window pattern (all-short pattern "S" also tried and failed)
- Batch size: 131K tokens (halving was tried and failed)
- Warmdown ratio: 0.7 (0.3, 0.5, 0.8 all tried and failed)
- LR floor: 0%
- HEAD_DIM: 128
- n_kv_head: 6 (same as n_head, GQA failed)
- Matrix LR: 0.04
- MLP ratio: 4 (ratio=3 tried and failed)
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt on budget GPU
- SSSL window attention improved; all-short (S) pattern slightly worse than SSSL
- Window pattern experiments exhausted — SSSL is optimal
- Warmdown 0.7 is sweet spot (0.3, 0.5, 0.8 all worse)
- Halving batch = noisier gradients, net negative
- GQA too aggressive for this model size
- HEAD_DIM 64 worse than 128
- Matrix LR 0.05 marginally worse than 0.04
- MLP ratio 3 slightly worse than 4
- Most knobs in architecture, attention, and warmdown are exhausted
- Remaining unexplored: LR floor, WARMUP_RATIO, EMBEDDING_LR, ADAM_BETAS, WEIGHT_DECAY, SCALAR_LR

## Your Task
You are an ML experiment advisor. Architecture changes, attention patterns, MLP capacity, and warmdown schedule have all been thoroughly explored. Read results.tsv to confirm what has been tried, and read train.py for remaining tunable knobs.

Propose the single best next hyperparameter change that has NOT yet been tried.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
