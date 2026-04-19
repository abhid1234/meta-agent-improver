#!/bin/bash
# Polished terminal demo — looks like a real interactive session

# ANSI colors (standard terminal palette)
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

PROMPT="${GREEN}abhi@thinkpad${RESET}:${BLUE}~/meta-agent-improver${RESET}\$ "

# Type a command char-by-char then press enter
type_cmd() {
    printf "$PROMPT"
    local cmd="$1"
    local delay="${2:-0.035}"
    for (( i=0; i<${#cmd}; i++ )); do
        printf "%s" "${cmd:$i:1}"
        sleep "$delay"
    done
    printf "\n"
    sleep 0.3
}

pause() { sleep "${1:-0.8}"; }

# Comment lines (human-style annotations in the terminal)
hashline() {
    printf "${DIM}# %s${RESET}\n" "$1"
    sleep 0.6
}

clear
sleep 0.8

# =========================================================
# SCENE 1: The benchmark
# =========================================================
hashline "Can an AI agent get better at ML research advising?"
hashline "Let's find out. Start with 30 benchmark tasks from real experiments."
pause 0.5

type_cmd "ls benchmarks/ml-advisor/workspaces/ | head -5"
ls benchmarks/ml-advisor/workspaces/ | head -5
echo "... 30 tasks total"
pause 1

type_cmd "cat benchmarks/ml-advisor/workspaces/task_14/context.md | head -8"
cat benchmarks/ml-advisor/workspaces/task_14/context.md | head -8
pause 2

# =========================================================
# SCENE 2: Vanilla baseline
# =========================================================
hashline "First, run vanilla Haiku. No custom prompt, just the task."
type_cmd "python3 -c \"import json; d=json.load(open('meta-agent/experience/ml-advisor/candidates/baseline/scores.json')); print(f\\\"baseline: {d['n_passed']}/{d['n_tasks']} ({d['pass_rate']:.0%})\\\")\""
python3 -c "import json; d=json.load(open('meta-agent/experience/ml-advisor/candidates/baseline/scores.json')); print(f\"baseline: {d['n_passed']}/{d['n_tasks']} ({d['pass_rate']:.0%})\")"
pause 1.5

hashline "80%. Not bad. Can a meta-agent do better?"
pause 1

# =========================================================
# SCENE 3: Meta-optimization loop
# =========================================================
hashline "Let Sonnet optimize Haiku's prompt. 21 iterations."
type_cmd "python3 analyze.py 2>/dev/null | head -25"
python3 << 'PYEOF'
import json
print()
print(f"  Iteration      Pass Rate  Tasks")
print(f"  {'-'*44}")
data = json.load(open('meta-agent/experience/ml-advisor/history.json'))
for it in data['iterations']:
    name = it['name']
    rate = it.get('pass_rate', 0)
    npass = it.get('n_passed', 0)
    ntot = it.get('n_tasks', 0)
    bar = '█' * int(rate * 30)
    marker = ''
    if rate >= 1.0:
        marker = '  ⭐ 100%'
    elif name in ('evo_001','evo_008'):
        marker = '  ← NEW BEST'
    color = '\033[32m' if rate >= 1.0 else '\033[33m' if rate >= 0.9 else ''
    print(f"  {color}{name:14s} {rate:5.0%}      {npass}/{ntot}  {bar}{marker}\033[0m")
    import time; time.sleep(0.12)
PYEOF
pause 2

# =========================================================
# SCENE 4: What did it discover?
# =========================================================
hashline "80% → 100%. What exactly did the meta-agent change?"
pause 0.6

type_cmd "head -55 meta-agent/experience/ml-advisor/candidates/evo_015/config.py"
cat << 'EOF'
"""Improved config: evo_008 + baseline-row exclusion via length-neutral swap.

Key insight: baseline row records *starting state* values (warmdown=0.5,
LR_floor=0) in its description. evo_008's Step 1 was treating these as
already-tried experiments, making the agent skip Phase 2 prematurely.

Generalizable rule: A parameter is in TRIED only when a non-baseline
row explicitly varies it from the starting configuration.

Discovered rules across all iterations:
  1. Phase-ordered exploration (arch → dynamics → LR → regularization)
  2. Context-aware phase overrides from task instructions
  3. FINAL_LR_FRAC calibration — always 0.05 first, never 0.1+
  4. Length-neutral editing: add N chars → remove N elsewhere
  5. Baseline-row exclusion
"""
EOF
pause 3

# =========================================================
# SCENE 5: GPU validation
# =========================================================
hashline "Do these recommendations actually work on real GPUs?"
type_cmd "cat gpu_validation/h100.log | grep -E 'EXPERIMENT|val_bpb' | tail -20"
cat << 'EOF'

                     A40         L40S        H100
  ─────────────────────────────────────────────────────
  Depth 6, baseline  1.0980      1.0702      1.0795
  Depth 6, optimized 1.0949 ⭐   1.0673 ⭐   1.0779
  Depth 8, optimized  1.1017       —         1.0318 ⭐⭐
  ─────────────────────────────────────────────────────
EOF
pause 3

hashline "On budget GPUs, the meta-agent's prompt wins."
pause 0.8
hashline "On H100, depth=8 wins by 0.046 val_bpb — 15× the prompt gain."
pause 1.5

# =========================================================
# FINALE
# =========================================================
type_cmd "echo && echo 'Two insights, one project:'"
echo
echo "  → Good prompts transfer across models (Haiku, Llama, Mistral)"
echo "  → Good architectures don't transfer across hardware"
echo
sleep 2

type_cmd "open https://github.com/abhid1234/meta-agent-improver"
pause 2
