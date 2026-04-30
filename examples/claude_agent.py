#!/usr/bin/env python3
"""可移植的 Claude Agent SDK 封装 — 单文件，零项目依赖。

基于 claude-agent-sdk query() 模式，提供：
- AgentConfig: 统一配置（tools / MCP / skills / 结构化输出 / cwd / model ...）
- Agent.ask(): 类型安全的结构化查询，失败抛异常而非返回 None
- ask(): 一行快捷函数
- QueryStats: token / 工具调用 / skills / 任务统计
- 完善的日志: INFO 级别摘要 + DEBUG 级别字段详情

迁移方式:
    cp examples/claude_agent.py your_project/claude_agent.py
    from claude_agent import Agent, AgentConfig, ask

运行:
    python claude_agent.py                  # 演示（正常模式）
    python claude_agent.py --debug          # 演示（DEBUG 日志）

依赖: pydantic>=2.0, claude-agent-sdk>=0.1.71, opentelemetry-sdk>=1.41, rich
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

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
    """Base exception."""


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
# 配置类
# ============================================================================


class AgentConfig(BaseModel):
    """Claude Agent 查询配置。

    覆盖 ClaudeAgentOptions 的常用字段。
    可通过 Agent() 注入，也可在 ask() 时按调用覆盖。
    """

    # ── 模型 & 行为 ──────────────────────────────
    model: str | None = Field(default=None, description="模型 ID")
    fallback_model: str | None = Field(default=None)
    effort: Literal["low", "medium", "high", "max"] | None = None
    thinking: dict[str, Any] | None = Field(
        default=None,
        description='{"type":"adaptive"} | {"type":"enabled","budget_tokens":N} | {"type":"disabled"}',
    )
    betas: list[str] = Field(default_factory=list, description="Beta 功能，如 context-1m-2025-08-07")
    user: str | None = Field(default=None, description="系统用户名（传给子进程 Popen），非自定义标识")

    # ── 提示词 ────────────────────────────────────
    system_prompt: str | dict[str, Any] | None = Field(
        default=None,
        description="str | {'type':'preset','preset':'claude_code'} | {'type':'file','path':'...'}",
    )

    # ── 会话 & 工作目录 ───────────────────────────
    cwd: str | Path | None = Field(default_factory=lambda: Path.cwd())
    session_id: str | None = Field(default=None, description="指定 session ID（UUID）")
    resume: str | None = Field(default=None, description="恢复指定 session")
    continue_conversation: bool = Field(default=False, description="继续最近对话")
    add_dirs: list[str] = Field(default_factory=list, description="额外可访问目录（绝对路径）")

    # ── 权限 & 安全 ───────────────────────────────
    permission_mode: Literal[
        "default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"
    ] | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None

    # ── 工具 & 技能 ───────────────────────────────
    tools: list[str] | None = Field(default=None)
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)
    skills: list[str] | Literal["all"] | None = Field(default=None)

    # ── MCP & 插件 ─────────────────────────────────
    mcp_servers: dict[str, Any] = Field(default_factory=dict)
    plugins: list[dict[str, Any]] = Field(default_factory=list, description="插件配置列表")

    # ── 环境 & CLI ─────────────────────────────────
    env: dict[str, str] = Field(default_factory=dict)
    cli_path: str | Path | None = Field(default=None)
    extra_args: dict[str, str | None] = Field(
        default_factory=dict, description="直传 CLI 的额外参数（无 -- 前缀）",
    )
    settings: str | None = Field(default=None, description="额外 settings JSON 文件路径")

    # ── 高级选项 ─────────────────────────────────
    include_partial_messages: bool = Field(
        default=False, description="包含流式部分消息（SDKPartialAssistantMessage）",
    )
    setting_sources: list[Literal["user", "project", "local"]] | None = Field(
        default=None,
        description="控制加载哪些设置源。[] = 纯 SDK 隔离模式（不读磁盘设置）",
    )

    def to_sdk_options(self) -> Any:
        """转换为 ClaudeAgentOptions 实例。"""
        from claude_agent_sdk import ClaudeAgentOptions

        kwargs = self.model_dump(exclude_none=True)
        thinking_val = kwargs.pop("thinking", None)
        system_val = kwargs.pop("system_prompt", None)

        sdk_fields = {
            f.name for f in __import__("dataclasses").fields(ClaudeAgentOptions)
            if hasattr(ClaudeAgentOptions, f.name)
        }
        filtered = {k: v for k, v in kwargs.items() if k in sdk_fields}

        options = ClaudeAgentOptions(**filtered)

        # thinking 需要特殊处理（dict → ThinkingConfig）
        if thinking_val is not None:
            options.thinking = thinking_val

        # system_prompt 支持 preset / file / str 三种格式
        if system_val is not None:
            if isinstance(system_val, dict) and "type" in system_val:
                options.system_prompt = system_val  # type: preset | file
            else:
                options.system_prompt = system_val  # plain str

        return options


# ============================================================================
# Schema 工具函数
# ============================================================================


def output_format_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """从 Pydantic 模型生成 SDK output_format（自动内联 $defs）。"""
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

    路径: ResultMessage.structured_output > ToolUseBlock("StructuredOutput")
    """
    raw = _extract_raw_dict(message)
    if raw is None:
        return None
    try:
        return model_class.model_validate(raw)
    except ValidationError:
        return None


