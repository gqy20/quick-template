#!/usr/bin/env python3
"""可移植的 Claude Agent SDK 封装 — 单文件，零项目依赖。

基于 claude-agent-sdk query() 模式，提供：
- AgentConfig: 统一配置（tools / MCP / skills / 结构化输出 / cwd / model ...）
- Agent.ask(): 类型安全的结构化查询，失败抛异常而非返回 None
- ask(): 一行快捷函数
- 完善的 DEBUG 日志：每条消息的字段级记录

迁移方式:
    cp examples/claude_agent.py your_project/claude_agent.py
    # 在你的代码中:
    from claude_agent import Agent, AgentConfig, ask

运行演示:
    python claude_agent.py all              # 全部演示
    python claude_agent.py sentiment        # 情感分析
    python claude_agent.py review           # 代码审查
    python claude_agent.py tools            # Tools 配置
    python claude_agent.py mcp              # MCP Server

依赖: pydantic>=2.0, claude-agent-sdk>=0.1.71
"""

from __future__ import annotations

import asyncio
import collections
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, ValidationError

__all__ = [
    "Agent",
    "AgentConfig",
    "QueryStats",
    "ask",
    "AgentError",
    "AgentConnectionError",
    "AgentProcessError",
    "AgentValidationError",
    "AgentBudgetExceededError",
    "AgentRateLimitError",
    "output_format_schema",
    "parse_with_model",
]

logger = logging.getLogger("claude_agent")

T = TypeVar("T", bound=BaseModel)


# ============================================================================
# 异常体系
# ============================================================================


class AgentError(Exception):
    """Base exception for claude_agent wrapper."""


class AgentConnectionError(AgentError):
    """CLI 未安装或不可达。"""


class AgentProcessError(AgentError):
    """子进程失败或协议错误。"""

    def __init__(
        self,
        message: str,
        exit_code: int | None = None,
        stderr: str | None = None,
    ):
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(message)


class AgentValidationError(AgentError):
    """结构化输出无法通过 Pydantic 验证。"""

    def __init__(
        self,
        message: str,
        raw_data: dict[str, Any] | None = None,
        model_class: type[BaseModel] | None = None,
    ):
        self.raw_data = raw_data
        self.model_class = model_class
        super().__init__(message)


class AgentBudgetExceededError(AgentError):
    """超过 max_turns 或 max_budget_usd。"""

    def __init__(
        self,
        message: str,
        actual_turns: int = 0,
        actual_cost_usd: float | None = None,
    ):
        self.actual_turns = actual_turns
        self.actual_cost_usd = actual_cost_usd
        super().__init__(message)


class AgentRateLimitError(AgentError):
    """触发 API 限流。"""

    def __init__(
        self,
        message: str,
        status: str = "",
        resets_at: int | None = None,
        utilization: float | None = None,
    ):
        self.status = status
        self.resets_at = resets_at
        self.utilization = utilization
        super().__init__(message)


# ============================================================================
# 查询统计
# ============================================================================


@dataclass
class QueryStats:
    """单次查询的运行统计。

    属性:
        tool_calls:      {工具名: 调用次数}
        tasks:           [{task_id, description, status}, ...]  skills/subagent 调用记录
        token_usage:     ResultMessage.usage 原始 dict (input/output/cache tokens)
        model_usage:     ResultMessage.model_usage 原始 dict (按模型分解)
        message_count:   总消息数
        duration_sec:    耗时(秒)
        total_cost_usd:  费用(USD)
        num_turns:       对话轮次
    """

    tool_calls: dict[str, int] = field(default_factory=dict)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, Any] | None = None
    model_usage: dict[str, Any] | None = None
    message_count: int = 0
    duration_sec: float = 0.0
    total_cost_usd: float | None = None
    num_turns: int = 0

    def summary(self) -> str:
        """生成人类可读的统计摘要。"""
        parts = [
            f"消息={self.message_count}",
            f"轮次={self.num_turns}",
            f"耗时={self.duration_sec:.2f}s",
        ]
        if self.total_cost_usd is not None:
            parts.append(f"费用=${self.total_cost_usd:.4f}")

        if self.tool_calls:
            tools_str = ", ".join(f"{k}×{v}" for k, v in self.tool_calls.items())
            parts.append(f"工具=[{tools_str}]")

        if self.token_usage:
            parts.append(f"tokens={self.token_usage}")

        if self.tasks:
            parts.append(f"tasks={len(self.tasks)}")

        return " | ".join(parts)


