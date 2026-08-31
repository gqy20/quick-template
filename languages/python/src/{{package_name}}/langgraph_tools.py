"""LangGraph 的 MCP 配置适配层。

这里只转换 `.mcp.json` 的连接配置；协议、会话和工具 Schema 由
`langchain-mcp-adapters` 原生实现负责。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool

_TRANSPORT_ALIASES = {
    "http": "streamable_http",
    "streamable-http": "streamable_http",
    "streamable_http": "streamable_http",
    "sse": "sse",
    "stdio": "stdio",
    "websocket": "websocket",
}


def read_mcp_connections(path: Path | str) -> dict[str, dict[str, Any]]:
    """读取 Claude Code 形状的 `.mcp.json` 并转换为 Adapter 连接。"""
    config_path = Path(path)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("mcpServers"), dict):
        raise ValueError("MCP configuration must contain an mcpServers mapping")

    connections: dict[str, dict[str, Any]] = {}
    for name, raw in data["mcpServers"].items():
        if not isinstance(name, str) or not name or not isinstance(raw, dict):
            raise ValueError("Each MCP server must have a non-empty name and mapping")
        connection = dict(raw)
        declared = connection.pop("transport", connection.pop("type", None))
        if declared is None:
            declared = "stdio" if "command" in connection else "http"
        transport = _TRANSPORT_ALIASES.get(str(declared))
        if transport is None:
            raise ValueError(
                f"Unsupported MCP transport for server {name!r}: {declared!r}"
            )
        connection["transport"] = transport
        if transport == "stdio" and not isinstance(connection.get("command"), str):
            raise ValueError(f"MCP stdio server {name!r} requires command")
        if transport != "stdio" and not isinstance(connection.get("url"), str):
            raise ValueError(f"MCP network server {name!r} requires url")
        connections[name] = connection
    return connections


async def load_mcp_tools(
    path: Path | str,
    *,
    allowed_tools: list[str],
    tool_name_prefix: bool = True,
) -> list[BaseTool]:
    """通过官方 Adapter 加载并按最终工具名授权无状态 MCP 工具。"""
    from langchain_mcp_adapters.client import MultiServerMCPClient

    connections = read_mcp_connections(path)
    if not connections or not allowed_tools:
        return []
    client = MultiServerMCPClient(
        connections,  # type: ignore[arg-type]
        tool_name_prefix=tool_name_prefix,
        handle_tool_errors=True,
    )
    loaded = await client.get_tools()
    loaded_names = [tool.name for tool in loaded]
    duplicate_names = sorted(
        name for name in set(loaded_names) if loaded_names.count(name) > 1
    )
    if duplicate_names:
        raise ValueError(f"Duplicate MCP tool names: {duplicate_names}")
    loaded_by_name = {tool.name: tool for tool in loaded}
    missing = sorted(set(allowed_tools) - loaded_by_name.keys())
    if missing:
        raise ValueError(f"Allowed MCP tools were not found: {missing}")
    return [loaded_by_name[name] for name in allowed_tools]
