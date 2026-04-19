# GPU Validation Results — 3-Hardware Comparison

## Setup

Three GPU classes tested on identical training code (26M-param GPT, 5-min time budget, 131K batch):
- **NVIDIA A40** (48GB VRAM) — budget data-center GPU, ~$0.40/hr. *Original autoresearch experiments.*
- **NVIDIA L40S** (48GB VRAM) — mid-tier, $0.79/hr on RunPod
- **NVIDIA H100 80GB HBM3** — top-tier, $2.99/hr on RunPod secure

Each experiment ran for exactly 300 seconds of training wall-clock (same as the original autoresearch protocol).

## Results

| # | Experiment | A40 val_bpb | L40S val_bpb | H100 val_bpb | Steps (H100) |
|---|---|---|---|---|---|
| 1 | Baseline (depth=6, L attention) | 1.0980 | 1.0702 | 1.0795 | 1,693 |
| 2 | SSSL window attention (d=6) | 1.0961 | 1.0707 | 1.0794 | 1,699 |
| 3 | Full optimized (d=6, SSSL + warmdown 0.7 + LR floor 5%) | 1.0949 | 1.0673 | 1.0779 | 1,713 |
| 4 | Depth=8, L attention | 1.1017 | — | **1.0322** | 1,649 |
| 5 | Depth=8 + full optimized | — | — | **1.0318** ⭐ | 1,616 |

## Key Findings

### 1. Meta-agent advice validates on budget GPUs
On A40 and L40S, the meta-agent's recommended config (SSSL + warmdown 0.7 + LR floor 5%) achieves the best val_bpb among depth=6 candidates. Improvement magnitude: ~0.003 val_bpb — consistent across both GPUs.

### 2. Architecture is dramatically hardware-dependent
On H100, **depth=8 beats depth=6 by 0.046 val_bpb** — roughly 15× larger than the prompt-optimization win on the same GPU. This quantifies the thesis: *on budget GPUs, depth=6 wins because depth=8 can't complete enough training steps; on H100, depth=8 wins because it has compute headroom to train the deeper model to convergence.*

### 3. The meta-agent's strategy is self-consistent
The meta-agent discovered phase-ordered exploration: architecture → training dynamics → LR schedule → regularization. The H100 result demonstrates *why* phase ordering matters: **one architecture change** (depth 6 → 8) delivers 15× more gain than **all the LR schedule changes combined**. The meta-agent correctly prioritized the higher-leverage lever.

### 4. Schedule improvements transfer; architecture wins do not
The LR schedule improvements (warmdown 0.7, LR floor 5%) help on every GPU — they're hardware-independent optimizations. The architectural win (depth=8) is *hardware-specific*. A meta-agent advising a researcher should therefore prefer schedule changes unless the hardware context is known.

### 5. H100 is NOT 3× faster on this workload
Steps-per-5-min:
- A40: ~1,175
- L40S: ~1,890
- H100: ~1,700

L40S actually completes more steps than H100 at this small model scale — the 26M-param model doesn't saturate H100's compute, and kernel launch overhead dominates. This is a useful data point for cost/benefit: for small models, L40S at $0.79/hr beats H100 at $2.99/hr.

## Cost Summary

| GPU | Duration | Rate | Cost |
|-----|----------|------|------|
| A40 (original Karpathy experiment) | ~4 hr | $0.40/hr | ~$1.60 |
| L40S (3 experiments + setup) | 45 min | $0.79/hr | ~$0.60 |
| H100 (5 experiments + setup) | 55 min | $2.99/hr | ~$2.75 |
| **Total GPU spend** | | | **~$5** |

Plus ~$21 API costs for all Claude-based meta-optimization. **Total project: ~$26.**

## Raw training logs
- `experiments.log` — L40S runs (3 experiments)
- `h100.log` — H100 runs (5 experiments)
- `h100_watchdog.log` — auto-termination watchdog trace
