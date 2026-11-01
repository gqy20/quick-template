"""Claude Agent SDK 护栏示例：路径拦截 + 人工确认；真实模型必须 --run。

    uv run --extra agent python examples/claude_agent_guard.py --run

演示两种不依赖模型自觉的确定性控制：

- PreToolUse hook：拒绝工作目录之外的路径，命中即阻断，模型无法绕过；
- can_use_tool：每次工具调用前在终端确认，拒绝时可一并中断回合。

两者都通过 AgentRunner 注入——它们是回调，写不进 YAML。
"""

import argparse
import asyncio
from pathlib import Path
from typing import Any

from claude_agent_sdk import HookMatcher

from {{ package_name }}.agent import AgentConfig, AgentRunner, output_format_schema
from {{ package_name }}.agent_models import SummaryOutput

ROOT = Path.cwd().resolve()


def _outside(target: str) -> bool:
    resolved = Path(target).resolve()
    return resolved != ROOT and ROOT not in resolved.parents


async def deny_outside_root(
    payload: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    """PreToolUse：工具目标落在工作目录外时直接拒绝。"""
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("path")
    if isinstance(target, str) and _outside(target):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"拒绝访问工作目录外的路径: {target}",
            }
        }
    return {}


async def confirm_in_terminal(
    tool_name: str, tool_input: dict[str, Any], context: Any
) -> dict[str, Any]:
    """can_use_tool：终端确认后才放行，拒绝时中断本次回合。"""
    answer = input(f"允许 {tool_name}? [y/N] ").strip().lower()
    if answer == "y":
        return {"behavior": "allow", "updated_input": tool_input}
    return {"behavior": "deny", "message": "用户拒绝", "interrupt": True}


async def run_demo() -> None:
    config = AgentConfig(
        tools=["Read", "Write", "Bash"],
        allowed_tools=["Read", "Write"],
        permission_mode="default",
    )
    runner = AgentRunner(
        schema=output_format_schema(SummaryOutput),
        config=config,
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[deny_outside_root])]},
        can_use_tool=confirm_in_terminal,
    )
    result = await runner.run(
        "把这个仓库的 README 概括成三点。",
        SummaryOutput,
    )
    print(result.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude Agent SDK 护栏示例")
    parser.add_argument("--run", action="store_true", help="调用真实模型；需要 ANTHROPIC_API_KEY")
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
