# Social Media Posts: Meta-Agent ML Advisor Optimization

## 1. LinkedIn Post

Last month I ran 16 ML experiments overnight for $15 using Karpathy's autoresearch setup. This month I let AI optimize the AI researcher itself.

Starting point: 80% on a 30-task ML benchmark. After 21 iterations of outer-loop meta-optimization: **100% on the search set, 90% on held-out tasks**. Cost: ~$26 total.

But the result that surprised me most had nothing to do with prompts.

**The architecture-vs-hardware insight:**
When I validated on three GPU classes (A40, L40S, H100), the prompt optimization contributed just 0.003 val_bpb on real hardware. Meanwhile, switching model depth from 6 to 8 layers delivered **0.046 val_bpb improvement on the H100 — roughly 15× larger**. Depth=8 actually *hurt* on the A40. Same code, different hardware, opposite winner.

The framing I landed on: **prompts are portable capital, but architecture is hardware-dependent.** The meta-agent's own discovery — phase-ordered exploration, architecture evaluated first — turns out to be right for exactly this reason.

**The four rules the agent derived on its own:**
1. Phase-ordered exploration: architecture → dynamics → capacity → LR schedule → regularization
2. Context-aware phase overrides from task instructions
3. FINAL_LR_FRAC = 0.05 first, never 0.1+
4. Length-neutral prompt editing — adding N characters means removing N elsewhere

**Cross-model transfer check:** Applied the same optimized prompt to Mistral Small 24B via OpenRouter. Benchmark score went from 87% → 90%. Prompts generalize; the architecture lesson does not.

There's a 90-second terminal demo in the repo. Framework credit: canvas-org/meta-agent.

Code: https://github.com/abhid1234/meta-agent-improver
Full write-up: [BLOG_URL]

#AI #MachineLearning #GPU #MLOps #AIAgents

---

## 2. X/Twitter Thread

**Main Tweet:**
Last month I let AI optimize a neural network. This month I let AI optimize the AI researcher itself.

Result: 80% → 100% on a 30-task benchmark.

But the bigger insight: prompts don't transfer across hardware. A single architecture change was 15× more impactful.

[BLOG_URL]

---

**Tweet 2:**
The setup: 30 benchmark tasks derived from real ML experiments. A deterministic verifier scores each run. An outer agent watches failures, rewrites the inner agent's system prompt, and repeats.

21 iterations. 100% on search set. 90% on held-out tasks the optimizer never saw.

---

**Tweet 3:**
The 4 rules the meta-agent discovered — without being told:

1. Phase ordering: architecture → dynamics → capacity → LR → regularization (broad before narrow)
2. Context overrides: task instructions can jump the queue
3. LR calibration: FINAL_LR_FRAC = 0.05 first, never 0.1+
4. Length-neutral edits: add N chars, cut N elsewhere — attention budgets are real

---

**Tweet 4:**
Here's where hardware enters.

Validated on 3 GPU classes. The prompt optimization? +0.003 val_bpb on real hardware — real, but small.

Depth=8 vs depth=6? +0.046 on H100. That's ~15× bigger.

Plot twist: depth=8 *hurt* on A40 (-0.004). Same code. Different GPU. Opposite winner.

The meta-agent's instinct to evaluate architecture first is vindicated — because architecture is the biggest lever when you have the right hardware.

---

**Tweet 5:**
Does the optimized prompt transfer across models?

Applied it to Mistral Small 24B via OpenRouter. Benchmark: 87% → 90%.

Prompts are portable capital. Architecture choices are not.

---

**Tweet 6:**
Total cost: ~$26 (~$21 API + ~$5 RunPod GPU time).

90-second terminal demo in the repo. Framework: canvas-org/meta-agent.

Code: https://github.com/abhid1234/meta-agent-improver
Part 1 (16 experiments, $15, A40): [BLOG_URL]

---

## 3. Hacker News (Show HN)

**Title:**
Show HN: Meta-agent gets ML advisor to 100%; but hardware changed the winner

**Description:**
Built a two-tier agent system on top of the canvas-org/meta-agent framework. An outer loop watches an inner ML-advisor agent fail, rewrites its system prompt, and repeats. The benchmark: 30 tasks derived from real ML hyperparameter experiments, scored by a deterministic verifier.

Baseline: 80%. After 21 outer-loop iterations: 100% on the search set, 90% on held-out tasks the optimizer never touched.

Then I validated on three GPU classes (A40, L40S, H100). The prompt optimization contributed +0.003 val_bpb on real hardware — meaningful, but small. A depth change from 6 → 8 layers gave +0.046 val_bpb on H100 — roughly 15× larger. That same depth=8 config hurt on the A40 (-0.004). Architecture and hardware are coupled; prompts are not.

Cross-model transfer: the optimized prompt applied to Mistral Small 24B via OpenRouter moved the benchmark from 87% → 90%, confirming prompts generalize across models even when architecture insights don't.

Total cost: ~$26 ($21 API + $5 GPU on RunPod). 90-second terminal demo in the repo.

Framework: https://github.com/canvas-org/meta-agent
Repo + benchmark + results: https://github.com/abhid1234/meta-agent-improver
Full write-up: [BLOG_URL]
