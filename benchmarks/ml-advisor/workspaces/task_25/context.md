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
- 16 experiments run. Every standard knob has been touched.
- Depth (4, 6, 8): 6 is best
- Window patterns (L, S, SSSL): SSSL is best
- Warmdown (0.3, 0.5, 0.7, 0.8): 0.7 is best
- Batch size halving: worse
- GQA: worse
- HEAD_DIM 64: worse
- Matrix LR 0.05: worse
- MLP ratio 3: worse
- LR floor 5%: only clear win; 10% worse
- Standard optimization is plateaued

## Your Task
You are an ML experiment advisor. 16 experiments have been run and progress has stalled. It's time for a **Hail Mary** — propose something unconventional, bold, or exploratory that has not been tried at all. 

Do not propose anything that appears in results.tsv. Think outside the standard checklist: consider optimizer parameters, per-group learning rates, sequence length, aspect ratio changes, or anything else in train.py that hasn't been touched.

Propose the single most promising novel experiment.

## proposal.json Format
```json
{
  "parameter": "the parameter to change",
  "old_value": "current value",
  "new_value": "proposed value",
  "rationale": "why this change should improve val_bpb"
}
```
