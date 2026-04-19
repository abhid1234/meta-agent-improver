#!/bin/bash
# meta-agent-improver demo script — runs in asciinema for ~90 second capture
# Tells the story: baseline → meta-optimization → 100% → GPU validation

# Colors for emphasis
BOLD='\033[1m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
RESET='\033[0m'

slow() { echo -e "$1"; sleep "${2:-1.5}"; }
fast() { echo -e "$1"; sleep "${2:-0.5}"; }

clear

slow "${BOLD}${CYAN}█ META-AGENT IMPROVER${RESET}" 1
slow "${CYAN}Can an AI agent improve itself at ML hyperparameter advising?${RESET}" 2

# --- Act 1: The benchmark ---
slow "" 0.5
slow "${BOLD}${YELLOW}→ The benchmark: 30 ML advisor tasks${RESET}" 1
ls benchmarks/ml-advisor/workspaces/ | head -6 | tr '\n' '  '
echo " ... (30 total)"
sleep 2

slow "" 0.5
slow "${YELLOW}Each task: read experiment history, propose the next best hyperparameter change.${RESET}" 2.5

# --- Act 2: Vanilla baseline ---
slow "" 0.5
slow "${BOLD}${YELLOW}→ Vanilla Claude Haiku, no domain knowledge:${RESET}" 1.5
echo "  baseline ........ 80%  (24/30)"
sleep 2

# --- Act 3: Meta-optimization ---
slow "" 0.5
slow "${BOLD}${YELLOW}→ Let Sonnet optimize the prompt for Haiku, 21 iterations...${RESET}" 2
python3 -c "
import json
data = json.load(open('meta-agent/experience/ml-advisor/history.json'))
for it in data['iterations']:
    name = it['name']
    rate = it.get('pass_rate', 0)
    bar = '█' * int(rate * 40)
    marker = '  ← NEW BEST' if name in ('evo_001','evo_008','evo_015') else ''
    color = '\\033[32m' if rate >= 1.0 else '\\033[33m' if rate >= 0.9 else '\\033[37m'
    print(f'{color}  {name:10s} {rate:5.0%} {bar}{marker}\\033[0m')
    import time; time.sleep(0.15)
"
sleep 2

# --- Act 4: Discovery ---
slow "" 0.5
slow "${BOLD}${GREEN}→ 80% → 100%. What did it discover?${RESET}" 2
slow "${CYAN}  1. Phase-ordered exploration (architecture → dynamics → LR → regularization)${RESET}" 1.2
slow "${CYAN}  2. Context-aware overrides when the task hints at a specific parameter${RESET}" 1.2
slow "${CYAN}  3. Length-neutral prompt edits (add X chars → remove X elsewhere)${RESET}" 1.2
slow "${CYAN}  4. Baseline-row exclusion: 'baseline' is a starting state, not an experiment${RESET}" 2.5

# --- Act 5: GPU Validation ---
slow "" 0.5
slow "${BOLD}${YELLOW}→ Validating on actual GPUs — A40 vs L40S vs H100:${RESET}" 2
cat <<'EOF'
                     A40         L40S        H100
  Depth 6, baseline  1.0980      1.0702      1.0795
  Depth 6, optimized 1.0949 ★    1.0673 ★    1.0779
  Depth 8, optimized  1.1017       —          1.0318 ★

  Meta-agent's advice wins on budget GPUs.
  But on H100, a completely different config wins.
EOF
sleep 4

# --- Finale ---
slow "" 0.5
slow "${BOLD}${GREEN}→ Two insights, one project:${RESET}" 1.5
slow "${GREEN}  • Good prompts transfer across models${RESET}" 1
slow "${GREEN}  • Good architectures don't transfer across hardware${RESET}" 2
slow "" 0.3
slow "${BOLD}github.com/abhid1234/meta-agent-improver${RESET}" 2
slow "" 1
