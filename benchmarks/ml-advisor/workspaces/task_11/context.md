# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 5 experiments)
- Depth: 6, SSSL window pattern (kept)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0%
- Best val_bpb so far: 1.0961

## Key Learnings
- Depth 8 hurt (fewer steps in time budget)
- Depth 8 + SSSL also hurt (combined still worse)
- Depth 4 hurt badly (model too small)
- SSSL window attention improved over full attention

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
DEPTH changes have been tried in both directions (deeper AND shallower) and ALL failed. Avoid DEPTH.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