# ============================================================================
# 配置类
# ============================================================================


class AgentConfig(BaseModel):
    """Claude Agent 查询配置。

    覆盖 ClaudeAgentOptions 的常用字段，提供合理默认值。
    可通过 Agent() 注入，也可在 ask() 时按调用覆盖。

    Example:
        config = AgentConfig(
            model="claude-sonnet-4-5",
            cwd="/path/to/project",
            effort="high",
            max_turns=5,
        )
    """

    # -- 模型设置 --
    model: str | None = Field(default=None, description="模型 ID，如 'claude-sonnet-4-5'")
    fallback_model: str | None = Field(default=None, description="主模型失败时的回退模型")
    effort: Literal["low", "medium", "high", "max"] | None = Field(
        default=None, description="推理深度: low/medium/high/max"
    )
    thinking: dict[str, Any] | None = Field(
        default=None,
        description='思考配置: {"type":"adaptive"} | {"type":"enabled","budget_tokens":N} | {"type":"disabled"}',
    )
    betas: list[str] = Field(default_factory=list, description="Beta 功能标志")

    # -- 行为 --
    system_prompt: str | None = Field(default=None, description="系统提示词")
    cwd: str | Path | None = Field(default=None, description="工作目录，默认进程 cwd")
    permission_mode: Literal[
        "default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"
    ] | None = Field(default=None, description="工具权限模式")
    max_turns: int | None = Field(default=None, description="最大对话轮次")
    max_budget_usd: float | None = Field(default=None, description="最大预算 (USD)")

    # -- 工具 --
    tools: list[str] | None = Field(
        default=None, description="启用的内置工具名列表，[] 表示禁用所有"
    )
    allowed_tools: list[str] = Field(
        default_factory=list, description="自动批准的工具名（无需权限确认）"
    )
    disallowed_tools: list[str] = Field(
        default_factory=list, description="完全禁用的工具名"
    )
    skills: list[str] | Literal["all"] | None = Field(
        default=None, description="启用的 skills，'all' 表示全部"
    )

    # -- MCP 服务器 --
    mcp_servers: dict[str, Any] = Field(
        default_factory=dict,
        description="MCP 服务器配置 {name: McpServerConfig 或 McpSdkServerConfig}",
    )

    # -- 环境 --
    env: dict[str, str] = Field(default_factory=dict, description="子进程环境变量")
    cli_path: str | Path | None = Field(default=None, description="CLI 可执行文件路径")

    def to_sdk_options(self) -> Any:
        """转换为 ClaudeAgentOptions 实例。"""
        from claude_agent_sdk import ClaudeAgentOptions

        kwargs = self.model_dump(exclude_none=True)
        thinking_val = kwargs.pop("thinking", None)

        # 只传 ClaudeAgentOptions 实际拥有的字段
        sdk_fields = {
            f.name for f in __import__("dataclasses").fields(ClaudeAgentOptions)
            if hasattr(ClaudeAgentOptions, f.name)
        }
        filtered = {k: v for k, v in kwargs.items() if k in sdk_fields}

        options = ClaudeAgentOptions(**filtered)
        if thinking_val is not None:
            options.thinking = thinking_val
        return options


# ============================================================================
# Schema 工具函数
# ============================================================================


