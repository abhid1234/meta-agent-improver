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
- SSSL window attention improved over full attention (kept)
- Depth changes in both directions failed (depth 8 worse, depth 4 much worse)
- The results.tsv rows are not in chronological order — read all rows carefully

## Your Task
Read results.tsv and train.py. The results.tsv rows may not be in experiment order — read ALL
rows to understand the full history before proposing. Propose the single best next hyperparameter
change as proposal.json.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
