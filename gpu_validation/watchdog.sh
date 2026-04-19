#!/bin/bash
# Watchdog: poll H100 pod, auto-terminate when 5 experiments done, save results
set -e

POD_ID="4zklmjhtwcejf6"
POD_IP="216.243.220.217"
POD_PORT="10788"
PROJECT_DIR="/home/abhidaas/Core/Workspace/ClaudeCode/meta-agent-improver"
LOG_FILE="$PROJECT_DIR/gpu_validation/h100_watchdog.log"

source "$PROJECT_DIR/.env"
export RUNPOD_API_KEY

echo "[$(date)] Watchdog started, polling every 60s..." | tee -a "$LOG_FILE"

MAX_WAIT=5400  # 90 min hard cap
ELAPSED=0
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=10"

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # Count completed val_bpb lines
    N_DONE=$(ssh $SSH_OPTS -p $POD_PORT root@$POD_IP "grep -c '^val_bpb:' /root/h100.log 2>/dev/null || echo 0" 2>/dev/null || echo 0)
    N_DONE=$(echo "$N_DONE" | tr -d '[:space:]')
    # Extract just the number (last integer)
    N_DONE=$(echo "$N_DONE" | grep -oE '[0-9]+$' | tail -1)
    N_DONE=${N_DONE:-0}

    echo "[$(date)] experiments_completed=$N_DONE/5, elapsed=${ELAPSED}s" | tee -a "$LOG_FILE"

    if [ "$N_DONE" -ge 5 ]; then
        echo "[$(date)] All 5 experiments complete!" | tee -a "$LOG_FILE"
        break
    fi

    # Check if pod is still running (stopped = already terminated by someone)
    POD_STATUS=$(.venv/bin/python3 -c "
import runpod, os
runpod.api_key = os.environ['RUNPOD_API_KEY']
try:
    p = runpod.get_pod('$POD_ID')
    print(p.get('desiredStatus', 'UNKNOWN') if p else 'NOT_FOUND')
except: print('ERROR')
" 2>/dev/null)

    if [ "$POD_STATUS" != "RUNNING" ]; then
        echo "[$(date)] Pod status=$POD_STATUS, exiting watchdog" | tee -a "$LOG_FILE"
        break
    fi

    sleep 60
    ELAPSED=$((ELAPSED + 60))
done

# Download log
echo "[$(date)] Downloading log..." | tee -a "$LOG_FILE"
scp $SSH_OPTS -P $POD_PORT root@$POD_IP:/root/h100.log "$PROJECT_DIR/gpu_validation/h100.log" 2>&1 | tail -3 | tee -a "$LOG_FILE"

# Terminate pod
echo "[$(date)] Terminating pod $POD_ID..." | tee -a "$LOG_FILE"
.venv/bin/python3 -c "
import runpod, os
runpod.api_key = os.environ['RUNPOD_API_KEY']
try:
    runpod.terminate_pod('$POD_ID')
    print('Pod terminated')
except Exception as e:
    print(f'Terminate failed: {e}')
" 2>&1 | tee -a "$LOG_FILE"

# Extract results from log
echo "" | tee -a "$LOG_FILE"
echo "[$(date)] Extracting val_bpb results..." | tee -a "$LOG_FILE"
if [ -f "$PROJECT_DIR/gpu_validation/h100.log" ]; then
    grep -E "EXPERIMENT|^val_bpb:|^num_steps:" "$PROJECT_DIR/gpu_validation/h100.log" | tee -a "$LOG_FILE"
fi

echo "[$(date)] Watchdog finished." | tee -a "$LOG_FILE"
