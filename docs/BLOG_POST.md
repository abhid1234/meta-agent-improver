# I Let AI Optimize the AI Researcher Itself — Here's What Actually Works (and What Doesn't)

*A $26 weekend experiment on how meta-agents get better at advising ML experiments, and why the hardware mattered more than the prompt.*

---

A few weeks ago I ran 16 overnight ML experiments on an A40 GPU — an inner model playing researcher, reading logs, proposing hyperparameter changes, iterating. It worked. Cost me $15 and a night's sleep. ([That story is Part 1.](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent))

The follow-up question was obvious: what if I let AI optimize the AI researcher itself?

That's what this is. A meta-agent that reads its own failure traces and rewrites its own guidance. After 21 iterations it hit 100% on the search set and 90% on holdout. Total cost: $26. And the most important thing it taught me had nothing to do with prompts.

---

## How the Loop Works

The idea is straightforward. You have an inner agent doing a task. You have a verifier that grades it. And you have an outer loop — the meta-agent — that reads the failure traces and proposes edits to the inner agent's system prompt.

```
         ┌─────────────────────┐
         │    Outer Loop       │
         │  (proposer model)   │
         │                     │
         │  reads failures  →  │
         │  rewrites prompt    │
         └────────┬────────────┘
                  │ new prompt
         ┌────────▼────────────┐
         │    Inner Agent      │
         │  (inner model)      │
         │                     │
         │  reads experiment   │
         │  history → proposes │
         │  next hyperparam    │
         └────────▼────────────┘
                  │ proposal
         ┌────────▼────────────┐
         │  Deterministic      │
         │  Verifier           │
         │                     │
         │  checks against     │
         │  ground truth       │
         └─────────────────────┘
```

The benchmark: 30 tasks derived from those 16 real Part 1 experiments. Each task gives the inner agent an experiment log, a training script, and a context brief — and asks it to name the single best next hyperparameter change. The verifier checks against the actual outcome. No LLM judge. Either you got it right or you didn't.