def output_format_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """从 Pydantic 模型生成 SDK output_format。

    自动内联 $defs/$refs 使 schema 自包含。

    Example:
        class MyOutput(BaseModel):
            name: str
            score: int

        schema = output_format_schema(MyOutput)
        # => {"type": "json_schema", "schema": {...}, "name": "MyOutput", "strict": True}
    """
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
    """从 SDK 消息提取结构化输出并通过 Pydantic 验证。

    提取路径（优先级）:
        1. ResultMessage.structured_output  — 主路径
        2. AssistantMessage → ToolUseBlock("StructuredOutput") — 回退
    """
    raw = _extract_raw_dict(message)
    if raw is None:
        return None
    try:
        return model_class.model_validate(raw)
    except ValidationError:
        return None


def _extract_raw_dict(message: object) -> dict[str, Any] | None:
    """从 SDK 消息提取原始 dict。"""
    # 路径 1: ResultMessage.structured_output
    if hasattr(message, "structured_output"):
        output = getattr(message, "structured_output")
        if isinstance(output, dict):
            return output

    # 路径 2: AssistantMessage → StructuredOutput ToolUseBlock
    if hasattr(message, "content"):
        for block in getattr(message, "content", []):
            if getattr(block, "name", None) == "StructuredOutput":
                inp = getattr(block, "input", None)
                if isinstance(inp, dict):
                    return inp

    return None


# ============================================================================
# Agent 类
# ============================================================================


