#!/bin/bash
# Run the top 3 proposals from the meta-agent on actual GPU (L40S)

set -e

cd /root

# Clone if needed
if [ ! -d /root/autoresearch ]; then
    git clone https://github.com/karpathy/autoresearch.git /root/autoresearch
fi

cd /root/autoresearch

# Install uv
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Prepare the dataset (skips if already done)
if [ ! -f ~/.cache/autoresearch/shard_00000.parquet ]; then
    uv run prepare.py
else
    echo "Data already prepared, skipping."
fi

# Save original train.py
[ ! -f train_original.py ] && cp train.py train_original.py

# ========================================
# Experiment 1: BASELINE (depth=6, L attn)
# ========================================
echo "=== EXPERIMENT 1: Baseline ==="
cp train_original.py train.py
sed -i 's/^DEPTH = .*/DEPTH = 6/' train.py
sed -i 's/^WINDOW_PATTERN = .*/WINDOW_PATTERN = "L"/' train.py
sed -i 's/^TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/' train.py
sed -i 's/^WARMDOWN_RATIO = .*/WARMDOWN_RATIO = 0.5/' train.py
sed -i 's/^FINAL_LR_FRAC = .*/FINAL_LR_FRAC = 0.0/' train.py
sed -i 's/^DEVICE_BATCH_SIZE = .*/DEVICE_BATCH_SIZE = 32/' train.py
uv run train.py 2>&1 | tee /tmp/exp1_baseline.log
echo "--- Experiment 1 key metrics ---"
grep "^val_bpb:\|^num_steps:\|^peak_vram_mb:" /tmp/exp1_baseline.log

# ========================================
# Experiment 2: SSSL WINDOW PATTERN
# ========================================
echo ""
echo "=== EXPERIMENT 2: SSSL window attention ==="
cp train_original.py train.py
sed -i 's/^DEPTH = .*/DEPTH = 6/' train.py
sed -i 's/^WINDOW_PATTERN = .*/WINDOW_PATTERN = "SSSL"/' train.py
sed -i 's/^TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/' train.py
sed -i 's/^WARMDOWN_RATIO = .*/WARMDOWN_RATIO = 0.5/' train.py
sed -i 's/^FINAL_LR_FRAC = .*/FINAL_LR_FRAC = 0.0/' train.py
sed -i 's/^DEVICE_BATCH_SIZE = .*/DEVICE_BATCH_SIZE = 32/' train.py
uv run train.py 2>&1 | tee /tmp/exp2_sssl.log
echo "--- Experiment 2 key metrics ---"
grep "^val_bpb:\|^num_steps:\|^peak_vram_mb:" /tmp/exp2_sssl.log

# ========================================
# Experiment 3: META-AGENT'S FULL RECOMMENDATION
# ========================================
echo ""
echo "=== EXPERIMENT 3: SSSL + Warmdown 0.7 + LR floor 5% ==="
cp train_original.py train.py
sed -i 's/^DEPTH = .*/DEPTH = 6/' train.py
sed -i 's/^WINDOW_PATTERN = .*/WINDOW_PATTERN = "SSSL"/' train.py
sed -i 's/^TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/' train.py
sed -i 's/^WARMDOWN_RATIO = .*/WARMDOWN_RATIO = 0.7/' train.py
sed -i 's/^FINAL_LR_FRAC = .*/FINAL_LR_FRAC = 0.05/' train.py
sed -i 's/^DEVICE_BATCH_SIZE = .*/DEVICE_BATCH_SIZE = 32/' train.py
uv run train.py 2>&1 | tee /tmp/exp3_full.log
echo "--- Experiment 3 key metrics ---"
grep "^val_bpb:\|^num_steps:\|^peak_vram_mb:" /tmp/exp3_full.log

echo ""
echo "=========================================="
echo "=== FINAL SUMMARY ==="
echo "=========================================="
echo "Experiment 1 (Baseline — depth=6, L attention):"
grep "^val_bpb:\|^num_steps:" /tmp/exp1_baseline.log
echo ""
echo "Experiment 2 (SSSL window):"
grep "^val_bpb:\|^num_steps:" /tmp/exp2_sssl.log
echo ""
echo "Experiment 3 (Full optimized — SSSL + warmdown 0.7 + LR floor 5%):"
grep "^val_bpb:\|^num_steps:" /tmp/exp3_full.log
