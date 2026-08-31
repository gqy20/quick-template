"""LangGraph MCP 配置适配层的离线测试。"""

import asyncio
import json

import pytest

pytest.importorskip("langchain_mcp_adapters")

from langchain_core.tools import tool

from {{ package_name }}.langgraph_tools import load_mcp_tools, read_mcp_connections


def test_reads_shared_mcp_config_and_normalizes_transports(tmp_path):
    path = tmp_path / ".mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "local": {
                        "command": "uvx",
                        "args": ["example-server"],
                        "env": {"TOKEN": "${EXAMPLE_TOKEN}"},
                    },
                    "remote": {
                        "type": "http",
                        "url": "https://example.invalid/mcp",
                        "headers": {"Authorization": "Bearer ${EXAMPLE_TOKEN}"},
                    },
                }
            }
        )
    )

    connections = read_mcp_connections(path)

    assert connections["local"] == {
        "command": "uvx",
        "args": ["example-server"],
        "env": {"TOKEN": "${EXAMPLE_TOKEN}"},
        "transport": "stdio",
    }
    assert connections["remote"]["transport"] == "streamable_http"
    assert "type" not in connections["remote"]


@pytest.mark.parametrize(
    ("server", "message"),
    [
        ({"type": "custom", "url": "https://example.invalid"}, "Unsupported"),
        ({"type": "stdio", "args": []}, "requires command"),
        ({"type": "sse"}, "requires url"),
    ],
)
def test_rejects_invalid_mcp_connections(tmp_path, server, message):
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": {"invalid": server}}))

    with pytest.raises(ValueError, match=message):
        read_mcp_connections(path)


@tool
def alpha_tool() -> str:
    """返回 alpha。"""
    return "alpha"


@tool
def beta_tool() -> str:
    """返回 beta。"""
    return "beta"


def test_empty_allowlist_does_not_connect(tmp_path, monkeypatch):
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": {"local": {"command": "server"}}}))

    class UnexpectedClient:
        def __init__(self, *_args, **_kwargs):
            raise AssertionError("MCP client must not start without explicit grants")

    monkeypatch.setattr(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        UnexpectedClient,
    )

    assert asyncio.run(load_mcp_tools(path, allowed_tools=[])) == []


def test_loads_only_explicitly_allowed_mcp_tools(tmp_path, monkeypatch):
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": {"local": {"command": "server"}}}))

    class FakeClient:
        def __init__(self, connections, **options):
            assert connections["local"]["transport"] == "stdio"
            assert options["tool_name_prefix"] is True

        async def get_tools(self):
            return [alpha_tool, beta_tool]

    monkeypatch.setattr(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        FakeClient,
    )

    loaded = asyncio.run(load_mcp_tools(path, allowed_tools=["beta_tool"]))

    assert [item.name for item in loaded] == ["beta_tool"]


def test_rejects_duplicate_mcp_tool_names(tmp_path, monkeypatch):
    path = tmp_path / ".mcp.json"
    path.write_text(json.dumps({"mcpServers": {"local": {"command": "server"}}}))

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def get_tools(self):
            return [alpha_tool, alpha_tool]

    monkeypatch.setattr(
        "langchain_mcp_adapters.client.MultiServerMCPClient",
        FakeClient,
    )

    with pytest.raises(ValueError, match="Duplicate MCP tool names"):
        asyncio.run(load_mcp_tools(path, allowed_tools=["alpha_tool"]))
