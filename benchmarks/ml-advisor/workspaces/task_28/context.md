# ML Experiment Advisor Task

## Setup
- **Hardware:** NVIDIA A40 (48GB VRAM) — budget GPU at $0.40/hr
- **Model:** GPT-style transformer, ~26M parameters
- **Training budget:** 5 minutes wall clock per experiment
- **Metric:** val_bpb (validation bits per byte) — lower is better
- **Constraint:** Must fit in 48GB VRAM. Cannot change prepare.py or evaluation.

## Current State (after 19 experiments)
- Depth: 6, SSSL window pattern
- Batch size: 131K tokens
- Warmdown ratio: 0.7
- LR floor: 5% (FINAL_LR_FRAC=0.05)
- Weight decay: 0.01
- Warmup ratio: 0.05 (just added — small warmup stabilizes early training)
- Embedding LR: 0.6
- HEAD_DIM: 128
- n_kv_head: 6
- Matrix LR: 0.04
- ADAM_BETAS: (0.8, 0.95)
- Best val_bpb so far: 1.0940

## Key Learnings
- Depth changes hurt on budget GPU
- SSSL > L > S for window attention
- Warmdown 0.7 is sweet spot (0.3, 0.5, 0.8 all worse)
- LR floor 5% prevents over-annealing — major discovery
- LR floor 10% too high
- MLP ratio 3 lost too much capacity
- GQA (n_kv_head=1) too aggressive
- HEAD_DIM 64 worse than 128
- Matrix LR 0.05 marginal worse than 0.04
- Batch halving: net negative
- Weight decay 0.01 gave consistent small gain (kept)
- Embedding LR 0.8 too aggressive — reverted to 0.6
- Warmup 0.05 helps stabilize early training (newest keeper)
- LR schedule now well-tuned: warmup + cosine + floor all configured
- Remaining untried: SCALAR_LR, UNEMBEDDING_LR, ASPECT_RATIO, ADAM_BETAS

## Your Task
Read results.tsv and train.py. Propose the single best next hyperparameter change as proposal.json. This is a very late-stage task — 19 experiments completed. LR schedule is now fully configured. Attention, depth, batch, and MLP are exhausted. Look at truly untried parameters: SCALAR_LR, UNEMBEDDING_LR, ASPECT_RATIO, or ADAM_BETAS.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
