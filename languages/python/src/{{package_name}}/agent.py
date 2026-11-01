"""Claude Agent SDK 原生配置与结构化查询封装。

保持 SDK 的 `ClaudeAgentOptions`、`query()`、MCP、Skills、权限和消息类型
为事实源；本模块只负责项目配置、结构化输出、日志接入和轻量终端展示。
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Literal, NoReturn, TypeVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from {{ package_name }}.agent_log import AgentEventLogger, redact_text
from {{ package_name }}.agent_models import CodeReviewOutput, SentimentOutput
from {{ package_name }}.agent_state import RuntimeStateConfig, runtime_state_env
from {{ package_name }}.logger import console
from {{ package_name }}.prompt import RenderedPrompt

T = TypeVar("T", bound=BaseModel)
SettingSource = Literal["user", "project", "local"]
PermissionMode = Literal[
    "default", "acceptEdits", "bypassPermissions", "plan", "dontAsk", "auto"
]


def _project_setting_sources() -> list[SettingSource]:
    return ["project"]


def _default_system_prompt() -> dict[str, str]:
    return {
        "type": "preset",
        "preset": "claude_code",
    }


class AgentError(RuntimeError):
    """Agent 执行失败的基类，调用方按子类决定重试、补装还是放弃。"""


class AgentConnectionError(AgentError):
    """Claude Code CLI 未安装或无法连接。"""


class AgentProcessError(AgentError):
    """子进程失败或协议解析错误。"""

    def __init__(
        self,
        message: str,
        exit_code: int | None = None,
        stderr: str | None = None,
    ) -> None:
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(message)


class AgentBudgetExceededError(AgentError):
    """达到 max_turns 或 max_budget_usd 上限。"""

    def __init__(
        self,
        message: str,
        stop_reason: str = "",
        num_turns: int | None = None,
        total_cost_usd: float | None = None,
    ) -> None:
        self.stop_reason = stop_reason
        self.num_turns = num_turns
        self.total_cost_usd = total_cost_usd
        super().__init__(message)


class AgentRateLimitError(AgentError):
    """触发 API 限流，等待后重试或改用其他模型。"""

    def __init__(
        self,
        message: str,
        rate_limit_type: str = "",
        resets_at: int | None = None,
        utilization: float | None = None,
    ) -> None:
        self.rate_limit_type = rate_limit_type
        self.resets_at = resets_at
        self.utilization = utilization
        super().__init__(message)


class AgentOutputError(AgentError):
    """Agent 未返回符合 Schema 的结构化结果。"""


class AgentLoggingConfig(BaseModel):
    """Agent 运行日志配置。"""

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    jsonl_path: Path = Path("logs/agent.jsonl")
    capture_stderr: bool = True
    debug_file: Path | None = None
    max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    backup_count: int = Field(default=5, ge=1, le=20)


class AgentConfig(BaseModel):
    """映射到 ClaudeAgentOptions 的项目配置。"""

    model_config = ConfigDict(populate_by_name=True)

    system_prompt: str | dict[str, str] = Field(default_factory=_default_system_prompt)
    model: str | None = None
    fallback_model: str | None = None
    tools: list[str] | Literal["claude_code"] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    disallowed_tools: list[str] = Field(default_factory=list)
    permission_mode: PermissionMode = "dontAsk"
    max_turns: int = Field(default=5, ge=1)
    max_budget_usd: float | None = Field(default=None, gt=0)
    cwd: Path = Field(default_factory=Path.cwd)
    mcp_config: Path | None = Path(".mcp.json")
    mcp_servers: dict[str, Any] | None = None
    strict_mcp_config: bool = True
    skills: list[str] | Literal["all"] = Field(default_factory=list)
    setting_sources: list[SettingSource] = Field(
        default_factory=_project_setting_sources
    )
    plugins: list[dict[str, Any]] = Field(default_factory=list)
    prompt_dir: Path = Path("config/prompts")
    default_prompt: str = "default"
    runtime_state: RuntimeStateConfig = Field(default_factory=RuntimeStateConfig)
    include_partial_messages: bool = False
    include_hook_events: bool = True
    forward_subagent_text: bool = False
    logging_config: AgentLoggingConfig = Field(
        default_factory=AgentLoggingConfig,
        alias="logging",
    )

    @model_validator(mode="after")
    def validate_mcp_source(self) -> "AgentConfig":
        if self.mcp_config is not None and self.mcp_servers is not None:
            raise ValueError("mcp_config and mcp_servers are mutually exclusive")
        return self

    @classmethod
    def from_yaml(cls, path: Path | str = "config/agent.yaml") -> "AgentConfig":
        """从 YAML 加载项目配置。"""
        config_path = Path(path).resolve()
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("Agent configuration must be a mapping")
        project_root = (
            config_path.parent.parent
            if config_path.parent.name == "config"
            else config_path.parent
        )
        data.setdefault("cwd", project_root)
        return cls.model_validate(data)

    def resolve_path(self, path: Path) -> Path:
        """相对路径始终以 Agent 工作目录为基准。"""
        return path if path.is_absolute() else self.cwd / path

    def to_option_kwargs(
        self,
        output_format: dict[str, Any],
        system_prompt: str | dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """构建 ClaudeAgentOptions 原生参数，不实例化 SDK 类型。"""
        tools: list[str] | dict[str, str]
        if self.tools == "claude_code":
            tools = {"type": "preset", "preset": "claude_code"}
        else:
            tools = self.tools

        if self.mcp_servers is not None:
            mcp_servers: dict[str, Any] | str = self.mcp_servers
        elif self.mcp_config is not None:
            mcp_servers = str(self.resolve_path(self.mcp_config))
        else:
            mcp_servers = {}

        options: dict[str, Any] = {
            "system_prompt": system_prompt or self.system_prompt,
            "tools": tools,
            "allowed_tools": self.allowed_tools,
            "disallowed_tools": self.disallowed_tools,
            "permission_mode": self.permission_mode,
            "max_turns": self.max_turns,
            "cwd": self.cwd,
            "mcp_servers": mcp_servers,
            "strict_mcp_config": self.strict_mcp_config,
            "skills": self.skills,
            "setting_sources": self.setting_sources,
            "plugins": self.plugins,
            "include_partial_messages": self.include_partial_messages,
            "include_hook_events": self.include_hook_events,
            "forward_subagent_text": self.forward_subagent_text,
            "output_format": output_format,
        }
        if self.model is not None:
            options["model"] = self.model
        if self.fallback_model is not None:
            options["fallback_model"] = self.fallback_model
        if self.max_budget_usd is not None:
            options["max_budget_usd"] = self.max_budget_usd
        if self.logging_config.debug_file is not None:
            options["extra_args"] = {
                "debug-file": str(self.resolve_path(self.logging_config.debug_file)),
            }
        return options


def output_format_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """从 Pydantic 模型生成 SDK JSON Schema，并内联本地引用。"""
    schema = model_class.model_json_schema()
    definitions = schema.pop("$defs", {})

    def inline(node: Any) -> Any:
        if isinstance(node, dict):
            reference = node.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/$defs/"):
                name = reference.removeprefix("#/$defs/")
                if name in definitions:
                    resolved = inline(deepcopy(definitions[name]))
                    siblings = {
                        key: value for key, value in node.items() if key != "$ref"
                    }
                    if siblings and isinstance(resolved, dict):
                        resolved.update(inline(siblings))
                    return resolved
            return {key: inline(value) for key, value in node.items()}
        if isinstance(node, list):
            return [inline(item) for item in node]
        return node

    return {
        "type": "json_schema",
        "schema": inline(schema),
        "name": model_class.__name__,
        "strict": True,
    }


def parse_with_model(message: object, model_class: type[T]) -> T | None:
    """从 SDK ResultMessage 或 StructuredOutput 工具块解析结果。"""
    raw = _extract_raw_dict(message)
    if raw is None:
        return None
    try:
        return model_class.model_validate(raw)
    except ValidationError:
        return None


def _extract_raw_dict(message: object) -> dict[str, Any] | None:
    output = getattr(message, "structured_output", None)
    if isinstance(output, dict):
        return output
    for block in getattr(message, "content", []):
        if getattr(block, "name", None) == "StructuredOutput":
            tool_input = getattr(block, "input", None)
            if isinstance(tool_input, dict):
                return tool_input
    return None


_BUDGET_STOP_REASONS = frozenset({"max_turns_reached", "error_max_budget_usd"})


def _raise_on_rate_limit(message: object) -> None:
    """限流被拒时抛出可重试的错误。"""
    try:
        from claude_agent_sdk import RateLimitEvent
    except ImportError:
        return
    if not isinstance(message, RateLimitEvent):
        return
    info = message.rate_limit_info
    if getattr(info, "status", "") != "rejected":
        return
    raise AgentRateLimitError(
        f"限流拒绝: {getattr(info, 'rate_limit_type', '')}",
        rate_limit_type=str(getattr(info, "rate_limit_type", "")),
        resets_at=getattr(info, "resets_at", None),
        utilization=getattr(info, "utilization", None),
    )


def _raise_on_terminal_result(result: object | None) -> NoReturn:
    """查询结束时按终止原因分类失败，未得到结构化结果也在这里报出。"""
    if result is None:
        raise AgentOutputError("Agent 未返回符合 Schema 的结构化结果")

    stop_reason = str(getattr(result, "stop_reason", "") or "")
    if stop_reason in _BUDGET_STOP_REASONS:
        raise AgentBudgetExceededError(
            f"查询终止: {stop_reason}",
            stop_reason=stop_reason,
            num_turns=getattr(result, "num_turns", None),
            total_cost_usd=getattr(result, "total_cost_usd", None),
        )
    if getattr(result, "is_error", False):
        errors = getattr(result, "errors", None) or getattr(result, "result", None)
        raise AgentProcessError(f"查询返回错误: {errors}")
    raise AgentOutputError("Agent 未返回符合 Schema 的结构化结果")


def _translate_exception(error: Exception) -> AgentError:
    """把 SDK 异常映射成调用方能够区分的错误类型。"""
    try:
        from claude_agent_sdk import (
            CLIConnectionError,
            CLIJSONDecodeError,
            CLINotFoundError,
            ProcessError,
        )
    except ImportError:
        return AgentError(f"SDK 错误: {error}")

    if isinstance(error, CLINotFoundError):
        return AgentConnectionError(f"Claude Code CLI 未找到: {error}")
    if isinstance(error, CLIConnectionError):
        return AgentConnectionError(f"无法连接 Claude Code: {error}")
    if isinstance(error, ProcessError):
        return AgentProcessError(
            str(error),
            exit_code=getattr(error, "exit_code", None),
            stderr=getattr(error, "stderr", None),
        )
    if isinstance(error, CLIJSONDecodeError):
        return AgentProcessError(f"协议解析错误: {error}")
    return AgentError(f"SDK 错误: {error}")


class AgentRunner:
    """基于 query() 的单次、无状态、结构化 Agent 执行器。"""

    def __init__(
        self,
        schema: dict[str, Any],
        config: AgentConfig | None = None,
        event_logger: AgentEventLogger | None = None,
    ) -> None:
        self.schema = schema
        self.config = config or AgentConfig()
        self.events = event_logger or _create_event_logger(self.config)

    async def run(self, prompt: str | RenderedPrompt, output_model: type[T]) -> T:
        """执行查询，返回通过 Pydantic 验证的结构化结果。"""
        try:
            from claude_agent_sdk import ClaudeAgentOptions, query
        except ImportError as error:
            raise RuntimeError(
                "claude-agent-sdk 未安装，请运行: uv sync --extra agent"
            ) from error

        prompt_text, system_prompt, prompt_fields = _resolve_prompt(prompt)
        self.events.start_run()
        try:
            with runtime_state_env(self.config.runtime_state, self.config.cwd) as env:
                option_kwargs = self.config.to_option_kwargs(
                    self.schema,
                    system_prompt=system_prompt,
                )
                option_kwargs["env"] = env
                if self.config.logging_config.capture_stderr:
                    option_kwargs["stderr"] = self.events.capture_stderr
                options = ClaudeAgentOptions(**option_kwargs)
                self._record_start(prompt_text, output_model, prompt_fields)
                result: T | None = None
                last_result: object | None = None
                async for message in query(prompt=prompt_text, options=options):
                    self.events.observe(message)
                    _render_message(message)
                    _raise_on_rate_limit(message)
                    if getattr(message, "subtype", None) in ("success", "error"):
                        last_result = message
                    parsed = parse_with_model(message, output_model)
                    if parsed is not None:
                        result = parsed
                if result is not None:
                    return result
                _raise_on_terminal_result(last_result)
        except AgentError as error:
            self._record_failure(error)
            raise
        except Exception as error:
            translated = _translate_exception(error)
            self._record_failure(translated)
            raise translated from error

    def _record_failure(self, error: BaseException) -> None:
        self.events.emit(
            "run_failed",
            level=40,
            error_type=type(error).__name__,
            error=redact_text(str(error))[:1000],
        )

    def _record_start(
        self,
        prompt: str,
        output_model: type[BaseModel],
        prompt_fields: dict[str, Any],
    ) -> None:
        self.events.run_started(
            prompt=prompt,
            output_model=output_model.__name__,
            metadata=prompt_fields,
        )
        self.events.emit(
            "run_configured",
            tools=self.config.tools,
            allowed_tools=self.config.allowed_tools,
            disallowed_tools=self.config.disallowed_tools,
            skills=self.config.skills,
            mcp_source=str(self.config.mcp_config or "programmatic"),
            strict_mcp_config=self.config.strict_mcp_config,
            permission_mode=self.config.permission_mode,
            runtime_state_mode=self.config.runtime_state.mode,
        )


def _create_event_logger(config: AgentConfig) -> AgentEventLogger:
    import logging

    level = getattr(logging, config.logging_config.level)
    path = config.resolve_path(config.logging_config.jsonl_path)
    return AgentEventLogger(
        path=path,
        level=level,
        max_bytes=config.logging_config.max_bytes,
        backup_count=config.logging_config.backup_count,
    )


def _render_message(message: object) -> None:
    """终端只展示文本、工具名称和最终摘要，不展示隐藏思维。"""
    name = type(message).__name__
    if name == "AssistantMessage":
        for block in getattr(message, "content", []):
            block_name = type(block).__name__
            if block_name == "TextBlock":
                console.print(str(getattr(block, "text", "")))
            elif block_name in {"ToolUseBlock", "ServerToolUseBlock"}:
                console.print(f"[dim]Tool: {getattr(block, 'name', '')}[/dim]")
    elif name == "ResultMessage":
        cost = getattr(message, "total_cost_usd", None)
        turns = getattr(message, "num_turns", None)
        duration = getattr(message, "duration_ms", None)
        console.print(
            f"[dim]Agent finished: turns={turns}, duration_ms={duration}, cost={cost}[/dim]"
        )


async def structured_query(
    prompt: str | RenderedPrompt,
    output_model: type[T],
    *,
    config: AgentConfig | None = None,
    config_path: Path | str | None = None,
) -> T:
    """一行完成配置加载、Schema 构建和结构化查询。"""
    if config is not None and config_path is not None:
        raise ValueError("config and config_path are mutually exclusive")
    if config is not None:
        resolved = config
    elif config_path is not None:
        resolved = AgentConfig.from_yaml(config_path)
    elif Path("config/agent.yaml").is_file():
        resolved = AgentConfig.from_yaml()
    else:
        resolved = AgentConfig()
    runner = AgentRunner(
        schema=output_format_schema(output_model),
        config=resolved,
    )
    return await runner.run(prompt, output_model)


def _resolve_prompt(
    prompt: str | RenderedPrompt,
) -> tuple[str, str | dict[str, str] | None, dict[str, Any]]:
    if isinstance(prompt, str):
        return prompt, None, {}
    return (
        prompt.text,
        claude_system_prompt(prompt.instructions),
        {
            "prompt_id": prompt.id,
            "prompt_version": prompt.version,
            "definition_sha256": prompt.definition_sha256,
            "variable_names": list(prompt.variable_names),
            "sensitive_variables": sorted(prompt.sensitive_variables),
        },
    )


def claude_system_prompt(instructions: str) -> dict[str, str]:
    """将 Runtime-neutral instructions 映射为 Claude Code preset。"""
    return {
        "type": "preset",
        "preset": "claude_code",
        "append": instructions,
    }


def sentiment_schema() -> dict[str, Any]:
    """情感分析 Schema。"""
    return output_format_schema(SentimentOutput)


def code_review_schema() -> dict[str, Any]:
    """代码审查 Schema。"""
    return output_format_schema(CodeReviewOutput)
