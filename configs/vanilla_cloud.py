"""Baseline config: Vanilla Haiku with no domain knowledge for cloud sizing.

No hooks, no custom system prompt, no domain-specific guidance.
This is the floor — the simplest possible cloud infrastructure sizing config.
"""

import os

from claude_agent_sdk import ClaudeAgentOptions

from meta_agent.run_context import RunContext


def build_options(ctx: RunContext) -> ClaudeAgentOptions:
    permission_mode = os.environ.get("CLAUDE_PERMISSION_MODE", "bypassPermissions")
    return ClaudeAgentOptions(
        system_prompt={"type": "preset", "preset": "claude_code"},
        tools={"type": "preset", "preset": "claude_code"},
        cwd=ctx.cwd,
        model=ctx.model,
        permission_mode=permission_mode,
        max_turns=50,
        max_budget_usd=1.0,
        thinking={"type": "adaptive"},
    )
