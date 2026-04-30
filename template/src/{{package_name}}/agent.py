"""Agent SDK 核心封装。

基于 claude-agent-sdk 源码分析（types.py / query.py / client.py）：

消息类型层次（types.py Message union）：
    Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage | StreamEvent | RateLimitEvent

结构化输出路径（types.py ResultMessage）：
    ResultMessage.structured_output: Any = None  ← output_format 验证后的 JSON dict

两种使用模式：
    1. query() — 单次无状态查询（query.py），适合脚本/CI
    2. ClaudeSDKClient — 双向有状态会话（client.py），适合交互式应用

Usage:
    from {{ package_name }}.agent import output_format_schema, AgentRunner

    class MyOutput(BaseModel):
        result: str
        score: int

    runner = AgentRunner(schema=output_format_schema(MyOutput))
    result = await runner.run("你的查询", MyOutput)
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from {{ package_name }}.logger import console

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


# ============================================================================
# Schema 生成 & 解析
# ============================================================================


def output_format_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """从 Pydantic 模型生成 Claude Agent SDK 的 output_format。

    对应 ClaudeAgentOptions.output_format 字段（types.py）:
        output_format: dict[str, Any] | None = None
        # 格式: {"type": "json_schema", "schema": {...}, "name": "...", "strict": True}

    自动内联 $defs/$refs，使 schema 自包含。

    Args:
        model_class: Pydantic BaseModel 子类

    Returns:
        SDK 兼容的 output_format dict

    Example:
        class AuditResult(BaseModel):
            score: int
            issues: list[str]

        schema = output_format_schema(AuditResult)
        # => {"type": "json_schema", "schema": {...}, "name": "AuditResult", "strict": True}
    """
    import json
    from copy import deepcopy

    schema = model_class.model_json_schema()
    defs = schema.pop("$defs", {})

    def _inline(node: Any) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                name = ref.removeprefix("#/$defs/")
                if name in defs:
                    resolved = _inline(deepcopy(defs[name]))
                    siblings = {k: v for k, v in node.items() if k != "$ref"}
                    if siblings and isinstance(resolved, dict):
                        resolved.update(_inline(siblings))
                    return resolved
            return {k: _inline(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_inline(item) for item in node]
        return node

    return {
        "type": "json_schema",
        "schema": _inline(schema),
        "name": model_class.__name__,
        "strict": True,
    }


def parse_with_model(message: object, model_class: type[T]) -> T | None:
    """从 SDK 消息中提取结构化输出并通过 Pydantic 验证。

    提取优先级（基于 types.py 源码）：
        1. ResultMessage.structured_output — 主要路径，output_format 验证后的 JSON dict
        2. AssistantMessage.content 中 ToolUseBlock(name="StructuredOutput").input — 回退路径

    Args:
        message: SDK 消息对象（ResultMessage 或 AssistantMessage）
        model_class: Pydantic 模型类

    Returns:
        验证后的模型实例，解析失败返回 None
    """
    raw = _extract_raw_dict(message)
    if raw is None:
        return None
    try:
        return model_class.model_validate(raw)
    except ValidationError:
        return None


def _extract_raw_dict(message: object) -> dict[str, Any] | None:
    """从 SDK 消息中提取原始 dict。

    路径 1: ResultMessage.structured_output（types.py 定义）
        @dataclass ResultMessage:
            structured_output: Any = None  # output_format 验证后的结果

    路径 2: AssistantMessage → ToolUseBlock "StructuredOutput"（回退）
        @dataclass AssistantMessage:
            content: list[ContentBlock]  # ContentBlock = TextBlock | ToolUseBlock | ...
        @dataclass ToolUseBlock:
            id: str
            name: str
            input: dict[str, Any]
    """
    # 路径 1: ResultMessage.structured_output（主要路径）
    if hasattr(message, "structured_output"):
        output = getattr(message, "structured_output")
        if isinstance(output, dict):
            return output

    # 路径 2: AssistantMessage + StructuredOutput ToolUseBlock（回退）
    if hasattr(message, "content"):
        for block in getattr(message, "content", []):
            if hasattr(block, "name") and block.name == "StructuredOutput":
                if hasattr(block, "input") and isinstance(block.input, dict):
                    return block.input

    return None


# ============================================================================
# Agent Runner - 简化 query 执行（单次无状态模式）
# ============================================================================


class AgentRunner:
    """简化的 Agent 执行器，基于 query() 单次查询 API。

    底层调用链（query.py 源码）:
        query(prompt, options) → InternalClient.process_query() → AsyncIterator[Message]

    适用场景：脚本、CI/CD、批量处理等一次性任务。

    Example:
        class SentimentResult(BaseModel):
            sentiment: str
            confidence: float

        runner = AgentRunner(
            schema=output_format_schema(SentimentResult),
            system_prompt="你是一个情感分析专家。",
        )
        result = await runner.run("这个产品太棒了！", SentimentResult)
        assert isinstance(result, SentimentResult)
    """

    def __init__(
        self,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        model: str | None = None,
        max_turns: int | None = None,
    ):
        self.schema = schema
        self.system_prompt = system_prompt or "你是一个有帮助的 AI 助手。"
        self.model = model
        self.max_turns = max_turns

    async def run(self, prompt: str, output_model: type[T]) -> T | None:
        """执行查询并返回结构化结果。

        遍历 query() 返回的消息流，通过 parse_with_model 提取结构化输出。
        消息流顺序通常为: [StreamEvent*, AssistantMessage*, ResultMessage]
        """
        try:
            from claude_agent_sdk import ClaudeAgentOptions, query
        except ImportError:
            console.print("[red]错误: claude-agent-sdk 未安装[/red]")
            console.print("[dim]请运行: uv add claude-agent-sdk[/dim]")
            return None

        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            model=self.model,
            max_turns=self.max_turns,
            output_format=self.schema,
        )

        async for message in query(prompt=prompt, options=options):
            self._handle_message(message)
            result = parse_with_model(message, output_model)
            if result is not None:
                return result

        return None

    def _handle_message(self, message: object) -> None:
        """处理并打印 SDK 消息。

        消息类型处理（基于 types.py 源码）:
            - StreamEvent: event 是原始 API stream event dict
              event.type == "content_block_delta" → delta.text 为流式文本
            - AssistantMessage: content 包含 TextBlock / ToolUseBlock 等
            - ResultMessage: 包含 total_cost_usd / is_error / errors 等
        """
        try:
            from claude_agent_sdk import (
                AssistantMessage,
                ResultMessage,
                StreamEvent,
                TextBlock,
            )
        except ImportError:
            return

        if isinstance(message, StreamEvent):
            # StreamEvent.event: dict[str, Any] — 原始 Anthropic API stream event
            event = message.event
            if event.get("type") == "content_block_delta":
                delta = event.get("delta", {})
                if text := delta.get("text"):
                    console.print(text, end="", markup=True)
            return

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    console.print(block.text)
            return

        if isinstance(message, ResultMessage):
            if message.total_cost_usd is not None:
                console.print(f"\n[dim]Cost: ${message.total_cost_usd:.4f}[/dim]")
            if message.is_error:
                console.print(f"[red]Error: {message.errors}[/red]")


# ============================================================================
# 结构化输出快捷函数（推荐用于简单场景）
# ============================================================================


async def structured_query(
    prompt: str,
    output_model: type[T],
    *,
    system_prompt: str | None = None,
    model: str | None = None,
    max_turns: int | None = None,
) -> T | None:
    """一行代码完成结构化查询。

    封装 AgentRunner 的常见用法，适合快速脚本。

    Args:
        prompt: 用户提示词
        output_model: 输出 Pydantic 模型类
        system_prompt: 系统提示词
        model: 模型名称
        max_turns: 最大轮次

    Returns:
        解析后的模型实例，失败返回 None

    Example:
        class Summary(BaseModel):
            title: str
            points: list[str]

        result = await structured_query(
            "总结这篇文章",
            Summary,
            system_prompt="你是一个摘要专家。",
        )
        if result:
            print(result.title)
            print(result.points)
    """
    runner = AgentRunner(
        schema=output_format_schema(output_model),
        system_prompt=system_prompt,
        model=model,
        max_turns=max_turns,
    )
    return await runner.run(prompt, output_model)


# ============================================================================
# 预定义 Schema 工厂
# ============================================================================


def sentiment_schema() -> dict[str, Any]:
    """情感分析 Schema。"""
    from pydantic import BaseModel

    class SentimentOutput(BaseModel):
        sentiment: str
        confidence: float
        keywords: list[str]

    return output_format_schema(SentimentOutput)


def code_review_schema() -> dict[str, Any]:
    """代码审查 Schema。"""
    from pydantic import BaseModel, Field

    class CodeIssue(BaseModel):
        severity: str
        line: int | None = None
        description: str
        suggestion: str | None = None

    class CodeReviewOutput(BaseModel):
        score: int = Field(description="代码评分 0-10")
        issues: list[CodeIssue] = Field(default_factory=list)
        overall: str = Field(description="总体评价")

    return output_format_schema(CodeReviewOutput)
