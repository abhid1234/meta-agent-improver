# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 17 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% (FINAL_LR_FRAC=0.05)
- Weight decay: 0.01 (just added — small regularization helped)
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04
- Warmup ratio: 0.0
- ADAM_BETAS: (0.8, 0.95)
- Best val_bpb so far: 1.0945

## Key Learnings
- Depth changes hurt on budget GPU (fewer steps > more capacity)
- SSSL > L > S for window attention
- Warmdown 0.7 is sweet spot (0.3, 0.5, 0.8 all worse)
- LR floor 5% prevents over-annealing — best discovery so far
- LR floor 10% too high
- MLP ratio 3 lost too much capacity
- GQA (n_kv_head=1) too aggressive — attention degraded
- HEAD_DIM 64 worse than 128
- Matrix LR: 0.05 marginal worse than 0.04; lower may also hurt
- Batch halving noisier gradients — net negative
- Weight decay 0.01 gave small but consistent gain (newest keeper)
- Most obvious hyperparameters explored — focus on untried schedule/optimizer params
- Budget GPU constraint: "more compute-efficient" > "more capacity"

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json. This is a very late-stage task — 17 experiments completed. Most obvious changes have been tried. Look for untried schedule or optimizer parameters.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
