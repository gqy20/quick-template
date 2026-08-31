"""Claude Agent SDK 的结构化运行日志。

默认只记录元数据，不记录 prompt、模型正文、工具输入值或工具结果正文。
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

_SECRET_PATTERNS = (
    (re.compile(r"(?i)(authorization:\s*bearer\s+)\S+"), r"\1[REDACTED]"),
    (
        re.compile(r"(?i)((?:api[_-]?key|token|password|secret)\s*[=:]\s*)\S+"),
        r"\1[REDACTED]",
    ),
    (re.compile(r"\bsk-[A-Za-z0-9_-]+\b"), "[REDACTED]"),
)


def redact_text(value: str) -> str:
    """脱敏常见 Token、密钥和认证头。"""
    redacted = value
    for pattern, replacement in _SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


class _JsonFormatter(logging.Formatter):
    """将标准 logging record 输出为单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            **getattr(record, "agent_fields", {}),
        }
        return json.dumps(payload, ensure_ascii=False, default=str)


class AgentEventLogger:
    """记录 Agent 生命周期、能力加载、工具调用和终止指标。"""

    def __init__(
        self,
        path: Path | str = "logs/agent.jsonl",
        level: int = logging.INFO,
        run_id: str | None = None,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or str(uuid4())
        self.session_id: str | None = None
        self._tool_started: dict[str, float] = {}
        self._logger = self._create_logger(level, max_bytes, backup_count)

    def _create_logger(
        self,
        level: int,
        max_bytes: int,
        backup_count: int,
    ) -> logging.Logger:
        name = f"{{package_name}}.agent.{hash(self.path.resolve())}"
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        if not logger.handlers:
            handler = RotatingFileHandler(
                self.path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(_JsonFormatter())
            logger.addHandler(handler)
        return logger

    def emit(self, event: str, *, level: int = logging.INFO, **fields: Any) -> None:
        """写入结构化事件。"""
        payload = {
            "event": event,
            "run_id": self.run_id,
            "session_id": self.session_id,
            **fields,
        }
        self._logger.log(level, event, extra={"agent_fields": payload})

    def run_started(
        self,
        prompt: str,
        output_model: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """记录任务开始，只保存 prompt 长度与摘要。"""
        self.emit(
            "run_started",
            prompt_chars=len(prompt),
            prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            output_model=output_model,
            **(metadata or {}),
        )

    def capture_stderr(self, message: str) -> None:
        """接收 SDK stderr 回调并脱敏。"""
        level = logging.WARNING if "error" in message.lower() else logging.DEBUG
        self.emit(
            "sdk_stderr",
            level=level,
            message=redact_text(message)[:2000],
        )

    def observe(self, message: object) -> None:
        """从 SDK 原生消息对象采集安全元数据。"""
        session_id = getattr(message, "session_id", None)
        if isinstance(session_id, str):
            self.session_id = session_id

        name = type(message).__name__
        if (
            name == "SystemMessage"
            or name.endswith("Message")
            and hasattr(message, "subtype")
        ):
            self._observe_system(message)
        if name == "AssistantMessage":
            self._observe_assistant(message)
        elif name == "UserMessage":
            self._observe_user(message)
        elif name == "ResultMessage":
            self._observe_result(message)
        elif name == "RateLimitEvent":
            self._observe_rate_limit(message)

    def _observe_system(self, message: object) -> None:
        subtype = str(getattr(message, "subtype", "unknown"))
        data = getattr(message, "data", {})
        if subtype == "init" and isinstance(data, dict):
            self.emit(
                "sdk_initialized",
                tools=_names(data.get("tools")),
                mcp_servers=_names(data.get("mcp_servers")),
                skills=_names(data.get("skills")),
                plugins=_names(data.get("plugins")),
                slash_commands=_names(data.get("slash_commands")),
            )
        elif type(message).__name__ == "HookEventMessage":
            self.emit(
                "hook_event",
                subtype=subtype,
                hook_event=str(getattr(message, "hook_event_name", "")),
            )
        elif subtype != "unknown":
            safe_fields = _select_fields(
                data,
                {"task_id", "status", "duration_ms", "total_tokens", "tool_uses"},
            )
            self.emit("system_event", subtype=subtype, **safe_fields)

    def _observe_assistant(self, message: object) -> None:
        content = getattr(message, "content", [])
        self.emit(
            "assistant_message",
            model=str(getattr(message, "model", "")),
            stop_reason=getattr(message, "stop_reason", None),
            block_count=len(content) if isinstance(content, list) else 0,
            parent_tool_use_id=getattr(message, "parent_tool_use_id", None),
            usage=_numeric_mapping(getattr(message, "usage", None)),
        )
        if isinstance(content, list):
            for block in content:
                self.observe_block(block)

    def _observe_user(self, message: object) -> None:
        content = getattr(message, "content", [])
        if isinstance(content, list):
            for block in content:
                self.observe_block(block)

    def observe_block(self, block: object) -> None:
        """记录工具调用或结果，不持久化正文和值。"""
        name = type(block).__name__
        if name in {"ToolUseBlock", "ServerToolUseBlock"}:
            tool_input = getattr(block, "input", {})
            tool_use_id = str(getattr(block, "id", ""))
            if tool_use_id:
                self._tool_started[tool_use_id] = monotonic()
            self.emit(
                "tool_use",
                tool_name=str(getattr(block, "name", "")),
                tool_use_id=tool_use_id,
                input_keys=sorted(tool_input) if isinstance(tool_input, dict) else [],
            )
        elif name in {"ToolResultBlock", "ServerToolResultBlock"}:
            content = getattr(block, "content", None)
            tool_use_id = str(getattr(block, "tool_use_id", ""))
            started = self._tool_started.pop(tool_use_id, None)
            self.emit(
                "tool_result",
                tool_use_id=tool_use_id,
                is_error=bool(getattr(block, "is_error", False)),
                content_chars=len(str(content)) if content is not None else 0,
                duration_ms=round((monotonic() - started) * 1000) if started else None,
            )

    def _observe_result(self, message: object) -> None:
        self.emit(
            "run_finished",
            subtype=str(getattr(message, "subtype", "")),
            is_error=bool(getattr(message, "is_error", False)),
            terminal_reason=getattr(message, "terminal_reason", None),
            stop_reason=getattr(message, "stop_reason", None),
            duration_ms=getattr(message, "duration_ms", None),
            duration_api_ms=getattr(message, "duration_api_ms", None),
            num_turns=getattr(message, "num_turns", None),
            total_cost_usd=getattr(message, "total_cost_usd", None),
            api_error_status=getattr(message, "api_error_status", None),
            permission_denial_count=len(
                getattr(message, "permission_denials", None) or []
            ),
            usage=_numeric_mapping(getattr(message, "usage", None)),
        )

    def _observe_rate_limit(self, message: object) -> None:
        info = getattr(message, "rate_limit_info", None)
        fields = vars(info) if hasattr(info, "__dict__") else {}
        self.emit("rate_limit", level=logging.WARNING, **_safe_scalar_mapping(fields))


def _names(value: object) -> list[str]:
    if isinstance(value, dict):
        return sorted(str(key) for key in value)
    if isinstance(value, list):
        names = []
        for item in value:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
        return sorted(names)
    return []


def _numeric_mapping(value: object) -> dict[str, int | float]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): item
        for key, item in value.items()
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    }


def _safe_scalar_mapping(value: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): item
        for key, item in value.items()
        if item is None or isinstance(item, (str, int, float, bool))
    }


def _select_fields(value: object, allowed: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return _safe_scalar_mapping(
        {str(key): item for key, item in value.items() if key in allowed}
    )
