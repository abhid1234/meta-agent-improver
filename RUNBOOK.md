# RUNBOOK — Operational Guide

Every gotcha I hit while running this, and the fix. If you're debugging something unexpected, search here first.

---

## 🚨 Top lessons (read this first)

1. **Every proposer iteration is itself an agent that can fail.** Two of my 21 iterations (evo_002, evo_003) crashed because the proposer ran out of turns before writing a config. When the proposer burns its turn budget on analysis, nothing gets produced. See *Issue 1* for the fix.

2. **Prompt edits must be length-neutral once you're above 95%.** Adding guidance without removing anything elsewhere redistributes the inner model's attention and breaks tasks that were passing. See *Lesson 2*.

3. **The baseline row in `results.tsv` is a trap.** The row labeled "baseline" records the *starting state* of your experiment (e.g., `warmdown=0.5`, `LR_floor=0`). It is NOT an already-tried experiment. If your prompt treats it as one, the agent will skip a whole phase. See *Issue 5*.

4. **RunPod PyTorch containers are missing Python dev headers.** `triton` JIT compilation fails silently with `InductorError: returned non-zero exit status 1` because `/usr/include/python3.10/Python.h` doesn't exist. Install `python3.10-dev` before you run anything. See *Issue 3*.

5. **Verify.py receives an absolute path, not a relative one.** The meta-agent framework copies workspaces to `/tmp/...` before running verify. If your `verify` command is `["python3", "../../verify.py"]`, it breaks. Use an absolute path. See *Issue 2*.

---

## ✅ The correct setup (replaces everything below)

```bash
# From repo root
git clone https://github.com/canvas-org/meta-agent.git
cd meta-agent-improver

# Setup Python 3.13 venv
uv venv --python 3.13
uv pip install -e meta-agent
uv pip install google-genai openai   # optional, only if you want cross-model eval

# Set API keys in .env
cat > .env <<EOF
ANTHROPIC_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here  # optional
EOF

# Run the baseline
source .env
.venv/bin/python3 -m meta_agent.eval_runner \
    --benchmark benchmarks/ml-advisor/benchmark.yaml \
    --config configs/vanilla.py \
    --name baseline \
    --model <inner-model> \
    --keep-failed \
    --concurrency 6

# Run the outer loop (20+ iterations)
cd meta-agent
.venv/bin/python3 -m meta_agent.outer_loop \
    --benchmark ../benchmarks/ml-advisor/benchmark.yaml \
    --iterations 21 \
    --model <inner-model> \
    --proposer-model <proposer-model> \
    --fast --concurrency 6 \
    --evolve-skill --skill-evolve-every 5
```

### Host requirements

- **Python 3.13** (the framework requires `>=3.11`; newer is fine)
- **`uv`** for virtualenv management (gets around corp-airlock pip blocks)
- **GPU optional** — the ML advisor benchmark is pure reasoning, no GPU needed for the meta-optimization loop. You only need a GPU for the validation step.
- **Linux / macOS** — tested on both.

---

## Known issues and fixes

### Issue 1: Proposer hits turn limit without producing a config

**Symptom:** `evo_002` and `evo_003` logs show the proposer reading traces, planning, reasoning through failure modes — and then just stopping. No config written. The outer loop moves on.

**Cause:** The proposer is itself a coding agent. If it tries to reason through the full failure analysis in a single pass, it can hit the 50-turn limit before writing anything. Complex reasoning → no output.

**Fix:** The framework retries these automatically. Just re-run. Two workarounds for recurring failures:

1. Increase the proposer's `--max-turns` flag (default 50).
2. Structure the proposer prompt to write intermediate files (diagnosis.md, plan.md) before the final config. Forces it to produce something early.

**What I did:** Nothing. Both crashes were in iterations 2 and 3 — the proposer simply burned turns. iterations 4+ all produced configs. 2 failed runs out of 21 (~10% failure rate) was tolerable.

---

### Issue 2: `FAIL: No ground truth for workspace` from the verifier

**Symptom:** Every task fails in a fresh eval run. The verify output says:

```
FAIL: No ground truth for workspace
```

**Cause:** The meta-agent framework copies the task workspace to `/tmp/task_task_XX_<random>/task_XX/`. Your `verify` command in `benchmark.yaml` using a relative path (`["python3", "../../verify.py"]`) resolves against the temp directory, not your project root. So verify.py can't be found.

**Fix:** Use an absolute path in `benchmark.yaml`:

```yaml
verify: ["python3", "/home/abhidaas/Core/Workspace/ClaudeCode/meta-agent-improver/verify.py"]
```

