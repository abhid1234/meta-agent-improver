# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 20 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% (FINAL_LR_FRAC=0.05)
- Weight decay: 0.01
- Warmup ratio: 0.05
- Embedding LR: 0.6
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04
- ADAM_BETAS: (0.8, 0.95) — raising beta1 to 0.85 was just tried and failed
- Best val_bpb so far: 1.0940

## Key Learnings
- Depth changes hurt on budget GPU
- SSSL > L > S for window attention
- Warmdown 0.7 is sweet spot (0.3, 0.5, 0.8 all worse)
- LR floor 5% prevents over-annealing
- LR floor 10% too high
- MLP ratio 3 lost too much capacity
- GQA (n_kv_head=1) too aggressive
- HEAD_DIM 64 worse than 128
- Matrix LR 0.05 marginal worse than 0.04; lower likely also hurts
- Batch halving: net negative
- Weight decay 0.01 gave small consistent gain (kept)
- Embedding LR 0.8 too aggressive (tried, failed)
- Warmup 0.05 helps early training stability (kept)
- ADAM_BETAS: beta1 0.85 marginal vs 0.8 — not clearly better, discarded
- ADAM_BETAS direction now explored — avoid further beta1 changes
- Remaining untried: SCALAR_LR, UNEMBEDDING_LR, ASPECT_RATIO

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json. This is a very late-stage task — 20 experiments completed. ADAM_BETAS changes have been tried. Avoid repeating failures. Focus on the few remaining untried parameters: SCALAR_LR, UNEMBEDDING_LR, or ASPECT_RATIO.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
