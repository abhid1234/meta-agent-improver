"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 20 experiments. ADAM_BETAS beta1 0.85 was tried and discarded
— marginal, not clearly better than 0.8. Current best: 1.0940.
Active config: SSSL, warmdown=0.7, LR floor 5%, weight decay=0.01, warmup=0.05,
ADAM_BETAS=(0.8, 0.95).

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

# MLP expansion factor — ratio of MLP hidden dim to model dim
MLP_RATIO = 4

# ---------------------------------------------------------------------------
# Batch and sequence
# ---------------------------------------------------------------------------

TOTAL_BATCH_SIZE = 2**17   # ~131K tokens per gradient step (across all devices)
DEVICE_BATCH_SIZE = 64     # tokens per forward pass per device; grad accum fills the rest

# ---------------------------------------------------------------------------
# Learning rates (per parameter group)
# ---------------------------------------------------------------------------

EMBEDDING_LR = 0.6         # embedding table — 0.8 tried and failed
UNEMBEDDING_LR = 0.004     # output projection / unembedding matrix (untried)
MATRIX_LR = 0.04           # weight matrices in attention and MLP
SCALAR_LR = 0.5            # scalar params (biases, layernorm gains) — untried

# ---------------------------------------------------------------------------
# Attention configuration
# ---------------------------------------------------------------------------

n_kv_head = 6              # number of KV heads (= n_head; GQA disabled)

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.01        # L2 penalty — helped; higher untested
ADAM_BETAS = (0.8, 0.95)   # beta1=0.85 tried and discarded — stay at 0.8

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.05        # linear warmup for first 5% of steps
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay
FINAL_LR_FRAC = 0.05       # LR floor = 5% of peak LR

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# SCALAR_LR       — currently 0.5; completely untried — highest priority
# UNEMBEDDING_LR  — currently 0.004; untried range (0.002-0.008)
# ASPECT_RATIO    — currently 64; wider (80) or narrower (48) unexplored
# ADAM_BETAS      — beta1=0.85 FAILED; do not revisit beta1 changes
# EMBEDDING_LR    — 0.8 FAILED; do not change
# LR schedule     — fully configured; do not revisit
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
