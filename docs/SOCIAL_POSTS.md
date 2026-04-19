## LinkedIn Post

I've been tinkering with meta-agents — systems that optimize other AI agents by reading their failure traces and rewriting their instructions. After 21 iterations on a 30-task ML benchmark, the inner model went from 80% to 100% accuracy on the search set, 90% on holdout. Total cost: $26.

But the most important finding had nothing to do with the prompt.

What I built: a meta-optimization loop over a small ML hyperparameter advisor. An outer model reads failure traces from the inner agent, proposes edits to its system prompt, and keeps whatever scores better. No fine-tuning. No gradient updates. Just a proposer reading errors and writing better instructions.

What makes it different:

→ Deterministic verifier — no LLM judge, ground truth only. Either you got it right or you didn't.
→ Honest holdout — 10 tasks locked away, evaluated exactly twice (baseline and final). The 90% holdout result is the number I trust.
→ Cross-model transfer — the optimized prompt applied unchanged to Mistral Small 24B lifted it from 87% → 90%. Prompts describe what good reasoning looks like, not what one specific model needs to hear.
→ GPU validation — ran the top proposals on A40, L40S, and H100 via RunPod. The prompt wins were real (~0.003 val_bpb). The hardware wins were 15× larger.

What I built from scratch:
• 30-task benchmark from 16 real ML experiments ($15, A40 GPU) run in Part 1
• Deterministic verifier with exact ground-truth matching
• GPU validation harness across three machine classes

What I learned:

• Exceptions are a code smell in prompts, not just code. evo_004 added an "Exception" clause that fixed two tasks and broke two others. evo_008 removed it and fixed the root cause. Accuracy went up.
• At 95% accuracy, prompt edits must be length-neutral. Any net addition redistributes the inner model's attention and breaks tasks that were already passing. The final fix from 95% → 100% shrank the prompt by 82 characters while fixing a data interpretation bug.
• Architecture choices are hardware-conditional. depth=8 hurt on A40 (underbaked, not enough compute). On H100, it hit the best val_bpb across all configs by a wide margin. The meta-agent's rule to explore architecture first turned out to be exactly right — because architecture is the lever that depends on your hardware.
• For sub-50M parameter models, L40S at $0.79/hr ran more training steps than H100 at $2.99/hr. Kernel overhead dominates at small scale.

The benchmark, verifier, and all 21 evolution configs are in the repo. If you've run something similar — or tried meta-optimization on a different domain — I'd genuinely want to know what rules your outer loop discovered.

#MLOps #PromptEngineering #MachineLearning #OpenSource #MetaLearning

---

### First Comment

Links:

→ Repo: https://github.com/abhid1234/meta-agent-improver
→ Framework: https://github.com/canvas-org/meta-agent
→ Part 1 (autoresearch): https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent
→ Full write-up: [BLOG_URL]

---

### Launch Checklist

- Post Tuesday–Thursday morning (7:30–8:30 AM or 12:00–1:00 PM local)
- Upload the demo video natively (NOT a YouTube link — native video gets 3–5× the reach)
- Post the First Comment immediately after publishing so the links are visible in the thread

---

## Tweet / X Post

### Short Tweet

I let AI optimize an AI researcher. After 21 iterations it hit 100%. Then I ran it on 3 GPUs and found the architecture choice mattered 15× more than the prompt.

→ 80% → 100% on search set, 90% on holdout
→ $26 total ($21 API + $5 GPU)
→ depth=8 on H100: +0.046 val_bpb vs +0.003 for the prompt win
→ optimized prompt transferred to Mistral Small 24B with zero changes

https://github.com/abhid1234/meta-agent-improver

#MLOps #PromptEngineering

---

### Long Tweet

I let AI optimize an AI researcher. After 21 iterations it hit 100% on the search set. Then I validated on real hardware and found the prompt optimization was the least interesting result.

What the meta-agent did:
→ Read failure traces from an inner ML advisor agent
→ Proposed edits to its system prompt, kept whatever scored better
→ 80% → 100% on 30-task search set across 21 iterations
→ 90% on locked holdout (the number I actually trust)
→ $26 total: ~$21 API + ~$5 GPU

The four rules it independently discovered:
→ Explore architecture before training dynamics, dynamics before LR schedule — don't jump phases
→ When context.md says "focus on LR schedule," skip to LR schedule regardless of what phase ordering says
→ Always try FINAL_LR_FRAC=0.05 first — never 0.1 on a first trial
→ Exclude the baseline row from "tried experiments" — it's a starting state, not a tested value

Technical notes worth knowing:

Exceptions are a code smell in prompts. evo_004 added an "Exception" clause that fixed two tasks and broke two others. Removing it and fixing the root cause (evo_008) got to 95%. The exception was a patch for a symptom, not a fix.

At 95%, prompt edits must be length-neutral. The inner model's attention gets redistributed with any net addition — tasks that were passing start failing. The final 95% → 100% fix shrank the prompt by 82 characters while correcting a data interpretation bug.

The cross-model transfer: same prompt, unchanged, applied to Mistral Small 24B via OpenRouter → 87% to 90%. Applied to Llama 3.1 8B → same pass rate, different tasks. The rules describe good ML reasoning, not one model's quirks.

The GPU results: prompt optimization gave +0.003 val_bpb consistently across A40/L40S/H100. Architecture change (depth=6 → depth=8) on H100 gave +0.046 val_bpb — 15× larger. depth=8 had hurt on A40 (not enough compute headroom to train to convergence). On H100, it was the best config by a wide margin. Architecture is hardware-conditional. Prompts transfer. These are different levers.

Surprise: L40S at $0.79/hr ran 1,891 training steps on the same model. H100 at $2.99/hr ran 1,699. At sub-50M parameters, kernel overhead dominates. L40S is the better deal for small models.

Repo (benchmark + all 21 configs): https://github.com/abhid1234/meta-agent-improver
Framework: https://github.com/canvas-org/meta-agent
Part 1 (the original overnight autoresearch run): https://open.substack.com/pub/abhid/p/i-ran-an-autonomous-ai-research-agent

#MLOps #PromptEngineering #MachineLearning