def _extract_raw_dict(message: object) -> dict[str, Any] | None:
    if hasattr(message, "structured_output"):
        output = getattr(message, "structured_output")
        if isinstance(output, dict):
            return output
    if hasattr(message, "content"):
        for block in getattr(message, "content", []):
            if getattr(block, "name", None) == "StructuredOutput":
                inp = getattr(block, "input", None)
                if isinstance(inp, dict):
                    return inp
    return None


# ============================================================================
# 查询统计
# ============================================================================


@dataclass
class QueryStats:
    """单次查询运行统计。"""

    tool_calls: dict[str, int] = field(default_factory=dict)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    token_usage: dict[str, Any] | None = None
    model_usage: dict[str, Any] | None = None
    message_count: int = 0
    assistant_count: int = 0
    duration_sec: float = 0.0
    total_cost_usd: float | None = None
    num_turns: int = 0
    model: str = ""
    max_turns: int = 0
    session_id: str = ""          # 实际 session ID
    stop_reason: str = ""          # 结束原因


# ============================================================================
# Agent 类
# ============================================================================


class Agent:
    """可移植的 Claude Agent SDK 封装（query 模式）。"""

    def __init__(self, config: AgentConfig | None = None):
        self.config = config or AgentConfig()
        self._last_result: object | None = None
        self._stats: QueryStats = QueryStats()

    @property
    def last_stats(self) -> QueryStats:
        return self._stats

    async def ask(self, prompt: str, output_model: type[T], **overrides) -> T:
        """发送查询并返回验证后的结构化结果（失败抛异常）。"""
        merged = self.config.model_copy(update=overrides) if overrides else self.config
        options = self._build_options(output_model, merged)

        self._stats = QueryStats(max_turns=merged.max_turns or 0)
        stats = self._stats

        _print_config(merged, prompt)

        start = time.monotonic()
        result: T | None = None
        query_iter = None
        got_structured = False

        try:
            from claude_agent_sdk import query as sdk_query

            query_iter = sdk_query(prompt=prompt, options=options)
            async for message in query_iter:
                stats.message_count += 1
                self._handle_message(message)
                self._check_rate_limit(message)

                parsed = parse_with_model(message, output_model)
                if parsed is not None and not got_structured:
                    result = parsed
                    got_structured = True
                    console.print("  [green]✓[/] 结构化输出已提取")

                if self._is_result_message(message):
                    self._last_result = message
                    if got_structured:
                        break

        except ImportError:
            raise AgentConnectionError(
                "claude-agent-sdk 未安装: pip install 'claude-agent-sdk>=0.1.71'"
            )
        except AgentError:
            raise
        except Exception as exc:
            if got_structured and result is not None:
                pass  # 清理阶段的子进程退出码等，忽略
            else:
                self._translate_exception(exc)
        finally:
            if query_iter is not None:
                await _aclose_silent(query_iter)

        elapsed = time.monotonic() - start
        stats.duration_sec = elapsed
        stats.total_cost_usd = self._get_cost()

        result_turns = getattr(self._last_result, "num_turns", None)
        stats.num_turns = result_turns if result_turns else stats.assistant_count

        if result is None:
            self._raise_on_no_result(output_model, elapsed, stats.message_count)

        return result

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_options(self, output_model: type[BaseModel], config: AgentConfig) -> Any:
        options = config.to_sdk_options()
        options.output_format = output_format_schema(output_model)
        return options

    def _handle_message(self, message: object) -> None:
        """分发消息到日志处理器 + 收集统计。"""
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
                UserMessage,
            )
        except ImportError:
            logger.debug("消息 (SDK 类型不可用): %r", type(message).__name__)
            return

        if isinstance(message, StreamEvent):
            pass  # 静默，需要时 --debug 开启
        elif isinstance(message, AssistantMessage):
            self._stats.assistant_count += 1
            turn = self._stats.assistant_count
            model = getattr(message, "model", "") or ""
            if model and not self._stats.model:
                self._stats.model = model
            blocks = getattr(message, "content", [])
            block_names = [type(b).__name__.replace("Block", "") for b in blocks]
            console.print(f"  [dim][{turn}/{self._stats.max_turns or '?'}][/dim]  {' + '.join(block_names)}")
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
            self._log_system_message(message)
        elif isinstance(message, UserMessage):
            self._log_user_message(message)
        else:
            logger.debug("未知消息 | %s", type(message).__name__)

    def _log_stream_event(self, message: object) -> None:
        event = message.event
        etype = event.get("type", "?")
        safe = {k: v for k, v in event.items() if k not in ("delta", "content")}
        logger.debug("StreamEvent[%s]", etype)

        if etype == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                logger.debug("  text | %r", delta.get("text", "")[:100])
            elif delta.get("type") == "thinking_delta":
                logger.debug("  thinking")

    def _log_assistant_message(self, message: object) -> None:
        block_counts: dict[str, int] = {}
        try:
            from claude_agent_sdk import TextBlock, ThinkingBlock, ToolUseBlock

            for block in message.content:
                bname = type(block).__name__
                block_counts[bname] = block_counts.get(bname, 0) + 1
                if isinstance(block, TextBlock):
                    logger.debug("  Text[%d] | %r", block_counts[bname], block.text[:120])
                elif isinstance(block, ThinkingBlock):
                    sig = block.signature[:40] if block.signature else ""
                    logger.debug("  Think[%d] | %s", block_counts[bname], sig)
                elif isinstance(block, ToolUseBlock):
                    keys = list(block.input.keys()) if block.input else []
                    logger.debug("  Tool[%d] | %s | keys=%s", block_counts[bname], block.name, keys)
                    self._stats.tool_calls[block.name] = (
                        self._stats.tool_calls.get(block.name, 0) + 1
                    )

            # 收集 AssistantMessage 级别的 token 用量
            msg_usage = getattr(message, "usage", None)
            if msg_usage and isinstance(msg_usage, dict):
                self._aggregate_tokens(msg_usage)
                logger.debug("  [%d] usage=%s", self._stats.assistant_count, msg_usage)
        except Exception:
            pass

        logger.debug(
            "Assistant | model=%s stop=%s blocks=%s",
            message.model, message.stop_reason, block_counts,
        )

    def _aggregate_tokens(self, usage: dict[str, Any]) -> None:
        """累加 token 用量到 stats。"""
        if self._stats.token_usage is None:
            self._stats.token_usage = {}
        for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"):
            val = usage.get(key)
            if val is not None and isinstance(val, (int, float)):
                prev = self._stats.token_usage.get(key, 0)
                self._stats.token_usage[key] = prev + val

    def _log_result_message(self, message: object) -> None:
        usage = getattr(message, "usage", None)
        model_usage = getattr(message, "model_usage", None)
        if usage and isinstance(usage, dict):
            self._aggregate_tokens(usage)
        if model_usage:
            self._stats.model_usage = model_usage

        # 捕获会话元信息
        sid = getattr(message, "session_id", None)
        if sid:
            self._stats.session_id = str(sid)[:12]
        stop = getattr(message, "stop_reason", None)
        if stop:
            self._stats.stop_reason = stop

        cost = getattr(message, "total_cost_usd", None)
        dur_s = getattr(message, "duration_ms", 0) / 1000
        turns = getattr(message, "num_turns", None)

        r_parts = [f"{dur_s:.1f}s"]
        if cost is not None:
            r_parts.append(f"${cost:.4f}")
        if turns:
            r_parts.append(f"{turns}轮")
        if stop:
            r_parts.append(f"stop={stop}")
        console.print(f"  [green]done[/]   {' | '.join(r_parts)}")

    def _log_rate_limit_event(self, message: object) -> None:
        info = message.rate_limit_info
        util_pct = (info.utilization or 0) * 100
        if info.status == "rejected":
            logger.error("限流拒绝 | type=%s 利用率=%.0f%%", info.rate_limit_type, util_pct)
        else:
            logger.warning("限流警告 | %s 利用率=%.0f%%", info.rate_limit_type, util_pct)

    def _log_system_message(self, message: object) -> None:
        subtype = getattr(message, "subtype", "?")
        # 只在非 init/notification 时记录，减少噪音
        if subtype not in ("init",):
            logger.debug("System | %s", subtype)

    def _log_user_message(self, message: object) -> None:
        content = getattr(message, "content", "")
        text = content[:80] if isinstance(content, str) else f"<{len(content)} blocks>"
        uuid = getattr(message, "uuid", "")[:8]
        logger.debug("User | uuid=%s.. | %s", uuid, text)

    def _check_rate_limit(self, message: object) -> None:
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
                status=info.status, resets_at=info.resets_at,
                utilization=info.utilization,
            )

    def _track_task_start(self, message: object) -> None:
        self._stats.tasks.append({
            "task_id": getattr(message, "task_id", "?"),
            "description": getattr(message, "description", ""),
            "status": "started",
            "task_type": getattr(message, "task_type", None),
        })
        logger.debug(
            "TaskStart | id=%s | %s",
            message.task_id, message.description,
        )

    def _track_task_end(self, message: object) -> None:
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
                "status": getattr(message, "status", "?"),
                "summary": getattr(message, "summary", ""),
            })
        logger.debug("TaskEnd | id=%s | status=%s", task_id, getattr(message, "status", "?"))

    @staticmethod
    def _is_result_message(message: object) -> bool:
        return getattr(message, "subtype", None) in ("success", "error")

    def _translate_exception(self, exc: BaseException) -> None:
        from claude_agent_sdk import (
            CLIConnectionError, CLINotFoundError, ProcessError, CLIJSONDecodeError,
        )
        if isinstance(exc, CLINotFoundError):
            raise AgentConnectionError(f"Claude Code CLI 未找到: {exc}") from exc
        if isinstance(exc, CLIConnectionError):
            raise AgentConnectionError(f"无法连接 Claude Code: {exc}") from exc
        if isinstance(exc, ProcessError):
            raise AgentProcessError(str(exc), exit_code=getattr(exc, "exit_code", None), stderr=getattr(exc, "stderr", None)) from exc
        if isinstance(exc, CLIJSONDecodeError):
            raise AgentProcessError(f"协议解析错误: {exc}") from exc
        raise AgentError(f"SDK 错误: {exc}") from exc

    def _raise_on_no_result(self, output_model: type, elapsed: float, count: int) -> None:
        rm = self._last_result
        if rm and getattr(rm, "is_error", False):
            raise AgentProcessError(f"查询返回错误: {getattr(rm, 'errors', None)}")
        if rm:
            stop = getattr(rm, "stop_reason", None)
            if stop in ("max_turns_reached", "error_max_budget_usd"):
                raise AgentBudgetExceededError(
                    f"查询终止: {stop} (turns={getattr(rm, 'num_turns', '?')}, cost=${getattr(rm, 'total_cost_usd', '?')})",
                    actual_turns=getattr(rm, "num_turns", 0) or 0,
                    actual_cost_usd=getattr(rm, "total_cost_usd", None),
                )
        raw = _extract_raw_dict(rm) if rm else None
        raise AgentValidationError(
            f"无结构化输出 ({count} 条消息, {elapsed:.1f}s) | model={output_model.__name__}",
            raw_data=raw, model_class=output_model,
        )

    def _get_cost(self) -> float | None:
        if self._last_result:
            return getattr(self._last_result, "total_cost_usd", None)
        return None


