"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 14 experiments. Window pattern "S" (all short) tried and
failed last. All attention patterns tested; architecture, MLP, and warmdown
search all exhausted. Unexplored: FINAL_LR_FRAC, WARMUP_RATIO, ADAM_BETAS,
WEIGHT_DECAY, EMBEDDING_LR, SCALAR_LR, ASPECT_RATIO.

NOTE: Only the hyperparameter block is shown here.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH; never tuned
HEAD_DIM = 128             # HEAD_DIM 64 was tried and failed
DEPTH = 6                  # DEPTH 4 and 8 both tried and failed
MLP_RATIO = 4              # MLP_RATIO 3 tried and failed

# SSSL is optimal. Tried: L (baseline full attention), SSSL (kept), S (failed).
WINDOW_PATTERN = "SSSL"

# ---------------------------------------------------------------------------
# Batch and sequence
# ---------------------------------------------------------------------------

TOTAL_BATCH_SIZE = 2**17   # ~131K tokens per gradient step
DEVICE_BATCH_SIZE = 64     # tokens per forward pass per device

# ---------------------------------------------------------------------------
# Learning rates (per parameter group)
# ---------------------------------------------------------------------------

EMBEDDING_LR = 0.6         # embedding table — never tuned
UNEMBEDDING_LR = 0.004     # output projection
MATRIX_LR = 0.04           # attention + MLP matrices (0.05 tried and failed)
SCALAR_LR = 0.5            # biases, layernorm gains — never tuned

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.0         # L2 penalty — never tried non-zero
ADAM_BETAS = (0.8, 0.95)   # momentum params — never tuned

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.0         # linear warmup fraction — never tried
WARMDOWN_RATIO = 0.7       # cosine decay fraction — 0.3/0.5/0.8 all tried/failed
FINAL_LR_FRAC = 0.0        # LR floor fraction — never tried; strong candidate

# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

n_kv_head = 6              # GQA (n_kv_head=1) tried and failed

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# Already tried (do NOT repeat):
#   DEPTH 8, DEPTH 4, WINDOW_PATTERN L/SSSL(kept)/S, DEPTH 8+SSSL,
#   WARMDOWN_RATIO 0.3/0.5/0.7(kept)/0.8, TOTAL_BATCH_SIZE halved,
#   n_kv_head=1, HEAD_DIM 64, MATRIX_LR 0.05, MLP_RATIO 3
#
# NOT YET TRIED — strong candidates:
#   FINAL_LR_FRAC  — 0.0 → 0.05 or 0.1 (prevent over-decay at end of training)
#   WARMUP_RATIO   — 0.0 → 0.05 (brief warmup for early stability)
#   ADAM_BETAS     — (0.8, 0.95) → adjust beta1 or beta2
#   WEIGHT_DECAY   — 0.0 → 0.01–0.1 (mild regularization)
#   EMBEDDING_LR   — 0.6 → adjust relative to MATRIX_LR
#   SCALAR_LR      — 0.5 → adjust
#   ASPECT_RATIO   — 64 → wider or narrower model at fixed depth
# ---------------------------------------------------------------------------

# [Full train.py continues here — omitted for brevity]
