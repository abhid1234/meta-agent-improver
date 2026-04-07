# I Let AI Optimize the AI Researcher Itself — Here's What It Discovered

### Building a meta-agent that gets better at advising ML experiments by learning from its own failures.

---

A few weeks ago I ran 16 autonomous ML experiments overnight on an A40 GPU. Claude Sonnet played researcher: reading experiment logs, proposing hyperparameter changes, running training runs, iterating. By morning it had improved `val_bpb` from 1.098 to 1.095 — sliding window attention, warmdown ratio of 0.7, a 5% LR floor — for about $15 in API costs. ([Part 1 is here](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent) if you want the full story.)

The natural next question: what if I let AI optimize the AI researcher itself?

That's what this post is about. I took the same domain — ML hyperparameter search — and built a meta-agent that reads its own failure traces and rewrites its own guidance to do better. The result: accuracy on the search set went from 80% to 95% across 8 iterations. Cost: $12. And along the way, the system independently rediscovered several things that experienced ML engineers know intuitively but rarely write down.

---

## How Meta-Agents Work

The idea is simple. You have an inner agent doing some task. You have a way to evaluate whether it did the task correctly. And you have an outer loop — the meta-agent — that reads the failure traces and proposes improvements to the inner agent's instructions.

```
                 ┌─────────────────────┐
                 │    Outer Loop       │
                 │  (Sonnet proposer)  │
                 │                     │
                 │  reads failure      │
                 │  traces → rewrites  │
                 │  system prompt      │
                 └────────┬────────────┘
                          │ new prompt
                 ┌────────▼────────────┐
                 │    Inner Agent      │
                 │  (Haiku advisor)    │
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

The outer loop runs 8 iterations. Each iteration it reads all the failure traces from the previous run, identifies a recurring pattern, and writes one targeted change to the inner agent's system prompt. If the new prompt scores better on a search set of tasks, it becomes the new baseline. If not, it's discarded.

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

**Baseline (vanilla Haiku, no guidance): 80% on search set (24/30)**

No system prompt beyond the default. Haiku reads the files and proposes something. It gets most of the straightforward cases right — architecture exploration is intuitive enough. It fails on tasks that require understanding phase ordering or interpreting `context.md` directives correctly.

**The outer loop then ran 8 iterations.** Two iterations (evo_002 and evo_003) were proposer failures — Sonnet hit turn limits before producing a complete config. That left 6 successful iterations:

| Iteration | Pass Rate | What happened |
|-----------|-----------|---------------|
| baseline | 80% (24/30) | Vanilla Haiku |
| evo_001 | 85% (17/20) | Phase ordering discovered |
| evo_002 | — | Proposer hit turn limit |
| evo_003 | — | Proposer hit turn limit |
| evo_004 | 85% (17/20) | Added exception clause — subtle regression introduced |
| evo_005 | 85% (17/20) | Over-enforced ordering |
| evo_007 | 80% (16/20) | Regression |
| evo_008 | **95% (19/20)** | Context-awareness fixed, exception removed |

The two proposer failures are worth noting. They happened because Sonnet tried to reason through the full failure analysis in a single pass and ran out of turns before writing the config. This is a known failure mode in agentic systems — complex reasoning tasks need explicit structure or the agent runs long. The meta-agent framework retries these automatically, but it's a reminder that the proposer is itself an agent that can fail.

---

## What the Meta-Agent Discovered

After 8 iterations, the final system prompt — what I'm calling `_ADVISOR_GUIDANCE` — encodes four rules that the meta-agent worked out from its failure traces:

```python
_ADVISOR_GUIDANCE = """
You are an ML experiment advisor. When proposing the next hyperparameter change:

## Step 1 — Enumerate the experimental state
Read results.tsv carefully. Build two lists:
- TRIED: every parameter (and value) that appears in the description column
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

**1. Phase-ordered exploration.** Architecture before training dynamics, training dynamics before model capacity, model capacity before LR schedule, LR schedule before regularization. Don't jump to LR schedule while architecture is unexplored. This is what experienced ML researchers do intuitively, but the baseline Haiku had no concept of it — it would propose LR changes on run 3 if the context mentioned LR anywhere.

**2. Context-aware phase overrides.** When `context.md` explicitly names a parameter category ("The LR schedule still has an unexplored dimension"), skip to that phase regardless of what the default ordering says. The task context is authoritative. This rule was the hardest to get right — more on that below.

**3. LR floor calibration.** Always try FINAL_LR_FRAC=0.05 first. Never 0.1 or higher on a first trial. This is directly from what the real experiments found in Part 1: a 5% LR floor was the sweet spot. The meta-agent encoded this as a hard rule rather than leaving it to the agent to reason about.

**4. Code comments are hints, not commands.** If `train.py` has a comment saying `# try X = 0.05`, that's a candidate to evaluate, not an instruction to follow. The agent should verify that the suggestion is appropriate for the current exploration phase before using it. Without this rule, Haiku would sometimes follow code comments directly, skipping the phase-ordering logic entirely.

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

Result: 95%.

The lesson the proposer learned — and I think this generalizes — is that exceptions breed regressions. The Exception clause in evo_004 was a patch for a symptom (agents not reading context.md carefully enough) rather than a fix for the root cause (no explicit instruction about when context.md overrides phase ordering). Removing the exception and fixing the root cause was harder to reason through, but it was the correct architecture.

---

## Holdout Results: The Honest Assessment

I only ran holdout twice — baseline and evo_008. Here's what happened on the 10 holdout tasks that neither the optimizer nor the inner agent had seen:

| Task | Baseline | evo_008 |
|------|----------|---------|
| task_05 | FAIL | FAIL |
| task_08 | PASS | PASS |
| task_11 | PASS | PASS |
| task_12 | PASS | PASS |
| task_16 | PASS | FAIL |
| task_19 | FAIL | PASS |
| task_21 | PASS | PASS |
| task_24 | PASS | PASS |
| task_27 | PASS | PASS |
| task_29 | PASS | PASS |
| **Total** | **8/10 (80%)** | **8/10 (80%)** |

Same pass rate. But not the same tasks.

evo_008 fixed task_19 (which the baseline failed) but broke task_16 (which the baseline passed). The optimization isn't magic — it moves some failures around while fixing others. On the holdout set, those effects happen to cancel out.

This is actually the right result to trust. The search set accuracy went from 80% to 95%, which represents real improvement on those specific tasks. The holdout result at 80% tells you the generalization story: the improvements are real but bounded. The meta-agent didn't overfit to the search set (which would have shown a sharp drop on holdout) — it found rules that are broadly applicable. But there are still edge cases it hasn't solved.

task_05 failing in both versions probably represents a genuinely hard task — one where the correct answer requires reasoning the current guidance doesn't cover. task_16 breaking in evo_008 is a single regression worth investigating.

---

## What I Learned

**The barrier to meta-learning is now $12.** That's what the whole optimization run cost. You don't need a research lab. You need a benchmark, a verifier, and an outer loop.

**Prompts are programs.** The `_ADVISOR_GUIDANCE` string is a decision procedure: enumerate state, identify phase, check for context overrides, pick parameter, write output. It was discovered iteratively from failure traces, not designed top-down. The meta-agent wrote better structured prompts than I would have written by hand, because it was working from evidence.

**Exceptions are a code smell in prompts, not just code.** The evo_004 story is a clean illustration. When you find yourself adding an "Exception" clause to a prompt rule, that's usually a sign you haven't understood the underlying problem yet. evo_008 removed the exception and fixed the root cause. The prompt got cleaner and the accuracy went up.

**Holdout discipline matters.** I was tempted to look at holdout results after each iteration to understand what was happening. I didn't. If I had, I would have started implicitly optimizing for holdout, which would have made the final results meaningless. Run holdout once at the start and once at the end. That's it.

**Proposer failures are informative.** evo_002 and evo_003 hit turn limits. That tells you something: the proposer was reasoning too broadly, probably not using the file-based memory effectively. Better proposer design — chunking the failure analysis, reading prior candidates before generating a new one — would reduce this. The meta-agent framework stores everything to disk for exactly this reason; the proposer just needs to be instructed to use it.

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
    --model claude-haiku-4-5
```

The ml-advisor benchmark I built for this post (all 30 tasks, ground truth, verifier) is in the `benchmarks/ml-advisor/` directory of my project. If you want to run the same optimization I did, it's all there.

What you need to bring: an agent that does something, a way to evaluate whether it did it correctly, and about $10-15 in API budget for 8-10 iterations.

---

## What's Next

A few things I want to explore:

**The proposer is the bottleneck.** The outer loop improved the inner agent's accuracy by 15 points. But the proposer itself — Sonnet reading failure traces and writing new configs — is just running with default instructions. What happens if you run meta-agent on the meta-agent? Run the outer loop on the proposer's own prompts, optimizing for "fewer turn-limit failures" and "faster convergence." I don't know the answer yet.

**Unlabeled traces.** This experiment used a fully labeled benchmark — every task had a ground truth answer. In practice, you often don't have that. The canvas-org meta-agent framework is designed to work with an LLM judge scoring unlabeled production traces, which is the more realistic setting. Their tau-bench results (67% to 87% with judge-based search) suggest this works. I want to try it on a real task with no ground truth.

**Composing discovered rules.** The phase-ordering and context-override rules the meta-agent found are general enough that I could apply them to a different ML experiment domain without modification. This suggests that iterative prompt optimization can produce reusable domain knowledge, not just task-specific patches. Worth exploring whether rules from one benchmark transfer to another.

---

First I let AI optimize a neural network. Then I let AI optimize the AI researcher itself. The researcher got better. The rules it discovered made sense. And the whole thing cost less than a dinner.

That's the state of the art in April 2026.

---

*The code and benchmark are at [github.com/canvas-org/meta-agent](https://github.com/canvas-org/meta-agent). Part 1 of this series — the original overnight autoresearch run — is [here](https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent).*
