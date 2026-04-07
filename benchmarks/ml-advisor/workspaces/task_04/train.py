"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: Same as task_03 — SSSL window pattern, warmdown=0.7, LR floor=0.
All experiments run from this checkpoint were discarded; this config is the
stable baseline that subsequent tasks branch from.

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

WARMUP_RATIO = 0.0         # fraction of steps for linear LR warmup (none here)
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay (kept from task_03)
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR (0 = full decay to zero)

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# WINDOW_PATTERN  — currently "SSSL"; experiments with other patterns discarded
# WARMDOWN_RATIO  — currently 0.7; experiments from this task were discarded
# FINAL_LR_FRAC   — next logical experiment: try 0.05 LR floor (see task_05)
# DEPTH / ASPECT_RATIO — scale model width vs depth trade-off
# TOTAL_BATCH_SIZE — larger batches smooth gradients; smaller = more updates
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