async def _aclose_silent(aiter) -> None:
    """安全关闭异步生成器，忽略已关闭/未实现 aclose 的情况。"""
    if hasattr(aiter, "aclose"):
        try:
            await aiter.aclose()
        except (RuntimeError, AttributeError, StopAsyncIteration):
            pass


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
    """一行完成结构化查询。"""
    config_fields = set(AgentConfig.model_fields.keys())
    filtered = {k: v for k, v in kwargs.items() if k in config_fields}
    agent = Agent(AgentConfig(model=model, system_prompt=system_prompt, max_turns=max_turns, **filtered))
    return await agent.ask(prompt, output_model)


# ============================================================================
# 演示模型 & 函数
# ============================================================================


class CodeIssue(BaseModel):
    severity: str = Field(description="critical/major/minor/info")
    line: int | None = Field(default=None)
    description: str
    suggestion: str | None = Field(default=None)


class CodeReviewOutput(BaseModel):
    score: int = Field(description="评分 0-10", ge=0, le=10)
    issues: list[CodeIssue] = Field(default_factory=list)
    overall: str


def _print_header(title: str) -> None:
    console.print(Panel(f"[bold cyan]{title}[/]", box=box.DOUBLE, padding=(0, 2)))


def _print_config(config: AgentConfig, prompt: str) -> None:
    p = prompt.replace("\n", " ").strip()[:80]

    tbl = Table(box=None, padding=(0, 1), show_header=False)
    tbl.add_column("key", style="dim", width=10)
    tbl.add_column("value")

    tbl.add_row("prompt", f"[dim]{p}[/]")
    tbl.add_row("model", config.model or "[dim]default[/]")
    if config.fallback_model:
        tbl.add_row("fallback", f"{config.fallback_model}")
    tbl.add_row("cwd", str(config.cwd))

    opts: list[str] = []
    if config.effort:
        opts.append(f"effort={config.effort}")
    opts.append(f"turns={config.max_turns or '?'}")
    if config.max_budget_usd is not None:
        opts.append(f"budget=${config.max_budget_usd:.2f}")
    if config.tools:
        opts.append(f"tools={','.join(config.tools)}")
    if config.allowed_tools:
        opts.append(f"allowed={','.join(config.allowed_tools)}")
    if config.disallowed_tools:
        opts.append(f"deny={','.join(config.disallowed_tools)}")
    if config.skills:
        sk = config.skills if isinstance(config.skills, str) else ",".join(config.skills)
        opts.append(f"skills={sk}")
    if config.permission_mode and config.permission_mode != "default":
        opts.append(f"perm={config.permission_mode}")
    if config.thinking:
        ttype = config.thinking.get("type", "?") if isinstance(config.thinking, dict) else "?"
        opts.append(f"think={ttype}")
    if config.betas:
        opts.append(f"betas={','.join(config.betas)}")
    if config.user:
        opts.append(f"user={config.user}")

    if opts:
        tbl.add_row("options", "  ".join(opts))

    advanced: list[str] = []
    if config.session_id:
        advanced.append(f"session={config.session_id[:8]}...")
    if config.resume:
        advanced.append(f"resume={config.resume[:8]}...")
    if config.continue_conversation:
        advanced.append("continue=true")
    if config.include_partial_messages:
        advanced.append("partial_msgs=true")
    if config.setting_sources is not None:
        advanced.append(f"settings={config.setting_sources or '[]'}")
    if config.add_dirs:
        advanced.append(f"+dirs={len(config.add_dirs)}")
    if config.extra_args:
        advanced.append(f"cli_args={list(config.extra_args.keys())}")
    if config.plugins:
        advanced.append(f"plugins={len(config.plugins)}")
    if config.mcp_servers:
        advanced.append(f"mcp={list(config.mcp_servers.keys())}")

    if advanced:
        tbl.add_row("advanced", "  ".join(advanced))

    console.print(tbl)
    console.print()


