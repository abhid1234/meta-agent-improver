"""
GPT Training Configuration — Autoresearch Experiment on A40
============================================================
This file contains the hyperparameter configuration for a GPT-style language
model training run. Hardware target: single NVIDIA A40 (48GB VRAM).

Task state: After 21 experiments — maximum history. Matrix LR 0.03 was just
tried and discarded (slower learning, net negative vs 0.04). Best: 1.0940.
Active config: SSSL, warmdown=0.7, LR floor 5%, weight decay=0.01,
warmup=0.05, ADAM_BETAS=(0.8, 0.95), MATRIX_LR=0.04.

Remaining untried: SCALAR_LR, UNEMBEDDING_LR, ASPECT_RATIO.

NOTE: Only the hyperparameter block is shown here. The full training loop,
model architecture (GPT with configurable attention patterns), optimizer setup
(Muon + AdamW), and data pipeline are in the complete train.py (omitted for
brevity). Everything below is tunable without touching model or loop code.
"""

# ---------------------------------------------------------------------------
# Architecture hyperparameters
# ---------------------------------------------------------------------------

ASPECT_RATIO = 64          # width = ASPECT_RATIO * DEPTH — completely untried
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

EMBEDDING_LR = 0.6         # embedding table — 0.8 tried and FAILED; do not change
UNEMBEDDING_LR = 0.004     # output projection — very low; 0.002-0.008 completely untried
MATRIX_LR = 0.04           # weight matrices — 0.05 marginal worse; 0.03 also worse
SCALAR_LR = 0.5            # scalar params (layernorm, biases) — completely untried

# ---------------------------------------------------------------------------
# Attention configuration
# ---------------------------------------------------------------------------

n_kv_head = 6              # number of KV heads (= n_head; GQA tried and FAILED)

# ---------------------------------------------------------------------------
# Regularization
# ---------------------------------------------------------------------------

WEIGHT_DECAY = 0.01        # L2 penalty — helped; higher values untested
ADAM_BETAS = (0.8, 0.95)   # beta1=0.85 tried and FAILED; do not revisit

# ---------------------------------------------------------------------------
# LR schedule
# ---------------------------------------------------------------------------

WARMUP_RATIO = 0.05        # linear warmup for first 5% of steps
WARMDOWN_RATIO = 0.7       # fraction of steps for cosine LR decay
FINAL_LR_FRAC = 0.05       # LR floor = 5% of peak LR

# ---------------------------------------------------------------------------
# Tunable knobs summary — EXHAUSTION MAP (for the ML advisor agent)
# ---------------------------------------------------------------------------
# EXHAUSTED (do not retry):
#   DEPTH (4,8 both failed), WINDOW_PATTERN (L,S both worse than SSSL)
#   WARMDOWN (0.3,0.5,0.8 all worse than 0.7)
#   LR_FLOOR (10% too high; 0% too low; 5% is optimal)
#   MLP_RATIO (3 lost capacity), GQA (n_kv_head=1 failed)
#   HEAD_DIM (64 worse), BATCH_HALVING (noisier gradients)
#   MATRIX_LR (0.05 marginal worse; 0.03 also worse — 0.04 is sweet spot)
#   EMBEDDING_LR (0.8 failed — too aggressive)
#   ADAM_BETAS beta1 (0.85 failed — not clearly better)
#
# REMAINING UNTRIED (highest priority):
#   SCALAR_LR   — currently 0.5; completely unexplored
#   UNEMBEDDING_LR — currently 0.004; range 0.002-0.008 unexplored
#   ASPECT_RATIO — currently 64; wider (80) or narrower (48) unexplored
# ---------------------------------------------------------------------------

# [Full train.py continues here: model definition, Muon optimizer, data loader,
#  training loop, eval harness, checkpointing — omitted for brevity]
