"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM, $0.40/hr).

Task state: Baseline — full attention (L), depth=6, batch=131K, warmdown=0.5,
LR floor=0 (no floor). Only the baseline has been run so far.

IMPORTANT: This is a BUDGET GPU setup. Training budget is 5 minutes WALL CLOCK
per experiment — not a fixed number of steps. Changes that add parameters or
increase compute per step will result in fewer total training steps in the budget,
which on a small model often hurts more than the added capacity helps.

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
MLP_RATIO = 4              # MLP hidden size = MLP_RATIO * model_dim
n_kv_head = 6              # number of KV heads (= n_head for full MHA; <n_head for GQA)

# Attention window pattern — controls which layers use sliding-window (S)
# vs full (L) attention. Repeated to match DEPTH.
# "SSSL" = 3 sliding + 1 full per period — saves compute vs all-full "L"
WINDOW_PATTERN = "L"

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
WARMDOWN_RATIO = 0.5       # fraction of steps for cosine LR decay at end of run
FINAL_LR_FRAC = 0.0        # LR floor as fraction of peak LR (0 = full decay to zero)

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# WINDOW_PATTERN  — "SSSL" saves compute per step → more steps in wall-clock budget
# WARMDOWN_RATIO  — longer warmdown often improves final loss; try 0.6–0.8
# FINAL_LR_FRAC   — non-zero floor (e.g. 0.05) prevents over-annealing at tail
# DEPTH           — NOTE: adding depth costs more FLOPS per step (budget penalty)
# TOTAL_BATCH_SIZE — smaller batch = more steps but noisier gradients
# MLP_RATIO       — controls MLP capacity vs compute cost
# n_kv_head       — reduce for GQA (saves KV cache memory)
# HEAD_DIM        — 64 saves memory vs 128
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