# ── 严重度颜色映射 ──────────────────────────────────────

_SEVERITY_STYLE: dict[str, str] = {
    "critical": "bold red",
    "major": "bold yellow",
    "minor": "cyan",
    "info": "dim",
}


def _sev(text: str, severity: str) -> Text:
    """带颜色的严重度标签。"""
    style = _SEVERITY_STYLE.get(severity.lower(), "")
    return Text(f"[{severity.upper()}]", style=style)


def _print_stats(agent: Agent) -> None:
    """打印统计信息。"""
    s = agent.last_stats
    lines: list[str] = []

    # 基础信息
    if s.model:
        lines.append(f"  model   [cyan]{s.model}[/]")
    if s.total_cost_usd is not None:
        lines.append(f"  cost    [green]${s.total_cost_usd:.4f}[/]   {s.duration_sec:.1f}s   {s.num_turns}轮")

    # Token
    if s.token_usage:
        inp = s.token_usage.get("input_tokens", "?")
        out = s.token_usage.get("output_tokens", "?")
        cache_w = s.token_usage.get("cache_creation_input_tokens")
        cache_r = s.token_usage.get("cache_read_input_tokens", "?")
        tok = f"  tokens  {inp} in / {out} out"
        if cache_w or (cache_r and cache_r != "?"):
            cw = str(cache_w) if cache_w else "-"
            cr = str(cache_r) if cache_r != "?" else "-"
            tok += f"   [dim]cache: {cw}w / {cr}r[/]"
        lines.append(tok)

    # 工具 & 会话
    if s.tool_calls:
        for k, v in s.tool_calls.items():
            lines.append(f"  tool    {k}[dim]×{v}[/]")
    if s.session_id:
        lines.append(f"  session [dim]{s.session_id}[/]")
    if s.stop_reason:
        lines.append(f"  stop    {s.stop_reason}")

    if lines:
        console.print("\n".join(lines))


