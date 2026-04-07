"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 13 experiments. Warmdown 0.8 tried and failed; warmdown
search is now exhausted (0.3, 0.5, 0.7, 0.8 all tested). LR schedule knobs
beyond WARMDOWN_RATIO (FINAL_LR_FRAC, WARMUP_RATIO) and regularization
(WEIGHT_DECAY, ADAM_BETAS) remain completely unexplored.

NOTE: Only the hyperparameter block is shown here. Full training loop,
model architecture, optimizer, and data pipeline omitted for brevity.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH
HEAD_DIM = 128             # dimension per attention head
DEPTH = 6                  # number of transformer layers
MLP_RATIO = 4              # FFN hidden dim = MLP_RATIO * model_dim

# Attention window pattern — SSSL is optimal; L, S, and SSSL all tested
WINDOW_PATTERN = "SSSL"

# ---------------------------------------------------------------------------
# Batch and sequence
# ---------------------------------------------------------------------------

TOTAL_BATCH_SIZE = 2**17   # ~131K tokens per gradient step
DEVICE_BATCH_SIZE = 64     # tokens per forward pass per device

# ---------------------------------------------------------------------------
# Learning rates (per parameter group)
# ---------------------------------------------------------------------------

EMBEDDING_LR = 0.6         # embedding table
UNEMBEDDING_LR = 0.004     # output projection / unembedding matrix
MATRIX_LR = 0.04           # weight matrices in attention and MLP
SCALAR_LR = 0.5            # scalar params (biases, layernorm gains)

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.0         # L2 penalty — disabled; never tried non-zero
ADAM_BETAS = (0.8, 0.95)   # AdamW/Muon momentum params; never tuned

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.0         # fraction of steps for linear LR warmup; never tried
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay — exhausted
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR; never tried

# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

n_kv_head = 6              # KV heads; GQA (n_kv_head=1) tried and failed

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# Already tried (do NOT repeat):
#   DEPTH 8, DEPTH 4, WINDOW_PATTERN L/S/SSSL, DEPTH 8+SSSL, WARMDOWN_RATIO 0.3/0.5/0.8,
#   WARMDOWN_RATIO 0.7 (kept), TOTAL_BATCH_SIZE halved, n_kv_head=1,
#   HEAD_DIM 64, MATRIX_LR 0.05, MLP_RATIO 3
#
# NOT YET TRIED (candidates):
#   FINAL_LR_FRAC  — currently 0.0; non-zero floor can help final convergence
#   WARMUP_RATIO   — currently 0.0; brief warmup stabilizes early training
#   ADAM_BETAS     — currently (0.8, 0.95); unexplored
#   WEIGHT_DECAY   — currently 0.0; mild regularization never tried
#   EMBEDDING_LR   — currently 0.6
#   SCALAR_LR      — currently 0.5
#   ASPECT_RATIO   — currently 64
# ---------------------------------------------------------------------------

# [Full train.py continues here — omitted for brevity]
