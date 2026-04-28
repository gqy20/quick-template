"""Claude Agent SDK 示例脚本。

演示三种核心使用模式：
1. query 模式 - 一次性无状态查询
2. ClaudeSDKClient 模式 - 有状态对话，支持中断
3. 结构化输出 - 使用 JSON Schema 约束输出格式

运行方式：
    python -m {{package_name}}.agent [mode]

参数：
    mode 可选值：query | client | structured
    默认为 query
"""

import asyncio
import json
import sys
from dataclasses import asdict

from {{package_name }}.logger import console, print_header, print_success

# ============================================================================
# 模式 1：query 模式 - 一次性无状态查询
# ============================================================================

async def demo_query_mode() -> None:
    """query 模式：适合简单的一次性任务，无需维护会话状态。"""
    from claude_agent_sdk import ClaudeAgentOptions, query

    print_header("Query 模式演示")

    options = ClaudeAgentOptions(
        system_prompt="你是一个有帮助的助手，用简洁的语言回答问题。",
        permission_mode="acceptEdits",
        cwd=None,
    )

    prompts = [
        "用一句话解释什么是 Python。",
        "列出 3 个 Python 的主要特点。",
    ]

    for i, prompt_text in enumerate(prompts, 1):
        console.print(f"\n[dim]查询 {i}: {prompt_text}[/dim]")
        async for message in query(prompt=prompt_text, options=options):
            if hasattr(message, "content"):
                for block in message.content:
                    if hasattr(block, "text"):
                        print_success(f"回复: {block.text}")


# ============================================================================
# 模式 2：ClaudeSDKClient - 有状态对话，支持中断和继续
# ============================================================================

async def demo_client_mode() -> None:
    """ClaudeSDKClient 模式：适合需要多轮对话的交互式场景。"""
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    from claude_agent_sdk.types import (
        AssistantMessage,
        ResultMessage,
        TextBlock,
        ThinkingBlock,
    )

    print_header("ClaudeSDKClient 模式演示")

    options = ClaudeAgentOptions(
        system_prompt="你是一个技术顾问，帮助用户解决编程问题。",
        permission_mode="acceptEdits",
    )

    async with ClaudeSDKClient(options=options) as client:
        # 第一轮：发起问题
        console.print("\n[dim]发送问题：什么是闭包？[/dim]")
        await client.query("什么是 Python 中的闭包？请用简单的例子说明。")

        # 接收响应
        response_texts: list[str] = []
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_texts.append(block.text)
                        console.print(f"[cyan]Claude:[/cyan] {block.text}")
            elif isinstance(message, ResultMessage):
                if message.result:
                    console.print(f"\n[dim]最终结果: {message.result[:100]}...[/dim]")

        # 第二轮：追问（上下文保持）
        console.print("\n[dim]\n发送追问：能否给一个实际应用的例子？[/dim]")
        await client.query("能否给一个实际应用闭包的例子？")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        console.print(f"[cyan]Claude:[/cyan] {block.text}")


# ============================================================================
# 模式 3：结构化输出 - JSON Schema 约束
# ============================================================================

async def demo_structured_output() -> None:
    """结构化输出：使用 JSON Schema 约束 AI 输出格式。"""
    from claude_agent_sdk import ClaudeAgentOptions, query
    from claude_agent_sdk.types import ResultMessage

    print_header("结构化输出演示")

    # 定义输出 Schema
    sentiment_schema = {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "sentiment": {
                    "type": "string",
                    "enum": ["positive", "negative", "neutral"],
                    "description": "情感极性",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "置信度 0-1",
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "关键词列表",
                },
                "summary": {
                    "type": "string",
                    "description": "简短摘要",
                },
            },
            "required": ["sentiment", "confidence", "summary"],
        },
    }

    # 代码审查 Schema
    code_review_schema = {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "issues": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "severity": {
                                "type": "string",
                                "enum": ["critical", "warning", "info"],
                            },
                            "line": {"type": "integer"},
                            "description": {"type": "string"},
                            "suggestion": {"type": "string"},
                        },
                        "required": ["severity", "description"],
                    },
                },
                "score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 10,
                    "description": "代码评分",
                },
                "overall": {"type": "string", "description": "总体评价"},
            },
            "required": ["issues", "score", "overall"],
        },
    }

    test_texts = [
        "太棒了！这个库真的非常好用，性能优秀，文档清晰！",
        "代码有严重的内存泄漏问题，需要立即修复。",
    ]

    # 示例 1：情感分析
    console.print("\n[yellow]示例 1：情感分析[/yellow]")
    options = ClaudeAgentOptions(
        system_prompt="分析文本情感，以 JSON 格式输出。",
        output_format=sentiment_schema,
    )

    for text in test_texts:
        console.print(f"\n[dim]输入: {text}[/dim]")
        async for message in query(prompt=f"分析这段文字的情感：{text}", options=options):
            if isinstance(message, ResultMessage) and message.structured_output:
                result = message.structured_output
                console.print(f"[green]情感:[/green] {result.get('sentiment')}")
                console.print(f"[green]置信度:[/green] {result.get('confidence'):.2f}")
                console.print(f"[green]关键词:[/green] {result.get('keywords', [])}")
                console.print(f"[green]摘要:[/green] {result.get('summary')}")

    # 示例 2：代码审查
    console.print("\n[yellow]\n示例 2：代码审查（模拟）[/yellow]")
    code_review_options = ClaudeAgentOptions(
        system_prompt="审查代码问题，以 JSON 格式输出。",
        output_format=code_review_schema,
    )

    code_sample = """
    def process_data(data):
        print(data)  # potential security issue
        return data
    """

    console.print(f"\n[dim]代码片段:{code_sample}[/dim]")
    async for message in query(
        prompt=f"审查以下代码，返回结构化的问题列表：\n{code_sample}",
        options=code_review_options,
    ):
        if isinstance(message, ResultMessage) and message.structured_output:
            result = message.structured_output
            console.print(f"[green]评分:[/green] {result.get('score')}/10")
            console.print(f"[green]总体:[/green] {result.get('overall')}")
            console.print("[green]问题列表:[/green]")
            for issue in result.get("issues", []):
                severity_emoji = {
                    "critical": "🔴",
                    "warning": "⚠️",
                    "info": "ℹ️",
                }.get(issue.get("severity", "info"), "•")
                console.print(
                    f"  {severity_emoji} [{issue.get('severity')}] "
                    f"第 {issue.get('line', '?')} 行: {issue.get('description')}"
                )


# ============================================================================
# 主入口
# ============================================================================

async def main() -> None:
    """根据命令行参数运行不同的演示。"""
    mode = sys.argv[1] if len(sys.argv) > 1 else "query"

    demos = {
        "query": demo_query_mode,
        "client": demo_client_mode,
        "structured": demo_structured_output,
    }

    if mode not in demos:
        console.print(f"[red]未知模式: {mode}[/red]")
        console.print(f"可用模式: {', '.join(demos.keys())}")
        sys.exit(1)

    console.print(f"[dim]运行模式: {mode}[/dim]")
    await demos[mode]()


if __name__ == "__main__":
    asyncio.run(main())