class Agent:
    """可移植的 Claude Agent SDK 封装（query 模式）。

    Example:
        agent = Agent(AgentConfig(model="claude-sonnet-4-5", max_turns=3))

        class Summary(BaseModel):
            title: str
            points: list[str]

        result = await agent.ask("总结这篇文章", Summary)
        print(result.title)   # 类型安全访问
    """

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self._last_result: object | None = None
        self._stats: QueryStats = QueryStats()

    @property
    def last_stats(self) -> QueryStats:
        """最近一次 ask() 的查询统计。"""
        return self._stats

    async def ask(self, prompt: str, output_model: type[T], **overrides) -> T:
        """发送查询并返回验证后的结构化结果。

        Args:
            prompt: 用户问题
            output_model: Pydantic 输出模型类
            **overrides: 单次调用覆盖任意 AgentConfig 字段

        Returns:
            验证后的 output_model 实例

        Raises:
            AgentConnectionError: CLI 未安装或不可达
            AgentProcessError: 子进程失败
            AgentValidationError: 输出不符合模型定义
            AgentBudgetExceededError: 超过 turns/budget
            AgentRateLimitError: 触发限流
        """
        merged = self.config.model_copy(update=overrides) if overrides else self.config
        options = self._build_options(output_model, merged)

        # 重置统计
        self._stats = QueryStats()
        stats = self._stats

        logger.info(
            "查询开始 | prompt=%.80s | model=%s | turns=%s | cwd=%s",
            prompt, merged.model, merged.max_turns, merged.cwd,
        )

        start = time.monotonic()
        result: T | None = None

        try:
            from claude_agent_sdk import query as sdk_query

            async for message in sdk_query(prompt=prompt, options=options):
                stats.message_count += 1
                self._handle_message(message)
                self._check_rate_limit(message)

                parsed = parse_with_model(message, output_model)
                if parsed is not None:
                    result = parsed
                    logger.debug("结构化输出已提取 (消息 #%d)", stats.message_count)
                    break

                if self._is_result_message(message):
                    self._last_result = message

        except ImportError:
            raise AgentConnectionError(
                "claude-agent-sdk 未安装，请执行: pip install 'claude-agent-sdk>=0.1.71'"
            )
        except AgentError:
            raise
        except Exception as exc:
            self._translate_exception(exc)

        # 填充最终统计
        elapsed = time.monotonic() - start
        stats.duration_sec = elapsed
        stats.total_cost_usd = self._get_cost()
        stats.num_turns = getattr(self._last_result, "num_turns", 0) or 0

        if result is None:
            self._raise_on_no_result(output_model, elapsed, stats.message_count)

        logger.info("查询完成 | %s", stats.summary())

        return result

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_options(
        self, output_model: type[BaseModel], config: AgentConfig
    ) -> Any:
        """构建 ClaudeAgentOptions。"""
        options = config.to_sdk_options()
        options.output_format = output_format_schema(output_model)
        return options

    def _handle_message(self, message: object) -> None:
        """分发消息到对应日志处理器，同时收集统计。"""
        try:
            from claude_agent_sdk import (
                AssistantMessage,
                RateLimitEvent,
                ResultMessage,
                StreamEvent,
                SystemMessage,
                TaskStartedMessage,
                TaskNotificationMessage,
                TextBlock,
                ThinkingBlock,
                ToolUseBlock,
            )
        except ImportError:
            logger.debug("收到消息 (SDK 类型不可用): %r", type(message).__name__)
            return

        if isinstance(message, StreamEvent):
            self._log_stream_event(message)
        elif isinstance(message, AssistantMessage):
            self._log_assistant_message(message)
        elif isinstance(message, ResultMessage):
            self._log_result_message(message)
        elif isinstance(message, RateLimitEvent):
            self._log_rate_limit_event(message)
        elif isinstance(message, TaskStartedMessage):
            self._track_task_start(message)
        elif isinstance(message, TaskNotificationMessage):
            self._track_task_end(message)
        elif isinstance(message, SystemMessage):
            logger.debug("SystemMessage | subtype=%s", message.subtype)
        else:
            logger.debug("未知消息类型 | %s | %r", type(message).__name__, message)

    def _log_stream_event(self, message: object) -> None:
        event = message.event
        etype = event.get("type", "?")
        safe = {k: v for k, v in event.items() if k not in ("delta", "content")}
        logger.debug("StreamEvent | type=%s | %s", etype, safe)

        if etype == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                text = delta.get("text", "")
                logger.debug("  text_delta | %r", text[:100])
            elif delta.get("type") == "thinking_delta":
                logger.debug("  thinking_delta")
        elif etype == "thinking":
            logger.debug("  thinking block")

    def _log_assistant_message(self, message: object) -> None:
        block_counts: dict[str, int] = {}
        try:
            from claude_agent_sdk import TextBlock, ThinkingBlock, ToolUseBlock

            for block in message.content:
                bname = type(block).__name__
                block_counts[bname] = block_counts.get(bname, 0) + 1
                if isinstance(block, TextBlock):
                    logger.debug("  TextBlock[%d] | %r", block_counts[bname], block.text[:120])
                elif isinstance(block, ThinkingBlock):
                    logger.debug(
                        "  ThinkingBlock[%d] | sig=%s",
                        block_counts[bname],
                        block.signature[:40] if block.signature else "",
                    )
                elif isinstance(block, ToolUseBlock):
                    keys = list(block.input.keys()) if block.input else []
                    logger.debug(
                        "  ToolUseBlock[%d] | name=%s | keys=%s",
                        block_counts[bname], block.name, keys,
                    )
                    # 统计工具调用
                    self._stats.tool_calls[block.name] = (
                        self._stats.tool_calls.get(block.name, 0) + 1
                    )

            # AssistantMessage 级别的 token usage (每轮)
            msg_usage = getattr(message, "usage", None)
            if msg_usage:
                logger.debug("  usage=%s", msg_usage)

        except Exception:
            pass

        logger.debug(
            "AssistantMessage | model=%s | stop=%s | blocks=%s",
            message.model, message.stop_reason, block_counts,
        )

    def _log_result_message(self, message: object) -> None:
        so = message.structured_output
        so_info = ""
        if isinstance(so, dict):
            so_info = f" | output_keys={list(so.keys())}"
        elif so is not None:
            so_info = f" | output_type={type(so).__name__}"

        # 收集 token 统计
        usage = getattr(message, "usage", None)
        model_usage = getattr(message, "model_usage", None)
        self._stats.token_usage = usage
        self._stats.model_usage = model_usage

        token_info = ""
        if usage:
            token_info = f" | tokens={usage}"
        if model_usage:
            token_info += f" | model_usage={model_usage}"

        logger.debug(
            "ResultMessage | error=%s | cost=$%s | turns=%s "
            "| duration_ms=%s | api_ms=%s | stop=%s%s%s | errors=%s",
            message.is_error,
            message.total_cost_usd,
            message.num_turns,
            message.duration_ms,
            message.duration_api_ms,
            message.stop_reason,
            so_info,
            token_info,
            message.errors,
        )

    def _log_rate_limit_event(self, message: object) -> None:
        info = message.rate_limit_info
        util_pct = (info.utilization or 0) * 100
        if info.status == "rejected":
            logger.error(
                "RateLimitEvent | REJECTED | type=%s | 利用率=%.0f%% | resets_at=%s",
                info.rate_limit_type, util_pct, info.resets_at,
            )
        else:
            logger.warning(
                "RateLimitEvent | %s | type=%s | 利用率=%.0f%%",
                info.status, info.rate_limit_type, util_pct,
            )

    def _check_rate_limit(self, message: object) -> None:
        """检测限流事件，拒绝时抛异常。"""
        try:
            from claude_agent_sdk import RateLimitEvent
        except ImportError:
            return

        if not isinstance(message, RateLimitEvent):
            return
        info = message.rate_limit_info
        if info.status == "rejected":
            raise AgentRateLimitError(
                f"限流拒绝: {info.rate_limit_type}",
                status=info.status,
                resets_at=info.resets_at,
                utilization=info.utilization,
            )

    def _track_task_start(self, message: object) -> None:
        """追踪 TaskStartedMessage (skill/subagent 启动)。"""
        self._stats.tasks.append({
            "task_id": getattr(message, "task_id", "?"),
            "description": getattr(message, "description", ""),
            "status": "started",
            "task_type": getattr(message, "task_type", None),
        })
        logger.debug(
            "TaskStarted | id=%s | desc=%s | type=%s",
            message.task_id, message.description,
            getattr(message, "task_type", "-"),
        )

    def _track_task_end(self, message: object) -> None:
        """追踪 TaskNotificationMessage (skill/subagent 结束)。"""
        # 更新已存在的 task 记录或追加新记录
        task_id = getattr(message, "task_id", "?")
        updated = False
        for t in self._stats.tasks:
            if t.get("task_id") == task_id:
                t["status"] = getattr(message, "status", "?")
                t["summary"] = getattr(message, "summary", "")
                updated = True
                break
        if not updated:
            self._stats.tasks.append({
                "task_id": task_id,
                "description": getattr(message, "description", ""),
                "status": getattr(message, "status", "?"),
                "summary": getattr(message, "summary", ""),
            })

        logger.debug(
            "TaskNotification | id=%s | status=%s | summary=%s",
            task_id,
            getattr(message, "status", "?"),
            getattr(message, "summary", "")[:80],
        )

    @staticmethod
    def _is_result_message(message: object) -> bool:
        return getattr(message, "subtype", None) in ("success", "error")

    def _translate_exception(self, exc: BaseException) -> None:
        """将 SDK 异常翻译为封装异常后重新抛出。"""
        from claude_agent_sdk import (
            CLIConnectionError,
            CLINotFoundError,
            CLIJSONDecodeError,
            ProcessError,
        )

        if isinstance(exc, CLINotFoundError):
            raise AgentConnectionError(f"Claude Code CLI 未找到: {exc}") from exc
        if isinstance(exc, CLIConnectionError):
            raise AgentConnectionError(f"无法连接 Claude Code: {exc}") from exc
        if isinstance(exc, ProcessError):
            raise AgentProcessError(
                str(exc),
                exit_code=getattr(exc, "exit_code", None),
                stderr=getattr(exc, "stderr", None),
            ) from exc
        if isinstance(exc, CLIJSONDecodeError):
            raise AgentProcessError(f"协议解析错误: {exc}") from exc
        raise AgentError(f"SDK 错误: {exc}") from exc

    def _raise_on_no_result(
        self, output_model: type, elapsed: float, count: int
    ) -> None:
        """无结构化输出时根据原因抛出合适异常。"""
        rm = self._last_result

        if rm and getattr(rm, "is_error", False):
            raise AgentProcessError(
                f"查询返回错误: {getattr(rm, 'errors', None)}",
                errors=getattr(rm, "errors", None),
            )

        if rm:
            stop = getattr(rm, "stop_reason", None)
            if stop in ("max_turns_reached", "error_max_budget_usd"):
                raise AgentBudgetExceededError(
                    f"查询终止: {stop} "
                    f"(turns={getattr(rm, 'num_turns', '?')}, "
                    f"cost=${getattr(rm, 'total_cost_usd', '?')})",
                    actual_turns=getattr(rm, "num_turns", 0) or 0,
                    actual_cost_usd=getattr(rm, "total_cost_usd", None),
                )

        raw = _extract_raw_dict(rm) if rm else None
        raise AgentValidationError(
            f"未收到结构化输出 ({count} 条消息, {elapsed:.1f}s) | "
            f"model={output_model.__name__}",
            raw_data=raw,
            model_class=output_model,
        )

    def _get_cost(self) -> float | None:
        if self._last_result:
            return getattr(self._last_result, "total_cost_usd", None)
        return None