async def demo() -> None:
    _print_header("Claude Agent SDK — 结构化输出演示")
    code = """\
def calc(x, y):
    return x+y

def process(data):
    results = []
    for i in data:
        results.append(calc(i, i*2))
    return results"""

    # 展示完整配置能力
    agent = Agent(AgentConfig(
        system_prompt="你是资深代码审查专家，从可读性、性能、规范三个维度审查。",
        max_turns=2,
        effort="medium",
        # 以下是新增集成的原生能力示例：
        setting_sources=["project"],          # 只加载项目设置（隔离模式）
        disallowed_tools=["WebFetch"],         # 禁用不需要的工具
    ))
    result = await agent.ask(f"审查以下 Python 代码:\n\n{code}", CodeReviewOutput)

    console.print()
    score_color = "green" if result.score >= 7 else "yellow" if result.score >= 4 else "red"
    console.print(f"  评分:     [{score_color}]{result.score}/10[/]")
    console.print(f"  总体:     {result.overall}")

    if result.issues:
        tbl = Table(box=None, padding=(0, 1), show_header=False)
        tbl.add_column("sev", width=8)
        tbl.add_column("line", width=4)
        tbl.add_column("description")
        for issue in result.issues:
            line = f"L{issue.line}" if issue.line else "-"
            tbl.add_row(_sev(issue.severity, issue.severity), f"[dim]{line}[/]", issue.description)
        console.print(tbl)
    else:
        console.print("  [green]无问题[/]")
    _print_stats(agent)
    console.print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude Agent SDK 演示")
    parser.add_argument("--debug", action="store_true", help="启用 DEBUG 日志级别")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                           format="%(asctime)s [%(levelname)s] %(message)s",
                           datefmt="%H:%M:%S")
    else:
        logging.basicConfig(level=logging.WARNING,
                           format="%(asctime)s [%(levelname)s] %(message)s",
                           datefmt="%H:%M:%S")

    for name in ("claude_agent_sdk", "claude_agent_sdk._internal"):
        logging.getLogger(name).setLevel(logging.ERROR)

    asyncio.run(demo())


if __name__ == "__main__":
    main()
