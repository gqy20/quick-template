"""LangGraph Runtime 的离线测试。"""

import asyncio
import json

import pytest

pytest.importorskip("langgraph")

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.types import interrupt

from {{ package_name }}.agent_log import AgentEventLogger
from {{ package_name }}.agent_models import CodeReviewOutput
from {{ package_name }}.langgraph_agent import (
    LangGraphConfig,
    LangGraphInterruptError,
    LangGraphOutputError,
    LangGraphReviewRuntime,
)
from {{ package_name }}.prompt import PromptRegistry


class FakeStructuredRunnable:
    def __init__(self, outputs):
        self.outputs = outputs

    async def ainvoke(self, _messages):
        return self.outputs.pop(0)


class FakeStructuredModel:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0

    def with_structured_output(self, _schema, *, include_raw):
        assert include_raw is True
        self.calls += 1
        return FakeStructuredRunnable(self.outputs)


class FakeToolCallingModel(FakeStructuredModel):
    def __init__(self, outputs, agent_outputs):
        super().__init__(outputs)
        self.agent_outputs = agent_outputs
        self.bound_tool_names = []
        self.agent_messages = []

    def bind_tools(self, tools):
        self.bound_tool_names = [item.name for item in tools]
        return self

    async def ainvoke(self, messages):
        self.agent_messages.append(messages)
        return self.agent_outputs.pop(0)


def success_response(score=9):
    return {
        "raw": AIMessage(
            content="",
            usage_metadata={
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            },
        ),
        "parsed": CodeReviewOutput(score=score, overall="清晰", issues=[]),
        "parsing_error": None,
    }


def rendered_prompt():
    return PromptRegistry("config/prompts").render(
        "code-review",
        language="Python",
        code="print('secret')",
    )


def create_runtime(tmp_path, outputs, max_attempts=2, tools=(), model=None, **config):
    events = AgentEventLogger(
        path=tmp_path / "langgraph.jsonl",
        runtime="langgraph",
    )
    model = model or FakeStructuredModel(outputs)
    runtime = LangGraphReviewRuntime(
        model=model,
        tools=tools,
        config=LangGraphConfig(max_attempts=max_attempts, **config),
        event_logger=events,
    )
    return runtime, model, events.path


def test_graph_topology_matches_structured_workflow(tmp_path):
    runtime, _, _ = create_runtime(tmp_path, [success_response()])

    assert runtime.node_names == {
        "__start__",
        "prepare",
        "invoke_model",
        "validate",
        "repair",
        "fail",
        "__end__",
    }


def test_duplicate_tool_names_are_rejected(tmp_path):
    events = AgentEventLogger(
        path=tmp_path / "langgraph.jsonl",
        runtime="langgraph",
    )

    with pytest.raises(ValueError, match="Duplicate LangGraph tool names"):
        LangGraphReviewRuntime(
            model=FakeStructuredModel([]),
            tools=[lookup_context, lookup_context],
            event_logger=events,
        )


def test_successful_run_returns_shared_output_and_safe_logs(tmp_path):
    runtime, model, log_path = create_runtime(tmp_path, [success_response()])

    result = asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))

    assert result.score == 9
    assert model.calls == 1
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert records[0]["runtime"] == "langgraph"
    assert records[0]["prompt_id"] == "code-review"
    assert any(record["event"] == "graph_finished" for record in records)
    assert "print('secret')" not in log_path.read_text()


def test_validation_failure_retries_then_succeeds(tmp_path):
    outputs = [
        {
            "raw": AIMessage(content=""),
            "parsed": None,
            "parsing_error": ValueError("invalid"),
        },
        success_response(score=8),
    ]
    runtime, model, log_path = create_runtime(tmp_path, outputs)

    result = asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))

    assert result.score == 8
    assert model.calls == 2
    events = [json.loads(line)["event"] for line in log_path.read_text().splitlines()]
    assert "validation_failed" in events
    assert "retry_scheduled" in events


def test_exhausted_validation_raises_stable_error(tmp_path):
    invalid = {
        "raw": AIMessage(content=""),
        "parsed": None,
        "parsing_error": ValueError("invalid"),
    }
    runtime, _, _ = create_runtime(tmp_path, [invalid], max_attempts=1)

    with pytest.raises(LangGraphOutputError, match="after 1 attempts"):
        asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))


def test_runtime_config_loads_without_model_call():
    config = LangGraphConfig.from_yaml()

    assert config.model == "claude-sonnet-4-6"
    assert config.checkpoint == "memory"
    assert config.recursion_limit == 24
    assert config.max_tool_rounds == 4
    assert config.mcp_config.name == ".mcp.json"
    assert config.tool_name_prefix is True
    assert config.mcp_allowed_tools == []