# ============================================================================
# 快捷函数
# ============================================================================


async def ask(
    prompt: str,
    output_model: type[T],
    *,
    model: str | None = None,
    system_prompt: str | None = None,
    max_turns: int | None = None,
    **kwargs,
) -> T:
    """一行完成结构化查询。

    Example:
        result = await ask("分析情感", SentimentOutput, model="claude-opus-4-5")
    """
    config_fields = set(Agent_config_field_names())
    filtered = {k: v for k, v in kwargs.items() if k in config_fields}

    agent = Agent(AgentConfig(
        model=model,
        system_prompt=system_prompt,
        max_turns=max_turns,
        **filtered,
    ))
    return await agent.ask(prompt, output_model)


def agent_config_field_names() -> set[str]:
    return set(AgentConfig.model_fields.keys())


# ============================================================================
# 演示
# ============================================================================


class SentimentOutput(BaseModel):
    sentiment: str = Field(description="positive/negative/neutral")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1)
    keywords: list[str] = Field(description="关键词")


class CodeIssue(BaseModel):
    severity: str = Field(description="critical/major/minor/info")
    line: int | None = Field(default=None)
    description: str
    suggestion: str | None = Field(default=None)


class CodeReviewOutput(BaseModel):
    score: int = Field(description="评分 0-10", ge=0, le=10)
    issues: list[CodeIssue] = Field(default_factory=list)
    overall: str


