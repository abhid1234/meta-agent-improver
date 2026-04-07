"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 16 experiments. FINAL_LR_FRAC=0.05 was adopted (exp 15);
FINAL_LR_FRAC=0.10 was then tried and failed (exp 16). This is the most
advanced state: 16 experiments complete. Remaining unexplored knobs are
WARMUP_RATIO, ADAM_BETAS, WEIGHT_DECAY, EMBEDDING_LR, SCALAR_LR, ASPECT_RATIO.

NOTE: Only the hyperparameter block is shown here.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH; never tuned
HEAD_DIM = 128             # HEAD_DIM 64 tried and failed
DEPTH = 6                  # DEPTH 4 and 8 both tried and failed
MLP_RATIO = 4              # MLP_RATIO 3 tried and failed

# SSSL is optimal. L, S, SSSL all tested.
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
UNEMBEDDING_LR = 0.004     # output projection — never tuned
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
WARMDOWN_RATIO = 0.7       # cosine decay — 0.3/0.5/0.7(kept)/0.8 all tested
FINAL_LR_FRAC = 0.05       # LR floor — 0.05 kept; 0.10 tried and failed

# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

n_kv_head = 6              # GQA (n_kv_head=1) tried and failed

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# Already tried — DO NOT REPEAT ANY OF THESE:
#   DEPTH: 4, 8 (both failed; 6 kept)
#   WINDOW_PATTERN: L, SSSL (kept), S (failed)
#   WARMDOWN_RATIO: 0.3, 0.5, 0.7 (kept), 0.8
#   TOTAL_BATCH_SIZE: halved (failed)
#   n_kv_head: 1 (GQA, failed)
#   HEAD_DIM: 64 (failed)
#   MATRIX_LR: 0.05 (failed)
#   MLP_RATIO: 3 (failed)
#   FINAL_LR_FRAC: 0.05 (kept), 0.10 (failed)
#
# NOT YET TRIED — all novel directions:
#   WARMUP_RATIO   — 0.0 → 0.05 (brief warmup for early stability)
#   ADAM_BETAS     — (0.8, 0.95) → tune beta1 or beta2
#   WEIGHT_DECAY   — 0.0 → 0.01–0.1 (L2 regularization)
#   EMBEDDING_LR   — 0.6 → adjust embedding learning rate
#   SCALAR_LR      — 0.5 → adjust layernorm/bias LR
#   UNEMBEDDING_LR — 0.004 → adjust
#   ASPECT_RATIO   — 64 → wider or narrower model
# ---------------------------------------------------------------------------

# [Full train.py continues here — omitted for brevity]
