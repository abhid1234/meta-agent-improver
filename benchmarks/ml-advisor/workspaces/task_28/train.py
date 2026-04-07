"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 19 experiments. Warmup ratio 0.05 was just added (kept) —
small warmup stabilizes early training and prevents large initial gradient steps.
Current state: SSSL window, warmdown=0.7, LR floor 5%, weight decay=0.01,
warmup=0.05.

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

EMBEDDING_LR = 0.6         # embedding table — 0.8 tried and failed, stay at 0.6
UNEMBEDDING_LR = 0.004     # output projection / unembedding matrix (untried range)
MATRIX_LR = 0.04           # weight matrices in attention and MLP
SCALAR_LR = 0.5            # scalar params (biases, layernorm gains) — untried

# ---------------------------------------------------------------------------
# Attention configuration
# ---------------------------------------------------------------------------

n_kv_head = 6              # number of KV heads (= n_head; GQA disabled)

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.01        # L2 penalty — 0.01 kept; higher values untested
ADAM_BETAS = (0.8, 0.95)   # AdamW/Muon momentum params — beta1 range unexplored

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.05        # linear warmup for first 5% of steps — just added, helps
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay
FINAL_LR_FRAC = 0.05       # LR floor = 5% of peak LR — prevents full decay to zero

# ---------------------------------------------------------------------------
# Tunable knobs summary (for the ML advisor agent)
# ---------------------------------------------------------------------------
# SCALAR_LR       — currently 0.5; untried — layernorm/bias sensitivity unknown
# UNEMBEDDING_LR  — currently 0.004; very low — 0.002-0.008 range unexplored
# ASPECT_RATIO    — currently 64; width vs depth trade-off unexplored
# ADAM_BETAS      — currently (0.8, 0.95); beta1 and beta2 both untested
# LR schedule     — warmup + warmdown + floor all now configured
# EMBEDDING_LR    — 0.8 FAILED; do not increase. 0.6 is stable.
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