The framework is [canvas-org/meta-agent](https://github.com/canvas-org/meta-agent), which handles the loop mechanics, file-based memory, and candidate tracking.

---

## Lesson 1: Failures Are Free Training Data

Baseline inner model — no custom guidance, just the default prompt — scored 80% on 30 tasks (24/30). It handles the easy cases fine. Architecture exploration is intuitive: if you haven't tried sliding window attention, try it. Where it stumbles is on tasks that require phase awareness or careful reading of a context brief.

That 80% baseline matters because it isn't zero. The inner model is already good. What the outer loop is doing is hunting for the last 20% — the tasks where the model's default reasoning leads it somewhere plausible but wrong.

Those failures are the training signal. The outer loop reads them, patterns them, and writes a rule. No human labeling, no fine-tuning, no gradient updates. Just a proposer model reading errors and writing better instructions.

---

## Lesson 2: Prompts Are Programs

After 21 iterations, here's what the meta-agent produced:

```
_ADVISOR_GUIDANCE = """
You are an ML experiment advisor. When proposing the next hyperparameter change:

## Step 1 — Enumerate the experimental state
Read results.tsv carefully. Build two lists:
- TRIED: every parameter (and value) that appears in the description column
  (exclude the baseline row — it describes the starting state, not a tried experiment)
- UNTRIED: every tunable parameter from train.py that does NOT appear in TRIED

## Step 2 — Identify the current exploration phase
ML experiments follow a natural phase order. Determine which phase is still active:
1. Architecture — depth, attention window patterns (e.g. L → SSSL, SSSL → S)
2. Training dynamics — batch size, warmdown ratio (including values not yet tested)
3. Model capacity — HEAD_DIM, n_kv_head (GQA), MLP_RATIO, matrix LR multipliers
4. LR schedule — WARMUP_RATIO, FINAL_LR_FRAC (LR floor), embedding/scalar LRs
   - FINAL_LR_FRAC first trial: use 0.05 (a 5% floor). Do NOT use 0.1 or higher
     on a first trial — a high LR floor prevents sufficient decay.
5. Regularization — ADAM_BETAS, WEIGHT_DECAY

## Step 3 — Select the phase and pick the best parameter
Scan context.md for any explicit directive about which parameter area to explore.
If found, start from that phase — do not explore earlier phases even if they have
untried parameters. The task context is authoritative.

If context.md gives no specific directive, use the standard rule: choose the
earliest active phase from Step 2.

## Step 4 — Treat train.py code comments as hints, not commands
Code comments that suggest specific values are reminders of candidates,
not the recommended next step.

## Step 5 — Write proposal.json with the chosen parameter
"""
```

This isn't prose — it's a decision procedure. Enumerate state. Identify phase. Check for overrides. Pick parameter. Write output. Four rules, in order. The meta-agent wrote better-structured guidance than I would have written by hand, because it was working from evidence of what specifically went wrong.

What it converged on is also exactly what a senior ML engineer would tell a junior one in week one: explore architecture before schedule, don't skip phases, always try LR floor at 5% not 10%, respect what the context brief is telling you to do. The meta-agent rediscovered standard practice from failure traces.

---

## Lesson 3: Exceptions Are a Code Smell, Even in Prompts

The most instructive failure in the whole run was evo_004.

After evo_001 established phase ordering and reached 85%, the proposer looked at the remaining failures. Two of them (task_14 and task_18) involved cases where the context brief gave an explicit LR schedule directive, but the inner model kept following phase ordering and proposing architecture changes instead. Plausible diagnosis: add an exception.

So evo_004 added this:

> **Exception:** when a comment in `train.py` names a specific numeric value for an untried parameter, use that value exactly.

This was wrong in a subtle way. The proposer had conflated two different signals — context.md directives (authoritative, from the experimenter) and train.py code comments (implementation hints, from whoever wrote the training code). By treating code comments as override-worthy, it created a backdoor that let the inner model bypass phase ordering for the wrong reasons.

evo_004 fixed task_18 and task_20, and broke task_15 and task_17. Net: zero improvement. evo_007 tried a different angle and regressed to 80%.

evo_008 finally got it right by doing two things: removing the Exception clause entirely, and adding explicit instruction about how to distinguish context.md directives from code comments. No exceptions. Root cause fixed.

Result: 95%. One task still failing.

The pattern is identical to what experienced engineers mean when they say "exceptions are a code smell." A patch for a symptom is not a fix for the root cause.

Two early iterations (evo_002 and evo_003) also failed outright — the proposer model hit its turn limit before producing a complete config. Complex reasoning in a single unstructured pass, with no explicit scaffolding, tends to run long. The framework retried these automatically, but they're a reminder that the proposer is itself an agent that can fail.

---

## Lesson 4: Prompt Edits Must Be Length-Neutral

After evo_008 hit 95%, the next six iterations (evo_009 through evo_014) plateaued. Only task_02 kept failing. The proposer analyzed it across six prior configs and found something subtle.

The `results.tsv` file always has a "baseline" row — the very first row, describing the model's starting state. The prompt's Step 1 was telling the inner model to treat every row in results.tsv as a tried experiment. That baseline row was being read as evidence that warmdown=0.5 and LR_floor=0 had already been deliberately tested and discarded.

So the inner model marked those parameters as TRIED, skipped Phase 2 (training dynamics) entirely, and jumped to the wrong phase. task_02 required proposing a warmdown adjustment — and the model thought it had already been covered.

The fix: reword Step 1 to explicitly exclude baseline rows from the TRIED list. Clear, surgical, correct.

Here's the constraint that made it hard: at 95% accuracy, the inner model is operating near its attention limits. Any net addition to prompt length risks redistributing attention away from the rules that were already working, breaking tasks that were passing fine. The proposer figured this out.

The evo_015 fix added 64 characters to Step 1 and removed 146 characters from a redundant fallback clause in Step 3. Net change: 82 characters shorter. The prompt shrank to fix a bug that was causing a failure.

That's the real craft at 95% → 100%: not adding new guidance, but fixing a data interpretation bug while keeping the prompt the same size. Length-neutral editing. Prompt surgery is precise work.

---

## Lesson 5: Prompts Transfer Across Models; Architecture Doesn't Transfer Across Hardware

Two things happened after evo_015 that reframed the whole project.

**First, cross-model transfer.** I ran the same `_ADVISOR_GUIDANCE` — unchanged — on Mistral Small 24B and Llama 3.1 8B via OpenRouter:

| Model | Baseline | With optimized prompt |
|-------|----------|-----------------------|
| Original inner model | 80% | 100% (after 21 iterations) |
| Llama 3.1 8B | 87% | 87% (different tasks pass/fail) |
| Mistral Small 24B | 87% | **90%** |

Mistral Small 24B gained 3 percentage points with zero modification. Llama 3.1 8B stayed flat on count but changed which tasks it got right. The rules the meta-agent discovered — phase ordering, context override, baseline-row exclusion — describe what good ML research reasoning looks like. They're not model-specific. They transferred.

**Second, the GPU results.** I ran the top proposals from the optimized agent on actual hardware — A40, L40S, and H100 via RunPod:

| Config | A40 (val_bpb) | L40S (val_bpb) | H100 (val_bpb) |
|--------|---------------|----------------|----------------|
| Baseline (depth=6, vanilla) | 1.0980 | 1.0821 | 1.0950 |
| depth=6, full optimized | **1.0949** | **1.0673** | 1.0779 |
| SSSL window attention only | 1.0961 | 1.0801 | 1.0844 |
| depth=8, optimized schedule | 1.1017 | — | **1.0318** |

On every GPU, the meta-agent's optimized prompt improved val_bpb by ~0.003. Real, consistent, reproducible. But on H100, depth=8 with the optimized schedule hit 1.0318 — a 0.046 improvement over the best depth=6 result on that hardware. Fifteen times larger than the prompt-optimization win.

Good prompts transfer across model families. Architecture choices depend on your hardware. These are different levers.

---

## WOW MOMENT: The H100 Depth=8 Reveal

On A40, depth=8 actively hurt performance. val_bpb went from 1.0980 (baseline) to 1.1017. The A40 didn't have the compute headroom to train a deeper model to convergence within the step budget. The model was underbaked. So depth=8 went into the "doesn't work" column and stayed there.

Then I ran the same config on an H100.

val_bpb: 1.0318. The best result across all three GPUs by a wide margin.

The architecture the A40 had "rejected" was actually the correct architecture. It just needed a bigger GPU to prove it. The meta-agent's Phase 1 rule — always explore architecture before schedule — is vindicated here in a way I didn't anticipate when I designed the benchmark. Architecture depth is a hardware-dependent lever. Whether depth=8 helps or hurts is a function of your GPU budget, not your prompt.

There's also a counterintuitive footnote: the L40S completed 1,891 training steps on the same model. The H100 completed 1,699. The smaller, cheaper GPU ran more steps. At sub-50M parameter scale, kernel overhead dominates — H100's advantages are in throughput on large tensors, not on tiny models where every forward pass is a rounding error in GPU time. For anything under 50M parameters, an L40S at $0.79/hr is a better deal than an H100 at $2.99/hr.

The meta-agent optimized the prompt. The prompt told us to look at architecture first. The architecture decision depended on the hardware. The right answer was always hardware-conditional. The meta-agent didn't know that — but the order of investigation it enforced led us there.

---

## Holdout: The Honest Assessment

Holdout ran twice — baseline and evo_015. The 10 holdout tasks were untouched throughout the optimization run:

| Holdout | Baseline | evo_015 |
|---------|----------|---------|
| Pass rate | 8/10 (80%) | 9/10 (90%) |

task_05 failed in both versions and probably represents a genuinely hard case the current guidance doesn't cover. task_16 stayed passing. Everything else transferred cleanly from the search set.

The 90% holdout result is the number I actually trust. The 100% search-set result could have baked in search-set overfitting. The holdout confirms the gains are real.

---

## What's Next

A few threads worth pulling.

The proposer is the bottleneck. The outer loop improved the inner agent by 20 percentage points. But the proposer itself — reading failure traces and writing configs — ran on default instructions the whole time. What happens if you run meta-agent on the meta-agent? Optimize the proposer's own prompts for "fewer turn-limit failures" and "faster convergence." I don't have an answer yet.

Unlabeled traces. This experiment used a fully labeled benchmark. In practice, you often don't have ground truth. The canvas-org framework supports LLM-judge scoring on unlabeled production traces. Their tau-bench results (67% to 87% via judge-based search) suggest it works. Worth trying on a real task with no known ground truth.

Composing discovered rules. The phase-ordering and context-override rules the meta-agent found are general enough that I could apply them to a different ML domain without modification. Rules discovered on one benchmark might transfer to another. That's a different kind of leverage than prompt engineering.

---

## Try It Yourself

The framework is open source:

```bash
git clone https://github.com/canvas-org/meta-agent
cd meta-agent
pip install -e .

python -m meta_agent.outer_loop \
    --benchmark benchmarks/tau3/benchmark.yaml \
    --iterations 10 \
    --model <your-inner-model>
```

The ml-advisor benchmark I built (all 30 tasks, ground truth, verifier) is in `benchmarks/ml-advisor/` in my project repo. If you want to run the same optimization — same tasks, same verifier, same setup — it's all there.

The 90-second terminal demo of the whole pipeline is in the repo as well.

What you need: an agent that does something, a way to evaluate whether it did it correctly, and ~$10–15 in API budget for 8–10 iterations. Add another $5 in GPU time if you want to validate the winners on real hardware.

What I'd genuinely want to know: if you run this on a different domain, what rules does the meta-agent discover? Are they similarly "obvious in retrospect" or genuinely surprising? Hit the comments.

---

**Repo:** [github.com/abhid1234/meta-agent-improver](https://github.com/abhid1234/meta-agent-improver)
**Framework:** [github.com/canvas-org/meta-agent](https://github.com/canvas-org/meta-agent)
**Part 1 (the overnight autoresearch run):** [open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent)
