"""LangGraph Runtime 的离线测试。"""

import asyncio
import json

import pytest

pytest.importorskip("langgraph")

from langchain_core.messages import AIMessage

from {{ package_name }}.agent_log import AgentEventLogger
from {{ package_name }}.agent_models import CodeReviewOutput
from {{ package_name }}.langgraph_agent import (
    LangGraphConfig,
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


def create_runtime(tmp_path, outputs, max_attempts=2):
    events = AgentEventLogger(
        path=tmp_path / "langgraph.jsonl",
        runtime="langgraph",
    )
    model = FakeStructuredModel(outputs)
    runtime = LangGraphReviewRuntime(
        model=model,
        config=LangGraphConfig(max_attempts=max_attempts),
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
    assert config.recursion_limit == 12
