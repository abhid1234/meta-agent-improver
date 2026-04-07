# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 4 experiments)
- Depth: 6, SSSL window pattern (kept)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0%
- Best val_bpb so far: 1.0961

## Key Learnings
- Depth 8 hurt performance — even with SSSL, more layers means fewer steps in the time budget
- Depth 8 + SSSL also failed (tried as a combination)
- SSSL window attention improved over full attention L

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
The depth direction has been tested both with and without SSSL and failed both times. Do not revisit it.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
