# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State
- Depth: 6, full attention (L pattern)
- Batch size: 131K tokens
- Warmdown ratio: 0.5
- LR floor: 0% (decays to zero)
- Only baseline run completed so far

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
