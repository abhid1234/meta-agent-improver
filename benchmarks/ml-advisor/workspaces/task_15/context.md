# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 8 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens (halving was tried and failed)
- Warmdown ratio: 0.7
- LR floor: 0%
- Best val_bpb so far: 1.0960

## Key Learnings
- Depth changes hurt in both directions on budget GPU
- SSSL window attention helped
- Warmdown 0.7 is the sweet spot (0.3 worse, 0.5 baseline)
- Halving batch size hurt — more steps but noisier gradients, net negative
- Batch size changes look unpromising — gradient noise cancels out the extra steps

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json.
Batch size and depth are exhausted. Warmdown is tuned. Focus on unexplored knobs.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
