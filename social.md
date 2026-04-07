# Social Media Posts: Meta-Agent ML Advisor Optimization

## 1. LinkedIn Post

I just published a deep dive on building a **meta-agent that optimizes ML experiment workflows** — and it's wild what emerges when you let AI tune itself.

The backstory: I ran 16 ML experiments on hyperparameter tuning using Claude Haiku (inner agent proposing next steps) and Sonnet (outer loop refining the prompts). The baseline? 80% success on the search set. After meta-optimization? 95%.

**What's remarkable isn't the improvement—it's *how* it happened:**
- The outer agent independently discovered phase-ordered exploration (broad exploration → fine-grained refinement)
- It learned context-aware decision overrides without being told
- It's the same pattern experienced ML engineers use, but the meta-agent derived it from first principles
- Total cost: ~$12 (compared to $15 for the baseline autoresearch runs)

This is a follow-up to my earlier autoresearch work ([16 experiments, $15, A40 GPU](BLOG_URL)). This time, we're using the canvas-org/meta-agent framework to close the loop: not just running experiments, but improving the agent orchestrating them.

Open source code: https://github.com/abhid1234/meta-agent-improver

The key insight: **meta-agents aren't just efficient—they rediscover domain knowledge.** For teams shipping AI features, this suggests a path forward: use multi-tier agent loops to bootstrap best practices, then distill them into production systems.

Read the full post: [BLOG_URL]

#AI #MachineLearning #MLOps #Agents #Claude #Optimization #ML #DeepLearning

---

## 2. X/Twitter Thread

**Main Tweet:**
Built a meta-agent that optimizes ML experiment workflows. Inner loop proposes hyperparameters, outer loop refines the prompts. Result: 80% → 95% on benchmark tasks. Cost: $12. Best part? The agent rediscovered phase-ordered exploration on its own. [BLOG_URL]

**Thread:**

**Thread Tweet 1:**
The setup: Haiku (inner) runs ML experiments. Sonnet (outer) watches, learns from failures, and iterates on Haiku's system prompt. 30 benchmark tasks from real experiment data. No manual guidance on *what* strategy to use.

**Thread Tweet 2:**
After 4-5 rounds of meta-optimization, Sonnet's improved prompt gives Haiku a dramatic edge. Phase-ordered exploration emerges naturally: "broad strokes first, then refine." It's exactly what experienced ML engineers do. But the meta-agent derived it from scratch.

**Thread Tweet 3:**
Why this matters: Multi-tier agent loops aren't just about efficiency—they're a way to bootstrap domain knowledge. Train the agent orchestrator, then productionize the insights. This is the future of ML ops tooling.

Code: https://github.com/abhid1234/meta-agent-improver Follow-up to my earlier autoresearch work (16 expts, $15).

---

## 3. Hacker News (Show HN)

**Title:**
Show HN: Meta-Agent Optimizer for ML Workflows – 80→95% accuracy, $12 cost

**Description:**
Built a two-tier agent system where an outer AI loop optimizes the prompts of an inner agent running ML hyperparameter experiments. Starting point: 80% accuracy on 30 benchmark tasks. After 4-5 rounds of meta-optimization: 95%.

Haiku proposes hyperparameter changes; Sonnet refines Haiku's system prompt based on failure patterns. The surprising result: the agent independently learned phase-ordered exploration (broad search → fine-grained refinement)—a strategy experienced ML engineers use intuitively.

Total cost ~$12. No manual strategy guidance. Open source: https://github.com/abhid1234/meta-agent-improver

This is a follow-up to earlier autoresearch work with Claude. The insight: multi-tier agent loops naturally bootstrap domain knowledge, suggesting a path for productionizing ML ops workflows.

Full write-up: [BLOG_URL]