class SummaryOutput(BaseModel):
    title: str
    points: list[str]
    word_count: int = Field(description="估计字数")


class CalcOutput(BaseModel):
    answer: float
    steps: list[str]


def _print_header(title: str) -> None:
    w = min(60, max(len(title) + 8, 40))
    print("=" * w)
    print(f"  {title}")
    print("=" * w)


def _print_stats(agent: Agent) -> None:
    """打印查询统计摘要。"""
    s = agent.last_stats
    print(f"  --- 统计 ---")
    print(f"  {s.summary()}")
    if s.tool_calls:
        for name, count in s.tool_calls.items():
            print(f"    {name}: {count} 次")
    if s.token_usage:
        print(f"    tokens: {s.token_usage}")
    if s.model_usage:
        print(f"    model_usage: {s.model_usage}")
    if s.tasks:
        for t in s.tasks:
            print(f"    task[{t.get('task_id','?')}] {t.get('description','?')} → {t.get('status','?')}")
    print()


async def demo_sentiment() -> None:
    """Demo 1: 基本情感分析。"""
    _print_header("Demo 1: 基本情感分析")

    agent = Agent(AgentConfig(max_turns=1))
    result = await agent.ask(
        "分析以下文本的情感倾向: 这个产品太棒了！物流很快，客服也很耐心。",
        SentimentOutput,
    )
    print(f"  情感:     {result.sentiment}")
    print(f"  置信度:   {result.confidence:.2f}")
    print(f"  关键词:   {', '.join(result.keywords)}")
    print("  [OK] Pydantic 验证通过")
    _print_stats(agent)


