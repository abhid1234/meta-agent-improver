"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 11 experiments. Current best is warmdown=0.7 + SSSL pattern.
Matrix LR 0.05 was tried last and discarded; HEAD_DIM 64 and GQA also failed.
LR schedule (FINAL_LR_FRAC, WARMUP_RATIO) and regularization (WEIGHT_DECAY,
ADAM_BETAS) remain completely unexplored.

NOTE: Only the hyperparameter block is shown here. The full training loop,
model architecture (GPT with configurable attention patterns), optimizer setup
(Muon + AdamW), and data pipeline are in the complete train.py (omitted for
brevity). Everything below is tunable without touching model or loop code.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH (controls model width)
HEAD_DIM = 128             # dimension per attention head
DEPTH = 6                  # number of transformer layers
MLP_RATIO = 4              # FFN hidden dim = MLP_RATIO * model_dim

# Attention window pattern — "SSSL" = 3 sliding-window + 1 full-attention,
# tiled to match DEPTH. Adopted for memory efficiency.
WINDOW_PATTERN = "SSSL"

# ---------------------------------------------------------------------------
# Batch and sequence
# ---------------------------------------------------------------------------

TOTAL_BATCH_SIZE = 2**17   # ~131K tokens per gradient step (across all devices)
DEVICE_BATCH_SIZE = 64     # tokens per forward pass per device; grad accum fills the rest

# ---------------------------------------------------------------------------
# Learning rates (per parameter group)
# ---------------------------------------------------------------------------

EMBEDDING_LR = 0.6         # embedding table (high LR — embeddings are low-rank)
UNEMBEDDING_LR = 0.004     # output projection / unembedding matrix
MATRIX_LR = 0.04           # weight matrices in attention and MLP
SCALAR_LR = 0.5            # scalar params (biases, layernorm gains)

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.0         # L2 penalty — disabled at this scale
ADAM_BETAS = (0.8, 0.95)   # AdamW/Muon momentum params; low beta1 for fast adaptation

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.0         # fraction of steps for linear LR warmup (none currently)
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR (0 = full decay to zero)

# ---------------------------------------------------------------------------
# Attention
# ---------------------------------------------------------------------------

n_kv_head = 6              # KV heads for GQA; equals n_head (full MHA); GQA(1) was tried and failed

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# Already tried (do NOT repeat):
#   DEPTH 8, DEPTH 4, WINDOW_PATTERN "L"→"SSSL", DEPTH 8+SSSL, WARMDOWN_RATIO 0.3,
#   WARMDOWN_RATIO 0.5→0.7 (kept), TOTAL_BATCH_SIZE halved, n_kv_head=1,
#   HEAD_DIM 64, MATRIX_LR 0.05
#
# NOT YET TRIED (candidates):
#   FINAL_LR_FRAC  — currently 0.0; adding a small LR floor often helps
#   WARMUP_RATIO   — currently 0.0; even brief warmup can stabilize early training
#   ADAM_BETAS     — currently (0.8, 0.95); beta1/beta2 affect convergence speed
#   WEIGHT_DECAY   — currently 0.0; mild L2 can regularize at this scale
#   EMBEDDING_LR   — currently 0.6; relative to MATRIX_LR may be tunable
#   SCALAR_LR      — currently 0.5; layernorm/bias LR
#   ASPECT_RATIO   — currently 64; trades width vs depth at fixed DEPTH=6
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
