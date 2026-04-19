# I Let AI Optimize the AI Researcher Itself — Here's What It Discovered

### Building a meta-agent that gets better at advising ML experiments by learning from its own failures.

---

A few weeks ago I ran 16 autonomous ML experiments overnight on an A40 GPU. An LLM played researcher: reading experiment logs, proposing hyperparameter changes, running training runs, iterating. By morning it had improved `val_bpb` from 1.098 to 1.095 — sliding window attention, warmdown ratio of 0.7, a 5% LR floor — for about $15 in API costs. ([Part 1 is here](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent) if you want the full story.)

The natural next question: what if I let AI optimize the AI researcher itself?

That's what this post is about. I took the same domain — ML hyperparameter search — and built a meta-agent that reads its own failure traces and rewrites its own guidance to do better. The result: accuracy on the search set went from 80% to 100% across 21 iterations. Cost: ~$26 total (~$21 API + ~$5 GPU). And along the way, the system independently rediscovered several things that experienced ML engineers know intuitively but rarely write down — and then validated those discoveries on real GPU hardware across three different machines.

---

## How Meta-Agents Work

The idea is simple. You have an inner agent doing some task. You have a way to evaluate whether it did the task correctly. And you have an outer loop — the meta-agent — that reads the failure traces and proposes improvements to the inner agent's instructions.

```
                 ┌─────────────────────┐
                 │    Outer Loop       │
                 │  (proposer model)   │
                 │                     │
                 │  reads failure      │
                 │  traces → rewrites  │
                 │  system prompt      │
                 └────────┬────────────┘
                          │ new prompt
                 ┌────────▼────────────┐
                 │    Inner Agent      │
                 │  (inner model)      │
                 │                     │
                 │  reads experiment   │
                 │  history → proposes │
                 │  next hyperparam    │
                 └────────┬────────────┘
                          │ proposal
                 ┌────────▼────────────┐
                 │  Deterministic      │
                 │  Verifier           │
                 │                     │
                 │  checks against     │
                 │  ground truth       │
                 └─────────────────────┘
```

The outer loop ran 21 iterations total. Two iterations (evo_002 and evo_003) were proposer failures — the proposer model hit turn limits before producing a complete config. Each successful iteration reads all the failure traces from the previous run, identifies a recurring pattern, and writes one targeted change to the inner agent's system prompt. If the new prompt scores better on a search set of tasks, it becomes the new baseline. If not, it's discarded.