async def demo_review() -> None:
    """Demo 2: 嵌套模型 — 代码审查。"""
    _print_header("Demo 2: 代码审查（嵌套模型）")

    code = """\
def calc(x, y):
    return x+y

def process(data):
    results = []
    for i in data:
        results.append(calc(i, i*2))
    return results"""

    agent = Agent(AgentConfig(
        system_prompt="你是资深代码审查专家，从可读性、性能、规范三个维度审查。",
        max_turns=2,
        effort="medium",
    ))
    result = await agent.ask(f"审查以下 Python 代码:\n\n{code}", CodeReviewOutput)
    print(f"  评分:     {result.score}/10")
    print(f"  总体评价: {result.overall}\n")
    if result.issues:
        for issue in result.issues:
            line = f"L{issue.line}" if issue.line else "  -"
            print(f"  [{issue.severity.upper():>8}] {line}: {issue.description}")
    else:
        print("  [无问题]")
    _print_stats(agent)


async def demo_tools() -> None:
    """Demo 3: Tools + permission_mode + cwd 配置。"""
    _print_header("Demo 3: Tools & CWD 配置")

    agent = Agent(AgentConfig(
        tools=["Read", "Grep", "Glob"],
        allowed_tools=["Read", "Grep", "Glob"],
        permission_mode="bypassPermissions",
        cwd=Path(__file__).parent.parent,  # 项目根目录
        max_turns=3,
    ))
    result = await agent.ask(
        "读取 README.md 文件（如果存在），用 3 个要点概括其内容。",
        SummaryOutput,
    )
    print(f"  标题:  {result.title}")
    for p in result.points:
        print(f"  - {p}")
    print(f"  字数估计: {result.word_count}")
    _print_stats(agent)


async def demo_mcp() -> None:
    """Demo 4: In-process MCP Server。"""
    _print_header("Demo 4: MCP Server (Calculator)")

    try:
        from claude_agent_sdk import tool, create_sdk_mcp_server
    except ImportError:
        print("  [SKIP] create_sdk_mcp_server 不可用\n")
        return

    @tool("add", "加法", {"a": float, "b": float})
    async def add_tool(args: dict) -> dict:
        a, b = args["a"], args["b"]
        return {"content": [{"type": "text", "text": f"{a} + {b} = {a + b}"}]}

    @tool("multiply", "乘法", {"a": float, "b": float})
    async def mul_tool(args: dict) -> dict:
        a, b = args["a"], args["b"]
        return {"content": [{"type": "text", "text": f"{a} * {b} = {a * b}"}]}

    server = create_sdk_mcp_server(
        name="calculator",
        version="1.0.0",
        tools=[add_tool, mul_tool],
    )

    agent = Agent(AgentConfig(
        mcp_servers={"calc": server},
        permission_mode="bypassPermissions",
        max_turns=5,
    ))
    result = await agent.ask(
        "使用计算器工具分步计算 (15 × 4) + 7，列出每一步。",
        CalcOutput,
    )
    print(f"  答案: {result.answer}")
    for step in result.steps:
        print(f"  步骤: {step}")
    _print_stats(agent)


# ============================================================================
# 入口
# ============================================================================

DEMOS = {
    "sentiment": demo_sentiment,
    "review": demo_review,
    "tools": demo_tools,
    "mcp": demo_mcp,
}


async def run_demo(target: str) -> None:
    """运行指定演示或全部。"""
    fn = DEMOS.get(target)
    if fn is None:
        print(f"可用演示: {', '.join(DEMOS)} | all")
        sys.exit(1)

    if target == "all":
        for name in DEMOS:
            await DEMOS[name]()
    else:
        await fn()

    print("全部演示完成。")


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    asyncio.run(run_demo(target))


if __name__ == "__main__":
    main()
