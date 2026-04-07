"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 12 experiments. MLP_RATIO=3 was tried last and discarded.
LR schedule (FINAL_LR_FRAC, WARMUP_RATIO) and regularization (WEIGHT_DECAY,
ADAM_BETAS) remain completely unexplored.

NOTE: Only the hyperparameter block is shown here. The full training loop,
model architecture, optimizer setup (Muon + AdamW), and data pipeline are
in the complete train.py (omitted for brevity).
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH (controls model width)
HEAD_DIM = 128             # dimension per attention head
DEPTH = 6                  # number of transformer layers
MLP_RATIO = 4              # FFN hidden dim = MLP_RATIO * model_dim (ratio=3 tried and failed)

# Attention window pattern — "SSSL" = 3 sliding-window + 1 full-attention
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

WEIGHT_DECAY = 0.0         # L2 penalty — disabled at this scale
ADAM_BETAS = (0.8, 0.95)   # AdamW/Muon momentum params

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.0         # fraction of steps for linear LR warmup
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR

# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

n_kv_head = 6              # KV heads; equals n_head (GQA n_kv_head=1 tried and failed)

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# Already tried (do NOT repeat):
#   DEPTH 8, DEPTH 4, WINDOW_PATTERN L→SSSL, DEPTH 8+SSSL, WARMDOWN_RATIO 0.3,
#   WARMDOWN_RATIO 0.7 (kept), TOTAL_BATCH_SIZE halved, n_kv_head=1,
#   HEAD_DIM 64, MATRIX_LR 0.05, MLP_RATIO 3
#
# NOT YET TRIED (candidates):
#   FINAL_LR_FRAC  — currently 0.0; a small LR floor prevents over-decay
#   WARMUP_RATIO   — currently 0.0; brief warmup can help early stability
#   ADAM_BETAS     — currently (0.8, 0.95); tuning beta1/beta2 affects convergence
#   WEIGHT_DECAY   — currently 0.0; mild L2 regularization
#   EMBEDDING_LR   — currently 0.6; ratio to MATRIX_LR may be suboptimal
#   SCALAR_LR      — currently 0.5
#   ASPECT_RATIO   — currently 64; trades model width for depth
# ---------------------------------------------------------------------------

# [Full train.py continues here — omitted for brevity]
