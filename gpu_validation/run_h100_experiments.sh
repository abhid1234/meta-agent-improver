#!/bin/bash
# H100 validation — same 3 experiments as A40/L40S + 2 deeper variants
# Tests "optimal architecture depends on hardware" thesis

set -e
export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH
export PATH=$HOME/.local/bin:$PATH

cd /root

# Clone if needed
if [ ! -d /root/autoresearch ]; then
    git clone https://github.com/karpathy/autoresearch.git /root/autoresearch
fi

cd /root/autoresearch

# Install uv
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install python3.10-dev (needed for triton JIT compilation)
apt-get install -y python3.10-dev 2>&1 | tail -2

# Prepare data if needed
if [ ! -f ~/.cache/autoresearch/data/shard_00000.parquet ]; then
    uv run prepare.py
fi

# Save original
[ ! -f train_original.py ] && cp train.py train_original.py

run_experiment() {
    local name="$1"
    local depth="$2"
    local window="$3"
    local warmdown="$4"
    local lr_floor="$5"
    local device_bs="$6"
    local logfile="/tmp/${name}.log"

    echo ""
    echo "=========================================="
    echo "=== EXPERIMENT: $name ==="
    echo "=== depth=$depth window=$window warmdown=$warmdown lr_floor=$lr_floor device_bs=$device_bs ==="
    echo "=========================================="

    cp train_original.py train.py
    sed -i "s/^DEPTH = .*/DEPTH = $depth/" train.py
    sed -i "s/^WINDOW_PATTERN = .*/WINDOW_PATTERN = \"$window\"/" train.py
    sed -i "s/^TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/" train.py
    sed -i "s/^WARMDOWN_RATIO = .*/WARMDOWN_RATIO = $warmdown/" train.py
    sed -i "s/^FINAL_LR_FRAC = .*/FINAL_LR_FRAC = $lr_floor/" train.py
    sed -i "s/^DEVICE_BATCH_SIZE = .*/DEVICE_BATCH_SIZE = $device_bs/" train.py

    uv run train.py 2>&1 | tee "$logfile"
    echo ""
    echo "--- $name key metrics ---"
    grep "^val_bpb:\|^num_steps:\|^peak_vram_mb:" "$logfile"
}

# Original 3 experiments (matching A40/L40S runs)
run_experiment "h100_exp1_baseline_d6_L"       6 "L"    0.5 0.0  32
run_experiment "h100_exp2_sssl_d6"             6 "SSSL" 0.5 0.0  32
run_experiment "h100_exp3_full_optimized_d6"   6 "SSSL" 0.7 0.05 32

# H100-only: does depth=8 win with more compute headroom?
run_experiment "h100_exp4_depth8_L"            8 "L"    0.5 0.0  16
run_experiment "h100_exp5_depth8_full"         8 "SSSL" 0.7 0.05 16

echo ""
echo "=========================================="
echo "=== H100 FINAL SUMMARY ==="
echo "=========================================="
for exp in h100_exp1_baseline_d6_L h100_exp2_sssl_d6 h100_exp3_full_optimized_d6 h100_exp4_depth8_L h100_exp5_depth8_full; do
    echo ""
    echo "$exp:"
    grep "^val_bpb:\|^num_steps:" /tmp/$exp.log 2>/dev/null || echo "  (missing)"
done
