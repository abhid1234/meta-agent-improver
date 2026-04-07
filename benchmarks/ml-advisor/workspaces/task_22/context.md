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
- SSSL window attention: best pattern; all-short (S) and full (L) both worse
- Warmdown 0.7 sweet spot (0.3, 0.5, 0.8 all worse)
- Halving batch size: worse
- GQA (n_kv_head=1): worse
- HEAD_DIM 64: worse
- Matrix LR 0.05: worse
- MLP ratio 3: worse
- LR floor 5%: improvement (current best)
- LR floor 10%: worse than 5%
- Virtually all standard knobs have been tried. The search space is nearly exhausted.

## Your Task
You are an ML experiment advisor. All 16 experiments so far have been run. Review results.tsv carefully — every change listed there has been tried. Read train.py for the complete list of hyperparameters.

Propose the single best NOVEL next experiment — one that introduces a parameter or direction that has NOT appeared anywhere in results.tsv.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
