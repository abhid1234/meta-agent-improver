# Meta-Agent Improver: Self-Optimizing ML Experiment Advisor

A meta-agent that discovers better prompts and tools for an ML hyperparameter advisor by learning from its own failures.

## The Idea

This project builds on two core insights:

1. **Real experiments first**: We ran [Karpathy's autoresearch](https://github.com/karpathy/autoresearch) to generate 16 real ML experiments exploring hyperparameter sensitivity in neural networks.

2. **Meta-optimization second**: Rather than hand-tuning the advisor, we built a meta-agent that iteratively improves the system prompts, hooks, and tools used by the inner agent, discovering what actually works through empirical evaluation.

The result: a feedback loop where a larger proposer model optimizes a smaller inner model by reading traces of failures and proposing better configurations.

## How It Works

### Inner Agent (small, fast model)
- **Input**: Experiment history (past hyperparameter changes) + `train.py` source code
- **Task**: Propose the next hyperparameter change to try
- **Evaluation**: Deterministic verifier checks proposal against ground truth from real experiments
- **Scoring**: Early tasks require proposing the best remaining change; later tasks accept any novel untried parameter

### Meta Loop (larger proposer model)
- **Iteration**: Run 8 optimization rounds
- **Input**: Traces of failed proposals from previous iteration (why did the inner model get it wrong?)
- **Output**: New system prompt, hooks, or tool definitions
- **Feedback**: Re-run baseline eval, measure improvement, decide next move

### Task Distribution
- **Tasks 01-13** (early/mid stage): 30 hyperparameter options available, must rank by expected improvement
- **Tasks 14-21** (late stage): Fewer options left, must propose final correct parameter (`FINAL_LR_FRAC=0.05`)
- **Tasks 22-30** (synthetic/very late): Only novel untried parameters score (prevent repeating failures)

## Project Structure

```
meta-agent-improver/
├── meta-agent/                      # Framework (canvas-org/meta-agent fork)
│   ├── meta_agent/
│   │   ├── outer_loop.py            # Meta-optimization loop (proposes config changes)
│   │   ├── eval_runner.py           # Runs tasks, evaluates scores
│   │   ├── task_runner.py           # Executes single task (calls verify.py)
│   │   └── cli.py                   # Inspect candidates, compare results
│   ├── configs/
│   │   ├── vanilla.py               # Baseline agent config
│   │   ├── bootstrap.py             # Config with hooks
│   │   └── hooks.py                 # System prompt templates
│   └── benchmarks/ml-advisor/       # ML advisor tasks
├── experience/ml-advisor/           # Generated candidates + results
│   └── candidates/
│       ├── baseline/                # Baseline run (vanilla config)
│       ├── evo_001/, evo_002/, ...  # Meta-optimized variants
│       └── staging/                 # Current work-in-progress
├── benchmarks/ml-advisor/           # Task definitions
│   ├── benchmark.yaml               # 30 tasks with workspaces
│   └── workspaces/                  # Per-task experiment dirs
├── ground_truth.json                # Reference solutions from real experiments
├── verify.py                        # Deterministic task verifier
└── pyproject.toml
```

## Running It

### Prerequisites
- Python 3.13+
- `ANTHROPIC_API_KEY` (for the inner and proposer models)
- `OPENAI_API_KEY` (optional, for LLM judge)

### Install

```bash
cd /path/to/meta-agent-improver

# Create virtual environment
uv sync

# Set environment
export ANTHROPIC_API_KEY=sk-ant-...
```

### Baseline Evaluation

Run the vanilla config against all 30 tasks:

```bash
python -m meta_agent.eval_runner \
    --benchmark benchmarks/ml-advisor/benchmark.yaml \
    --config meta-agent/configs/vanilla.py \
    --name baseline \
    --model <inner-model>
```

Results saved to `experience/ml-advisor/candidates/baseline/`.

### Meta-Optimization Loop

Run 8 iterations of optimization (proposer model refines configs, inner model evaluates them):

```bash
python -m meta_agent.outer_loop \
    --benchmark benchmarks/ml-advisor/benchmark.yaml \
    --iterations 8 \
    --model <inner-model> \
    --proposer-model <proposer-model>
```

Results saved to `experience/ml-advisor/candidates/evo_001/`, `evo_002/`, etc.

### Inspect Results

List all candidates sorted by pass rate:

```bash
python -m meta_agent.cli list
```

Show detailed results for a candidate:

```bash
python -m meta_agent.cli show baseline
```

Compare two configs:

```bash
python -m meta_agent.cli diff baseline evo_001
```

View failures for a candidate:

```bash
python -m meta_agent.cli failures evo_001
```

## Results

Placeholder for final results (to be updated after meta-optimization runs complete).

## Blog Post

Full writeup coming to [Substack](https://abhidas.substack.com/).

## Based On

- **[canvas-org/meta-agent](https://github.com/canvas-org/meta-agent)**: Harness optimization framework (67% → 87% on tau-bench with no labels)
- **[Karpathy's autoresearch](https://github.com/karpathy/autoresearch)**: Autonomous ML researcher that generated the 16 real experiments
- **LLM Models**: small/fast model for inner agent, larger model for meta-loop proposer

## License

MIT
