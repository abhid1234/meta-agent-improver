"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 10 experiments — SSSL adopted, warmdown=0.7 adopted. Batch
halving failed. GQA (n_kv_head=1) failed. HEAD_DIM 64 failed (attention
quality degraded). Most architecture knobs tried. Current best: 1.0960.

NOTE: Only the hyperparameter block is shown here. The full training loop,
model architecture (GPT with configurable attention patterns), optimizer setup
(Muon + AdamW), and data pipeline are in the complete train.py (omitted for
brevity). Everything below is tunable without touching model or loop code.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH (controls model width)
HEAD_DIM = 128             # dimension per attention head (64 was tried, failed)
DEPTH = 6                  # number of transformer layers
MLP_RATIO = 4              # MLP hidden size = MLP_RATIO * model_dim
n_kv_head = 6              # KV heads; GQA (n_kv_head=1) was tried and failed

# Attention window pattern — "SSSL" = 3 sliding-window + 1 full-attention.
WINDOW_PATTERN = "SSSL"

# ---------------------------------------------------------------------------
# Batch and sequence
# ---------------------------------------------------------------------------

TOTAL_BATCH_SIZE = 2**17   # ~131K tokens per gradient step (halving failed)
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

WARMUP_RATIO = 0.0         # fraction of steps for linear LR warmup (none here)
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay (adopted)
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR — unexplored, try 0.05

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# FINAL_LR_FRAC   — currently 0; try 0.05 to prevent over-annealing (key unexplored lever)
# WARMDOWN_RATIO  — 0.7 adopted; further tuning may yield marginal gains
# WINDOW_PATTERN  — "SSSL" adopted; L worse, S untested
# DEPTH           — AVOID: failed in both directions
# TOTAL_BATCH_SIZE — AVOID: halving failed
# n_kv_head       — AVOID: n_kv_head=1 failed
# HEAD_DIM        — AVOID: 64 failed
# MLP_RATIO       — controls MLP capacity (untested in this series)
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
