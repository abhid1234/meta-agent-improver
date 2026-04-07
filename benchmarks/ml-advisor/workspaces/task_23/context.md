# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 16 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% of peak (FINAL_LR_FRAC=0.05)
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04
- MLP ratio: 4
- Best val_bpb so far: 1.0949

## Key Learnings
- Depth changes hurt (both 4 and 8 worse than 6)
- SSSL window attention: best pattern found
- Warmdown 0.7: sweet spot; 0.3, 0.5, 0.8 all worse
- Halving batch: worse
- GQA (n_kv_head=1): worse
- HEAD_DIM 64: worse
- Matrix LR 0.05: marginally worse
- MLP ratio 3: worse
- LR floor 5%: current best improvement
- LR floor 10%: worse than 5%
- Architecture and capacity changes have been exhausted

## Your Task
You are an ML experiment advisor specializing in **learning rate schedules**. All standard architecture and capacity experiments have been run. The LR schedule area still has unexplored territory.

Focus your proposal on the LR schedule: warmup phase, per-group LR ratios (EMBEDDING_LR, SCALAR_LR vs MATRIX_LR), or optimizer momentum parameters (ADAM_BETAS). Read train.py carefully for all available schedule-related knobs.

Propose the single best next experiment targeting the LR schedule that has NOT yet been tried.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
