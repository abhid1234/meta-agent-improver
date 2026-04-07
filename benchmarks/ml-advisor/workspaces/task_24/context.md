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
- WEIGHT_DECAY: 0.0 (disabled)
- Best val_bpb so far: 1.0949

## Key Learnings
- Depth changes hurt (both 4 and 8 worse than 6)
- SSSL window attention: best pattern found
- Warmdown 0.7: sweet spot
- Halving batch: worse
- GQA (n_kv_head=1): worse
- HEAD_DIM 64: worse
- Matrix LR 0.05: marginally worse
- MLP ratio 3: worse
- LR floor 5%: current best improvement
- LR floor 10%: worse than 5%
- WEIGHT_DECAY is currently 0 — regularization is completely off

## Your Task
You are an ML experiment advisor specializing in **regularization**. All architecture, capacity, and warmdown experiments have been run. The regularization area is completely unexplored.

Focus your proposal on regularization: weight decay (WEIGHT_DECAY), optimizer momentum (ADAM_BETAS beta2 controls effective regularization), or any regularization-adjacent change visible in train.py. 

Propose the single best next experiment in the regularization space.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
