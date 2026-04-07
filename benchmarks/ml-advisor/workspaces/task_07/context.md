# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 2 experiments)
- Depth: 6, full attention (L pattern)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0%
- Best val_bpb so far: 1.0980

## Key Learnings
- Increasing depth to 8 hurt performance — the A40 is a budget GPU with a 5-minute wall clock
  budget; more parameters means fewer training steps, which outweighs any capacity gain

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Use the experiment history to avoid directions already shown to hurt.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
