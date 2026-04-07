# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 7 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7 (kept — improved over 0.5, 0.3 was worse)
- LR floor: 0%
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth 8 hurt (fewer steps on budget GPU), depth 4 too small
- SSSL window attention helped (cheaper compute = more training steps)
- Warmdown 0.7 > 0.5 > 0.3 (longer decay helps)
- Architecture changes on budget GPU are risky — fewer steps hurts more than capacity helps

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