Also: verify.py determines the task name from `Path.cwd().name`. Make sure `eval_openrouter.py` (or whatever eval script you wrote) copies the workspace to a directory named after the task, not a generic name like `workspace/`.

**What broke for me:** Both problems hit me on the first smoke-test run. Fixed with `sed -i 's|"../../verify.py"|"/abs/path/verify.py"|' benchmark.yaml` and one `task_name` variable fix in the custom runner.

---

### Issue 3: `torch._inductor.exc.InductorError: CalledProcessError` during training on RunPod

**Symptom:** Your training script starts, prints the model config, then fails during the first `torch.compile` pass:

```
torch._inductor.exc.InductorError: CalledProcessError:
  Command '['/usr/bin/gcc', ..., '-lcuda', ..., '-I/usr/include/python3.10']'
  returned non-zero exit status 1.
```

**Cause:** RunPod's `runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04` image ships with Python 3.11 system binaries but the venv was created with Python 3.10 (pulled by `uv`). Triton JIT-compiles CUDA helpers via `gcc`, which needs `Python.h` for the active Python version. The image doesn't include `python3.10-dev`, so the compile fails with a cryptic error that doesn't directly mention the missing header.

**Fix:** Install the dev headers on the pod before running training:

```bash
apt-get update -qq
apt-get install -y python3.10-dev
```

Or, better: use a PyTorch image that matches the Python version your venv uses.

**What broke for me:** Both L40S and H100 runs hit this. First attempt on each pod failed with 5+ minutes wasted before I realized the real error was the missing header (the stack trace only shows the gcc exit code, not its stderr). Added the install step to `run_experiments.sh` after the first failure.

---

### Issue 4: `AssertionError: TOTAL_BATCH_SIZE % tokens_per_fwdbwd == 0`

**Symptom:** Training aborts at line 496 of `autoresearch/train.py`:

```python
assert TOTAL_BATCH_SIZE % tokens_per_fwdbwd == 0
AssertionError
```

**Cause:** The original Karpathy `autoresearch/train.py` is tuned for H100 (`TOTAL_BATCH_SIZE = 2**19 = 524K`, `DEVICE_BATCH_SIZE = 64`). If you lower `TOTAL_BATCH_SIZE` to `2**17 = 131K` for an A40/L40S but keep `DEVICE_BATCH_SIZE = 64`, you get `64 * 2048 = 131072` per forward-backward pass, which only divides evenly into `TOTAL_BATCH_SIZE = 131072` once. That's fine by the math — but the real issue is that my `sed` was matching `TOTAL_BATCH_SIZE` inside other comment lines, corrupting the file.

**Fix:** Anchor your `sed` regex to beginning-of-line:

```bash
# BAD — matches anywhere including comments
sed -i 's/TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/' train.py

# GOOD — only matches the assignment at line start
sed -i 's/^TOTAL_BATCH_SIZE = .*/TOTAL_BATCH_SIZE = 2**17/' train.py
```

Also explicitly set `DEVICE_BATCH_SIZE` to match your target `TOTAL_BATCH_SIZE`:

```bash
sed -i 's/^DEVICE_BATCH_SIZE = .*/DEVICE_BATCH_SIZE = 32/' train.py
```

---

### Issue 5: 95% → 100% requires a "length-neutral" prompt edit

**Symptom:** You're at 95% pass rate (19/20). Only `task_02` is failing. The proposer adds a clearer instruction to Step 1 of the prompt. New config scores 90%. Several tasks that were passing now fail.

**Cause:** At the inner model's attention boundary (around 20-task success rate for small models), any net addition of prompt text redistributes attention and breaks tasks that were passing. Adding 200 chars of new guidance isn't free — the model re-weights everything.

**Fix:** Length-neutral editing. For every N characters added to fix a failing case, remove N characters elsewhere that are either redundant or over-specified.

**What worked for me:** evo_015 fixed `task_02` by (a) rewording Step 1 to exclude baseline rows from TRIED (+64 chars), and (b) compressing Step 3's "no-directive fallback" from 3 paragraphs to 1 sentence (-146 chars). Net: -82 chars, but the critical new guidance was in place. Pass rate went from 95% to 100%.

**Generalizable rule:** Above 95%, track prompt character counts in your proposer's diagnosis. Write explicit length-neutral edits.

---

### Issue 6: Mistral OpenRouter model ID returns 404

**Symptom:** Calling `mistralai/mistral-7b-instruct` via OpenRouter returns:

```
Error code: 404 - {'error': {'message': 'No endpoints found for mistralai/mistral-7b-instruct.', 'code': 404}}
```