The framework I used is [canvas-org/meta-agent](https://github.com/canvas-org/meta-agent), which handles the loop, file-based memory, and candidate tracking. Each harness candidate — config, traces, scores — gets written to disk so the proposer has full history when deciding what to try next.

---

## Building the Benchmark

The inner agent's job: given an experiment log (results from prior training runs) and the training code (`train.py`), propose the single best next hyperparameter change.

I built 30 tasks from the 16 real experiments I ran in Part 1, plus 5 synthetic extensions to cover edge cases. Each task has:

- `results.tsv` — the experiment history up to that point
- `train.py` — the training code with all tunable parameters
- `context.md` — a short brief describing what's been learned so far and what to focus on next
- A ground truth answer: the parameter change that was actually best

The ground truth was determined by what the real experiments found — sliding window attention before warmdown, warmdown before LR floor, LR floor at 0.05 not 0.1. Tasks vary in difficulty: early-stage tasks (architecture unexplored) are relatively straightforward. Late-stage tasks with explicit phase directives in `context.md` are harder because they require the agent to override its default instincts.

I split 20 tasks for the search set (where the optimizer can iterate) and 10 for holdout (evaluated only twice: baseline and final).

The verifier is deterministic — it checks whether the proposed parameter and value match the ground truth exactly. No LLM judge. Either you got it right or you didn't.

---

## The Optimization Loop

**Baseline (vanilla inner model, no guidance): 80% on search set (24/30)**

No system prompt beyond the default. The inner model reads the files and proposes something. It gets most of the straightforward cases right — architecture exploration is intuitive enough. It fails on tasks that require understanding phase ordering or interpreting `context.md` directives correctly.

**The outer loop then ran 21 iterations.** Two (evo_002 and evo_003) were proposer failures. The extended run revealed something important: progress isn't monotonic, and the final 5 percentage points were the hardest to earn.

| Iteration | Pass Rate | What happened |
|-----------|-----------|---------------|
| baseline | 80% (24/30) | Vanilla inner model |
| evo_001 | 85% (17/20) | Phase ordering discovered |
| evo_002 | — | Proposer hit turn limit |
| evo_003 | — | Proposer hit turn limit |
| evo_004 | 85% (17/20) | Added exception clause — subtle regression introduced |
| evo_007 | 80% (16/20) | Regression from over-enforced ordering |
| evo_008 | **95% (19/20)** | Context-awareness fixed, exception removed |
| evo_009–014 | 85–90% | Plateau — proposer tuning around edges |
| **evo_015** | **100% (20/20)** | Baseline-row exclusion bug discovered |
| evo_016 | **100%** | Confirmed |
| evo_018 | **100%** | Confirmed again |

The two proposer failures are worth noting. They happened because the proposer model tried to reason through the full failure analysis in a single pass and ran out of turns before writing the config. This is a known failure mode in agentic systems — complex reasoning tasks need explicit structure or the agent runs long. The meta-agent framework retries these automatically, but it's a reminder that the proposer is itself an agent that can fail.

---

## What the Meta-Agent Discovered

After 21 iterations, the final system prompt — what I'm calling `_ADVISOR_GUIDANCE` — encodes four rules that the meta-agent worked out from its failure traces:

```python
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
   - FINAL_LR_FRAC first trial: use 0.05 (a 5% floor). This is the
     conservative, well-calibrated starting point. Do NOT use 0.1 or higher
     on a first trial — a high LR floor prevents sufficient decay and tends to
     hurt final performance.
5. Regularization — ADAM_BETAS, WEIGHT_DECAY

A phase is active if any parameter within it is untried AND the current context
does not explicitly state that phase is exhausted.

## Step 3 — Select the phase and pick the best parameter

First, scan context.md (the "Key Learnings" and "Your Task" sections) for any
explicit directive about which parameter area to explore. Examples of explicit
directives:
- "The LR schedule still has an unexplored dimension"
- "Focus on LR schedule parameters that haven't been tried"
- "Focus on schedule and optimization"
- "Architecture changes are exhausted — move to regularization"

If you find such a directive naming a specific parameter category, start from
that phase — do not explore earlier phases even if they have untried parameters.
The task context is authoritative about where the experimenter wants to go next.

If context.md gives no specific phase directive (e.g., just "propose the best
next change" or "focus on unexplored knobs"), use the standard rule: choose the
earliest active phase from Step 2. Do NOT jump to a later phase (e.g. LR
schedule) while an earlier phase still has unexplored parameters.

## Step 4 — Treat train.py code comments as hints, not commands
Code comments that suggest specific values (e.g. "try X = 0.05") are reminders of
candidates, not the recommended next step. Always verify the suggestion is
appropriate for the current exploration phase before following it.

## Step 5 — Write proposal.json with the chosen parameter
Be precise about old_value (the current value in train.py) and new_value.
"""
```

The four rules it converged on:

**1. Phase-ordered exploration.** Architecture before training dynamics, training dynamics before model capacity, model capacity before LR schedule, LR schedule before regularization. Don't jump to LR schedule while architecture is unexplored. This is what experienced ML researchers do intuitively, but the baseline inner model had no concept of it — it would propose LR changes on run 3 if the context mentioned LR anywhere.

**2. Context-aware phase overrides.** When `context.md` explicitly names a parameter category ("The LR schedule still has an unexplored dimension"), skip to that phase regardless of what the default ordering says. The task context is authoritative. This rule was the hardest to get right — more on that below.

**3. LR floor calibration.** Always try FINAL_LR_FRAC=0.05 first. Never 0.1 or higher on a first trial. This is directly from what the real experiments found in Part 1: a 5% LR floor was the sweet spot. The meta-agent encoded this as a hard rule rather than leaving it to the agent to reason about.

**4. Code comments are hints, not commands.** If `train.py` has a comment saying `# try X = 0.05`, that's a candidate to evaluate, not an instruction to follow. The agent should verify that the suggestion is appropriate for the current exploration phase before using it. Without this rule, the inner model would sometimes follow code comments directly, skipping the phase-ordering logic entirely.

What strikes me is that these are all things a senior ML engineer would tell a junior one on their first week. The meta-agent didn't discover anything exotic. It rediscovered standard practice from failure traces.

---

## The Evolution Story: evo_004's Exception Clause

The most instructive failure in the whole run was evo_004.

After evo_001 established phase ordering and got to 85%, the proposer looked at the remaining three failures. Two of them (task_14 and task_18) involved tasks where `context.md` gave an explicit LR schedule directive, but the agent kept following phase ordering and proposing architecture or capacity changes instead. The proposer's diagnosis: we need an exception to the phase ordering rule.

So evo_004 added this to Step 4 of the guidance:

> **Exception:** when a comment in `train.py` names a specific numeric value for an untried parameter, use that value exactly.

This was wrong in a subtle way. The proposer conflated two different signals: `context.md` directives (which are authoritative task-level guidance from the experimenter) and `train.py` code comments (which are just implementation hints from whoever wrote the training code). By treating train.py comments as override-worthy, it created a backdoor that let the agent bypass phase ordering for the wrong reasons.

The result: evo_004 fixed task_18 and task_20, but broke task_15 and task_17. Both new failures happened because the agent saw a numeric value in a train.py comment, invoked the Exception, and jumped to LR schedule while capacity was still unexplored. The Exception was solving the wrong problem.

evo_007 tried a different approach and ended up with a regression back to 80%. The proposer had over-corrected.

evo_008 finally got it right. The fix was twofold: remove the Exception clause entirely, and add explicit guidance in Step 3 about how to read `context.md` for phase directives. The rule became precise: scan the "Key Learnings" and "Your Task" sections for language that names a parameter category. If you find it, that category overrides default phase ordering. If you don't find it, fall back to the standard earliest-active-phase rule.

Result: 95%. One task still failing.

The lesson the proposer learned — and I think this generalizes — is that exceptions breed regressions. The Exception clause in evo_004 was a patch for a symptom (agents not reading context.md carefully enough) rather than a fix for the root cause (no explicit instruction about when context.md overrides phase ordering). Removing the exception and fixing the root cause was harder to reason through, but it was the correct architecture.

### evo_015: The Baseline-Row Bug

After evo_008 hit 95%, the next six iterations (evo_009 through evo_014) plateaued between 85% and 90% on intermediate configurations before stabilizing. Only task_02 kept failing. The proposer looked at this single holdout failure and analyzed 6 configs across all prior iterations. What it found was subtle.

The `results.tsv` file always contains a "baseline" row — the very first row, describing the model's starting configuration: warmdown=0.5, LR_floor=0. This row exists to anchor the experiment history. But the prompt's Step 1 was instructing the inner model to treat every row in results.tsv as a "tried experiment." The baseline row was being read as if warmdown=0.5 and LR_floor=0 had already been deliberately tried and rejected.

That made the inner model mark those parameters as TRIED, which caused it to skip Phase 2 (training dynamics) entirely — even when it was the correct next phase. Task_02 required proposing warmdown adjustment, and the model thought it had already been covered.

The fix was surgical: reword Step 1 to explicitly exclude baseline rows from the TRIED list (+64 characters), while compressing Step 3's fallback clause to avoid net prompt growth (-146 characters). Net change: 82 characters shorter.

That's the surprising meta-lesson from evo_015: at 95% → 100%, the proposer was operating at the inner model's attention boundary. Any net addition to prompt length risked breaking tasks that had been working fine — the model's attention gets redistributed. Length-neutral editing became a hard constraint. The final step from 95% to 100% wasn't about adding a new rule. It was about fixing a data interpretation bug while keeping the prompt the same size.

This generalizes: prompt surgery is precise work. Adding guidance is easy. Adding guidance *without regressing anything else* is the real craft.

---

## Holdout Results: The Honest Assessment

I ran holdout twice — baseline and evo_015. Here's what happened on the 10 holdout tasks that neither the optimizer nor the inner agent had seen during the search phase:

| Task | Baseline | evo_015 |
|------|----------|---------|
| task_05 | FAIL | FAIL |
| task_08 | PASS | PASS |
| task_11 | PASS | PASS |
| task_12 | PASS | PASS |
| task_16 | PASS | PASS |
| task_19 | FAIL | PASS |
| task_21 | PASS | PASS |
| task_24 | PASS | PASS |
| task_27 | PASS | PASS |
| task_29 | PASS | PASS |
| **Total** | **8/10 (80%)** | **9/10 (90%)** |

The search set went 80% → 100%. The holdout set went 80% → 90%. That's genuine generalization — the rules the meta-agent discovered aren't just memorized patterns for the search tasks; they're actually better guidance.

task_05 failing in both versions probably represents a genuinely hard case — one where the correct answer requires reasoning the current guidance doesn't cover. Everything else transferred cleanly.

The 10-point holdout improvement (80% to 90%) is the number I actually trust. The 100% on the search set could have search-set overfitting baked in. The holdout result confirms the gains are real.

---

## Cross-Model Transfer

The optimized prompt was developed with one specific inner model. The obvious question: does it work anywhere else?

I ran the same `_ADVISOR_GUIDANCE` prompt — unchanged — on Llama 3.1 8B and Mistral Small 24B via OpenRouter. No framework changes, no model-specific tuning.

| Model | Baseline | With optimized prompt |
|-------|----------|-----------------------|
| Vanilla inner model | 80% | 100% (after 21 iterations) |
| Llama 3.1 8B | 87% (26/30) | 87% — no net gain |
| Mistral Small 24B | 87% (26/30) | **90% (27/30)** |

Llama 3.1 8B: same pass rate, but different tasks pass and fail. The prompt reorganized where it was right and wrong without changing the total count. Mistral Small 24B gained 3 percentage points — matching the 90% holdout result the baseline inner model needed 21 rounds of meta-optimization to achieve.

The key finding: the rules the meta-agent discovered (phase ordering, context override, baseline-row exclusion) are not model-specific. They describe what good ML research reasoning looks like, not what any one model needs to hear. They transferred cleanly across model families.

Prompts are portable capital. A good prompt is worth more than a larger model.

---

## GPU Validation — The Real Payoff

The prompt optimization was interesting. What happened when I actually ran the top proposals on hardware is where the story gets worth telling.

I took the three highest-confidence proposals from the optimized agent — depth=6 with full optimization schedule, depth=8 with optimized schedule, and SSSL window attention alone — and ran them as actual autoresearch experiments on three GPU classes.

| Config | A40 (val_bpb) | L40S (val_bpb) | H100 (val_bpb) |
|--------|---------------|----------------|----------------|
| Baseline (depth=6, vanilla) | 1.0980 | 1.0821 | 1.0950 |
| depth=6, full optimized | **1.0949** | **1.0673** | 1.0779 |
| SSSL window attention only | 1.0961 | 1.0801 | 1.0844 |
| depth=8, optimized schedule | 1.1017 | — | **1.0318** |

**A40** (the original Part 1 setup): depth=6 with the full optimization schedule won at val_bpb 1.0949. SSSL window attention on its own helped some, but the full config beat it. Same conclusion as Part 1 reached after 16 runs.

**L40S** (new, via RunPod at $0.79/hr): same winner — depth=6 optimized hit 1.0673, the best result across all three machines for that config. SSSL window attention alone didn't help here the same way it helped on A40. On A40, freeing up compute via sparse attention gave the training more headroom. L40S already had that headroom, so the gain disappeared.

**H100** (via RunPod Secure Cloud at $2.99/hr): ran 5 experiments. Depth=6 optimized hit 1.0779 — better than A40 baseline but not as good as L40S for this config. Then depth=8 with the optimized schedule hit **1.0318**. That's a 0.046 val_bpb improvement over the best depth=6 result on the same hardware. Roughly 15× larger than the prompt-optimization win from 21 iterations of meta-agent work.

This result connects directly back to Part 1. In that run, depth=8 on A40 *hurt* — 1.1017 vs 1.0980 baseline — because the A40 didn't have enough compute budget to train a depth=8 model to convergence within the step budget. The model was underbaked. On H100, depth=8 has the compute headroom to actually train, and it wins by a wide margin.

The meta-agent's discovered Phase 1 rule — always explore architecture before schedule — is vindicated here. Architecture depth is a hardware-dependent lever. Whether depth=8 helps or hurts is a function of your GPU budget, not your prompt.

**The surprise data point:** L40S completed 1,891 training steps. H100 completed 1,699 steps on the same model. The smaller, cheaper GPU ran *more* steps. At sub-50M model scale, kernel overhead dominates — H100's advantages are in throughput on large tensors, not on tiny models where every forward pass is a rounding error in GPU time. For anything under 50M parameters, an L40S at $0.79/hr is a better deal than an H100 at $2.99/hr.

The honest framing: the prompt-optimization result (+0.003 val_bpb) is real but modest. The architecture-plus-hardware insight (depth=8 on H100: +0.046 val_bpb) is where the bigger lesson lives. The meta-agent's strategy of prioritizing architecture changes before schedule changes is vindicated precisely because the architecture lever is 15× more powerful — when you have the hardware to use it.

The meta-agent optimized the prompt. The prompt told us to look at architecture first. The architecture decision depended on the hardware. The right answer was always hardware-conditional; the meta-agent didn't know that, but the order of investigation it enforced led us to find out.

---

## What I Learned

**The barrier to meta-learning is now ~$26.** That's what the whole run cost — ~$21 in API calls plus ~$5 in GPU time for validation. You don't need a research lab. You need a benchmark, a verifier, an outer loop, and an honest holdout set.

**Prompts are programs.** The `_ADVISOR_GUIDANCE` string is a decision procedure: enumerate state (excluding baseline rows), identify phase, check for context overrides, pick parameter, write output. It was discovered iteratively from failure traces, not designed top-down. The meta-agent wrote better structured prompts than I would have written by hand, because it was working from evidence.

**Exceptions are a code smell in prompts, not just code.** The evo_004 story is a clean illustration. When you find yourself adding an "Exception" clause to a prompt rule, that's usually a sign you haven't understood the underlying problem yet. evo_008 removed the exception and fixed the root cause. The prompt got cleaner and the accuracy went up.

**Holdout discipline matters.** I was tempted to look at holdout results after each iteration to understand what was happening. I didn't. If I had, I would have started implicitly optimizing for holdout, which would have made the final results meaningless. Run holdout once at the start and once at the end. That's it.

**Good prompts transfer across models; good architectures don't transfer across hardware.** The optimized prompt transferred to Mistral Small 24B with zero modification. The depth=8 architecture required H100 to work — on A40 it actively hurt. Optimization schedules are hardware-independent. Architecture is hardware-dependent. Know which lever you're pulling.

---

## Try It Yourself

The meta-agent framework is open source: [github.com/canvas-org/meta-agent](https://github.com/canvas-org/meta-agent)

```bash
git clone https://github.com/canvas-org/meta-agent
cd meta-agent
pip install -e .

python -m meta_agent.outer_loop \
    --benchmark benchmarks/tau3/benchmark.yaml \
    --iterations 10 \
    --model <inner-model>
```

The ml-advisor benchmark I built for this post (all 30 tasks, ground truth, verifier) is in the `benchmarks/ml-advisor/` directory of my project. If you want to run the same optimization I did, it's all there.

What you need to bring: an agent that does something, a way to evaluate whether it did it correctly, and about $10–15 in API budget for 8–10 iterations. Add another $5 in GPU time if you want to validate the winners on real hardware.

I also recorded a 90-second terminal demo of the whole pipeline — from baseline through 21 iterations to the GPU validation. It's in the repo at [github.com/abhid1234/meta-agent-improver](https://github.com/abhid1234/meta-agent-improver/blob/main/gpu_validation/meta-agent-demo-music.mp4).

---

## What's Next

A few things I want to explore:

**The proposer is the bottleneck.** The outer loop improved the inner agent's accuracy by 20 points. But the proposer itself — reading failure traces and writing new configs — is just running with default instructions. What happens if you run meta-agent on the meta-agent? Run the outer loop on the proposer's own prompts, optimizing for "fewer turn-limit failures" and "faster convergence." I don't know the answer yet.

**Unlabeled traces.** This experiment used a fully labeled benchmark — every task had a ground truth answer. In practice, you often don't have that. The canvas-org meta-agent framework is designed to work with an LLM judge scoring unlabeled production traces, which is the more realistic setting. Their tau-bench results (67% to 87% with judge-based search) suggest this works. I want to try it on a real task with no ground truth.

**Composing discovered rules.** The phase-ordering and context-override rules the meta-agent found are general enough that I could apply them to a different ML experiment domain without modification. This suggests that iterative prompt optimization can produce reusable domain knowledge, not just task-specific patches. Worth exploring whether rules from one benchmark transfer to another.

---

First I let AI optimize a neural network. Then I let AI optimize the AI researcher itself.

That's the state of the art in April 2026.

---

*The code and benchmark are at [github.com/canvas-org/meta-agent](https://github.com/canvas-org/meta-agent). Part 1 of this series — the original overnight autoresearch run — is [here](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent).*
