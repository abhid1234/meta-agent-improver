# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 6 experiments)
- Depth: 6, SSSL window pattern (kept)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0%
- Best val_bpb so far: 1.0961

## Key Learnings
- Depth changes hurt in both directions on budget GPU
- SSSL window attention improved over full attention
- Warmdown 0.3 (shorter) hurt — decay period was too short
- Warmdown direction: longer is likely better than shorter

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Warmdown 0.3 has been tried and failed — do NOT propose warmdown 0.3. Consider whether longer
warmdown (e.g., 0.7) or a different parameter class might help.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