**Cause:** OpenRouter has deprecated several older Mistral models. The model name in their docs may not match what's actually routable.

**Fix:** Use `mistralai/mistral-small-3.1-24b-instruct` instead. It's the smallest currently-routable Mistral model with tool/instruction-following quality. Check [openrouter.ai/models](https://openrouter.ai/models) for the current list.

---

### Issue 7: `No space left on device` during `uv pip install` on RunPod

**Symptom:** When trying to reinstall `autoresearch/.venv` on a RunPod pod you've been using for a while:

```
error: Failed to install: matplotlib-3.10.8-cp310-cp310-manylinux...
  Caused by: failed to open file `...`: No space left on device (os error 28)
```

**Cause:** Default RunPod container disk is 20GB. The PyTorch image alone is ~8GB. After downloading CUDA libs and data shards, matplotlib + numpy + pyarrow tip it over the edge.

**Fix:** Either (a) deploy the pod with `container_disk_in_gb=25` or higher from the start, or (b) clean up before reinstalling:

```bash
rm -rf /root/autoresearch/.venv
apt clean
df -h /
```

---

### Issue 8: RunPod community A40 pods out of stock

**Symptom:** `runpod.create_pod(gpu_type_id="NVIDIA A40", cloud_type="COMMUNITY")` returns:

```
There are no longer any instances available with the requested specifications.
```

**Cause:** A40 community cloud inventory fluctuates. At peak times there are zero available.

**Fix:** Try in this order: A40 community → L40S community → A40 secure → L40S secure → other 48GB cards. L40S is functionally equivalent to A40 for this workload (same VRAM class, similar compute). Secure cloud is ~2× the price but usually has capacity.

My actual fallback sequence: A40 community (out) → L40S community (available at $0.79/hr). Worked fine.

---

## Recurring patterns I noticed

### Pattern A: Exceptions breed regressions

When the proposer found a failure case, its first instinct was usually to add an "Exception" clause to the existing rules. In evo_004 it did exactly this — and the exception fixed 2 tasks while breaking 2 others. Every "Exception" clause I've seen in an agent prompt has caused regressions.

The better fix: go upstream. Rewrite the rule that's generating the exception into something that doesn't need one. evo_008 removed the exception and fixed the root cause, jumping from 85% to 95%.

### Pattern B: Context.md trumps inline code comments

Two different signals competed for the agent's attention:
- `context.md` — authoritative task-level guidance ("focus on LR schedule")
- `train.py` code comments — implementation hints ("try X = 0.05")

Early iterations treated these as equivalent. That broke tasks where the two disagreed. Rule that eventually worked: **context.md overrides phase ordering; train.py comments never do, they're just candidates.**

### Pattern C: The proposer needs memory

The framework writes every previous candidate to disk (`experience/<bench>/candidates/<name>/`). Early proposer runs didn't read this history — they re-derived rules from scratch each iteration, often reversing prior fixes.

Fix in the SKILL.md guidance: tell the proposer to explicitly run `python -m meta_agent.cli list` and `show <name>` on the top 3 candidates before writing a new config. Forces it to see what's been tried.

---

## Hardware notes

For the 26M parameter model used in autoresearch:

| GPU | Price/hr | Steps in 5 min | Cost per 5-min experiment |
|---|---|---|---|
| A40 (RunPod community) | $0.40 | ~1,175 | $0.033 |
| L40S (RunPod community) | $0.79 | ~1,891 | $0.066 |
| H100 80GB HBM3 (RunPod secure) | $2.99 | ~1,699 | $0.249 |

**L40S completes more steps than H100** at this model scale because kernel launch overhead dominates for small models. For sub-50M parameter experiments, L40S is the better price/performance point.

**H100 only wins when you can grow the model.** depth=8 (54M params) on H100 trained to `val_bpb = 1.0318`, while depth=6 (26M) capped around `1.0779`. On A40, depth=8 *hurt* performance because training steps ran out before convergence.

---

## Cost accounting for this project

| Line item | Cost |
|---|---|
| Baseline eval (30 tasks × small model, ~5 turns each) | ~$2 |
| Outer loop (21 iterations × 20 tasks × small model) | ~$15 |
| Outer loop proposer (21 × ~30 turns on larger model) | ~$3 |
| Cross-model transfer (Llama + Mistral × 30 tasks × 2 configs) | ~$1 |
| RunPod L40S (1 hr) | $0.79 |
| RunPod H100 (1 hr) | $2.99 |
| **Total** | **~$25-26** |

All receipts in the respective provider dashboards.
