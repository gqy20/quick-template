"""LangGraph 结构化代码审查示例；真实模型必须显式 --run。"""

import argparse
import asyncio

from {{ package_name }}.agent_models import CodeReviewOutput
from {{ package_name }}.langgraph_agent import LangGraphReviewRuntime
from {{ package_name }}.prompt import PromptRegistry

SAMPLE_CODE = """+def add(a, b):
    return a + b
"""


async def run_demo() -> None:
    prompts = PromptRegistry("config/prompts")
    prompt = prompts.render(
        "code-review",
        language="Python",
        code=SAMPLE_CODE,
    )
    runtime = await LangGraphReviewRuntime.with_anthropic_and_mcp()
    result = await runtime.run(prompt, CodeReviewOutput)
    print(result.model_dump_json(indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph 结构化代码审查示例")
    parser.add_argument(
        "--run",
        action="store_true",
        help="调用真实模型；需要 ANTHROPIC_API_KEY",
    )
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
