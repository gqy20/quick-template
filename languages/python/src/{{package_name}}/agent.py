"""Agent SDK 核心封装。

提供：
- output_format_schema: Pydantic → SDK output_format
- parse_with_model: 结构化输出解析 + 验证
- AgentRunner: 简化 query 执行

Usage:
    from {{ package_name }}.agent import output_format_schema, parse_with_model, AgentRunner

    # 1. 定义输出 Schema
    class MyOutput(BaseModel):
        result: str
        score: int

    # 2. 执行查询
    runner = AgentRunner(schema=output_format_schema(MyOutput))
    result = await runner.run("你的查询")
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

    自动内联 $defs/$refs，使 schema 自包含。

    Args:
        model_class: Pydantic BaseModel 子类

    Returns:
        SDK 兼容的 output_format dict

    Example:
        from pydantic import BaseModel

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

    支持 ResultMessage.structured_output 和 AssistantMessage 中的
    StructuredOutput tool_use 块。

    Args:
        message: SDK 消息对象
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

    支持 duck typing：只要对象有 structured_output 属性即可。
    """
    # ResultMessage.structured_output
    if hasattr(message, "structured_output"):
        output = getattr(message, "structured_output")
        if isinstance(output, dict):
            return output

    # AssistantMessage + ToolUseBlock named "StructuredOutput"
    if hasattr(message, "content"):
        for block in getattr(message, "content", []):
            if hasattr(block, "name") and block.name == "StructuredOutput":
                if hasattr(block, "input") and isinstance(block.input, dict):
                    return block.input

    return None


# ============================================================================
# Agent Runner - 简化 query 执行
# ============================================================================


class AgentRunner:
    """简化的 Agent 执行器。

    封装 query 轮次，自动解析结构化输出。

    Example:
        from pydantic import BaseModel

        class SentimentResult(BaseModel):
            sentiment: str
            confidence: float

        runner = AgentRunner(
            schema=output_format_schema(SentimentResult),
            system_prompt="你是一个情感分析专家。",
        )
        result = await runner.run("这个产品太棒了！")
        assert isinstance(result, SentimentResult)
    """

    def __init__(
        self,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        model: str | None = None,
        max_turns: int | None = None,
    ):
        """初始化 Agent Runner。

        Args:
            schema: output_format schema dict
            system_prompt: 系统提示词
            model: 使用的模型，默认使用 SDK 配置
            max_turns: 最大对话轮次
        """
        self.schema = schema
        self.system_prompt = system_prompt or "你是一个有帮助的 AI 助手。"
        self.model = model
        self.max_turns = max_turns

    async def run(self, prompt: str, output_model: type[T]) -> T | None:
        """执行查询并返回结构化结果。

        Args:
            prompt: 用户提示词
            output_model: 输出 Pydantic 模型类

        Returns:
            解析并验证后的输出模型实例，失败返回 None
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
            # 打印 assistant 消息
            self._handle_message(message)
            # 尝试解析
            result = parse_with_model(message, output_model)
            if result is not None:
                return result

        return None

    def _handle_message(self, message: object) -> None:
        """处理并打印 SDK 消息。"""
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
