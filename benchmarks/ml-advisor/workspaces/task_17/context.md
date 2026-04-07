# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 10 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 0%
- HEAD_DIM: 128 (reducing to 64 was tried and failed)
- n_kv_head: 6
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt in both directions on budget GPU
- SSSL window attention helped (adopted)
- Warmdown 0.7 is the sweet spot
- Halving batch size failed (noisier gradients)
- GQA (n_kv_head=1) too aggressive for small model
- HEAD_DIM 64 worse than 128 — reduces attention quality
- Most architecture knobs have been explored; optimization/schedule changes remain

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Architecture changes have largely been exhausted. Focus on LR schedule parameters that haven't
been tried. Do not repeat any previously-failed direction.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
