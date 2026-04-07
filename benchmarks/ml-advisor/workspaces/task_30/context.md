# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 21 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% (FINAL_LR_FRAC=0.05)
- Weight decay: 0.01
- Warmup ratio: 0.05
- Embedding LR: 0.6
- Unembedding LR: 0.004
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04 (reducing to 0.03 was just tried and failed)
- SCALAR_LR: 0.5
- ADAM_BETAS: (0.8, 0.95)
- ASPECT_RATIO: 64
- Best val_bpb so far: 1.0940

## Key Learnings
- Depth changes hurt on budget GPU (6 is sweet spot; 4, 8 both worse)
- SSSL > L > S for window attention
- Warmdown 0.7 is sweet spot (0.3, 0.5, 0.8 all worse)
- LR floor 5% prevents over-annealing — biggest gain
- LR floor 10% too high
- MLP ratio 3 lost too much capacity
- GQA (n_kv_head=1) too aggressive for 6-head model
- HEAD_DIM 64 worse than 128
- Matrix LR: 0.05 marginal worse; 0.03 also worse — 0.04 is sweet spot
- Batch halving: noisier gradients, net negative
- Weight decay 0.01 gave small consistent gain
- Embedding LR 0.8 too aggressive — reverted to 0.6
- Warmup 0.05 stabilizes early training (kept)
- ADAM_BETAS beta1 0.85 not clearly better than 0.8 (discarded)
- Matrix LR 0.03 slower learning, net negative (most recent failure)
- EXHAUSTED: depth, attention window, batch size, warmdown, LR floor, MLP ratio, GQA, HEAD_DIM, matrix LR, embedding LR, weight decay, warmup, adam betas
- REMAINING UNTRIED: SCALAR_LR adjustment, UNEMBEDDING_LR adjustment, ASPECT_RATIO change

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json. This is the hardest task — 21 experiments completed. Nearly every obvious direction has been tried. Only truly novel ideas remain viable: SCALAR_LR, UNEMBEDDING_LR, or ASPECT_RATIO. Do NOT repeat any failed direction.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