@tool
async def lookup_context(query: str) -> str:
    """查找审查上下文。"""
    return f"context-for:{query}"


@tool
async def failing_lookup(query: str) -> str:
    """模拟失败的上下文查询。"""
    raise ValueError(f"private failure: {query}")


@tool
async def approval_tool(action: str) -> str:
    """请求人工批准动作。"""
    decision = interrupt({"action": action})
    return f"decision:{decision}"


def tool_call_message(
    name="lookup_context",
    query="private-query",
    call_id="call-1",
    arg_name="query",
):
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": name,
                "args": {arg_name: query},
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def test_tool_loop_uses_native_tool_node_then_structured_output(tmp_path):
    model = FakeToolCallingModel(
        [success_response()],
        [tool_call_message(), AIMessage(content="context collected")],
    )
    runtime, _, log_path = create_runtime(
        tmp_path,
        [],
        tools=[lookup_context],
        model=model,
    )

    result = asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))

    assert result.score == 9
    assert model.bound_tool_names == ["lookup_context"]
    assert len(model.agent_messages) == 2
    assert any(isinstance(message, ToolMessage) for message in model.agent_messages[1])
    assert {
        "invoke_agent",
        "tools",
        "record_tool_round",
        "tool_limit",
    }.issubset(runtime.node_names)
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert any(record["event"] == "tool_call_finished" for record in records)
    log_text = log_path.read_text()
    assert "private-query" not in log_text
    assert "context-for" not in log_text


def test_tool_failure_is_safe_message_and_audited(tmp_path):
    model = FakeToolCallingModel(
        [success_response()],
        [
            tool_call_message(name="failing_lookup", query="secret-value"),
            AIMessage(content="continue without tool"),
        ],
    )
    runtime, _, log_path = create_runtime(
        tmp_path,
        [],
        tools=[failing_lookup],
        model=model,
    )

    asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))

    tool_result = next(
        message
        for message in model.agent_messages[1]
        if isinstance(message, ToolMessage)
    )
    assert tool_result.status == "error"
    assert tool_result.content == "Tool execution failed: ValueError"
    log_text = log_path.read_text()
    assert '"event": "tool_call_failed"' in log_text
    assert "secret-value" not in log_text
    assert "private failure" not in log_text


def test_tool_round_limit_stops_repeated_calls(tmp_path):
    model = FakeToolCallingModel(
        [],
        [
            tool_call_message(call_id="call-1"),
            tool_call_message(call_id="call-2"),
        ],
    )
    runtime, _, log_path = create_runtime(
        tmp_path,
        [],
        tools=[lookup_context],
        model=model,
        max_tool_rounds=1,
    )

    with pytest.raises(LangGraphOutputError, match="exceeded 1 rounds"):
        asyncio.run(runtime.run(rendered_prompt(), CodeReviewOutput))

    assert '"event": "tool_round_limit_reached"' in log_path.read_text()


def test_interrupted_tool_can_resume_from_checkpoint(tmp_path):
    model = FakeToolCallingModel(
        [success_response()],
        [
            tool_call_message(
                name="approval_tool",
                query="delete-private-record",
                arg_name="action",
            ),
            AIMessage(content="approved action completed"),
        ],
    )
    runtime, _, log_path = create_runtime(
        tmp_path,
        [],
        tools=[approval_tool],
        model=model,
    )

    with pytest.raises(LangGraphInterruptError) as caught:
        asyncio.run(
            runtime.run(
                rendered_prompt(),
                CodeReviewOutput,
                thread_id="approval-thread",
            )
        )

    assert caught.value.thread_id == "approval-thread"
    assert len(caught.value.interrupts) == 1

    result = asyncio.run(
        runtime.resume(
            thread_id=caught.value.thread_id,
            resume_value="approved-private-value",
            output_model=CodeReviewOutput,
        )
    )

    assert result.score == 9
    log_text = log_path.read_text()
    assert '"event": "tool_call_interrupted"' in log_text
    assert '"event": "graph_resumed"' in log_text
    assert "delete-private-record" not in log_text
    assert "approved-private-value" not in log_text


def test_resume_requires_checkpoint(tmp_path):
    runtime, _, _ = create_runtime(
        tmp_path,
        [],
        checkpoint="none",
    )

    with pytest.raises(LangGraphOutputError, match="checkpoint is disabled"):
        asyncio.run(
            runtime.resume(
                thread_id="missing-checkpoint",
                resume_value="approved",
                output_model=CodeReviewOutput,
            )
        )
