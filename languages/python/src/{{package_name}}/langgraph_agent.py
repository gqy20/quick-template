"""使用同一 Prompt 与输出模型的 LangGraph 结构化工作流。"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any, Literal, Protocol, TypedDict, TypeVar

import yaml
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.runtime import Runtime
from langgraph.types import (
    RetryPolicy,
    TimeoutPolicy,
    TracePolicy,
    omit_payload,
)
from pydantic import BaseModel, Field

from {{ package_name }}.agent_log import AgentEventLogger, redact_text
from {{ package_name }}.prompt import RenderedPrompt

T = TypeVar("T", bound=BaseModel)


class StructuredModel(Protocol):
    """LangChain chat model 的最小结构化输出能力。"""

    def with_structured_output(
        self,
        schema: type[BaseModel],
        *,
        include_raw: bool,
    ) -> Any: ...


class LangGraphOutputError(RuntimeError):
    """Graph 正常结束但没有产生有效结构化结果。"""


class LangGraphConfig(BaseModel):
    model: str = "claude-sonnet-4-6"
    temperature: float = 0
    max_attempts: int = Field(default=2, ge=1, le=5)
    provider_retry_attempts: int = Field(default=3, ge=1, le=5)
    model_timeout_seconds: float = Field(default=60, gt=0)
    recursion_limit: int = Field(default=12, ge=4)
    checkpoint: Literal["memory", "none"] = "memory"
    jsonl_path: Path = Path("logs/agent/langgraph.jsonl")
    project_root: Path = Field(default_factory=Path.cwd, exclude=True)

    @classmethod
    def from_yaml(
        cls,
        path: Path | str = "config/runtimes/langgraph.yaml",
    ) -> "LangGraphConfig":
        config_path = Path(path).resolve()
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("LangGraph configuration must be a mapping")
        data.setdefault("project_root", config_path.parents[2])
        return cls.model_validate(data)

    def resolve_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.project_root / path


class ReviewInput(TypedDict):
    prompt_id: str
    prompt_version: str
    definition_sha256: str
    instructions: str
    prompt_text: str
    max_attempts: int


class ReviewState(ReviewInput, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    attempts: int
    candidate: dict[str, Any] | None
    result: dict[str, Any] | None
    validation_errors: Annotated[list[str], operator.add]
    status: Literal["pending", "running", "valid", "failed"]


class ReviewOutput(TypedDict):
    result: dict[str, Any] | None
    validation_errors: list[str]
    status: Literal["valid", "failed"]


@dataclass(frozen=True)
class ReviewContext:
    model: StructuredModel
    output_model: type[BaseModel]
    events: AgentEventLogger


def _prepare(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict[str, Any]:
    runtime.context.events.emit("node_started", node="prepare")
    messages = [
        SystemMessage(content=state["instructions"]),
        HumanMessage(content=state["prompt_text"]),
    ]
    runtime.context.events.emit("node_finished", node="prepare")
    return {
        "messages": messages,
        "attempts": 0,
        "candidate": None,
        "result": None,
        "validation_errors": [],
        "status": "pending",
    }


async def _invoke_model(
    state: ReviewState,
    runtime: Runtime[ReviewContext],
) -> dict[str, Any]:
    events = runtime.context.events
    events.emit("node_started", node="invoke_model", attempt=state["attempts"] + 1)
    runnable = runtime.context.model.with_structured_output(
        runtime.context.output_model,
        include_raw=True,
    )
    response = await runnable.ainvoke(state["messages"])
    parsed = response.get("parsed")
    raw = response.get("raw")
    parsing_error = response.get("parsing_error")
    candidate = parsed.model_dump() if isinstance(parsed, BaseModel) else parsed
    error_name = type(parsing_error).__name__ if parsing_error else None
    events.emit(
        "node_finished",
        node="invoke_model",
        parsed=candidate is not None,
        error_type=error_name,
        usage=_usage_metadata(raw),
    )
    return {
        "messages": [raw] if isinstance(raw, BaseMessage) else [],
        "attempts": state["attempts"] + 1,
        "candidate": candidate,
        "validation_errors": [error_name] if error_name else [],
        "status": "running",
    }


def _validate(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict[str, Any]:
    events = runtime.context.events
    events.emit("node_started", node="validate")
    candidate = state.get("candidate")
    if candidate is None:
        events.emit("validation_failed", reason="missing_candidate")
        return {"status": "running"}
    try:
        result = runtime.context.output_model.model_validate(candidate)
    except Exception as error:
        name = type(error).__name__
        events.emit("validation_failed", reason=name)
        return {"validation_errors": [name], "status": "running"}
    events.emit("node_finished", node="validate", valid=True)
    return {"result": result.model_dump(), "status": "valid"}


def _route_after_validation(
    state: ReviewState,
) -> Literal["repair", "fail", "__end__"]:
    if state.get("status") == "valid":
        return "__end__"
    if state.get("attempts", 0) < state["max_attempts"]:
        return "repair"
    return "fail"


def _repair(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict[str, Any]:
    runtime.context.events.emit(
        "retry_scheduled",
        attempt=state.get("attempts", 0) + 1,
    )
    feedback = HumanMessage(
        content=(
            "上一次输出未通过结构化 Schema。"
            "请修正字段、类型和必填项，只返回符合要求的结果。"
        )
    )
    return {"messages": [feedback], "candidate": None}


def _fail(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict[str, Any]:
    runtime.context.events.emit(
        "node_finished",
        node="fail",
        attempts=state.get("attempts", 0),
    )
    return {"status": "failed", "result": None}


class LangGraphReviewRuntime:
    """显式 prepare → model → validate → repair/fail 工作流。"""

    def __init__(
        self,
        model: StructuredModel,
        config: LangGraphConfig | None = None,
        event_logger: AgentEventLogger | None = None,
    ) -> None:
        self.model = model
        self.config = config or LangGraphConfig()
        self.events = event_logger or AgentEventLogger(
            path=self.config.resolve_path(self.config.jsonl_path),
            runtime="langgraph",
        )
        self.graph = self._build_graph()

    @classmethod
    def with_anthropic(
        cls,
        config: LangGraphConfig | None = None,
        event_logger: AgentEventLogger | None = None,
    ) -> "LangGraphReviewRuntime":
        from langchain_anthropic import ChatAnthropic

        resolved = config or LangGraphConfig.from_yaml()
        model = ChatAnthropic(
            model_name=resolved.model,
            temperature=resolved.temperature,
            timeout=resolved.model_timeout_seconds,
            stop=None,
        )
        return cls(model=model, config=resolved, event_logger=event_logger)

    def _build_graph(self) -> Any:
        builder = StateGraph(
            ReviewState,
            context_schema=ReviewContext,
            input_schema=ReviewInput,
            output_schema=ReviewOutput,
        )
        builder.add_node("prepare", _prepare)
        builder.add_node(
            "invoke_model",
            _invoke_model,
            retry_policy=RetryPolicy(
                max_attempts=self.config.provider_retry_attempts,
            ),
            timeout=TimeoutPolicy(
                run_timeout=self.config.model_timeout_seconds,
            ),
            trace_policy=TracePolicy(
                process_inputs=omit_payload,
                process_outputs=omit_payload,
            ),
        )
        builder.add_node("validate", _validate)
        builder.add_node("repair", _repair)
        builder.add_node("fail", _fail)
        builder.add_edge(START, "prepare")
        builder.add_edge("prepare", "invoke_model")
        builder.add_edge("invoke_model", "validate")
        builder.add_conditional_edges("validate", _route_after_validation)
        builder.add_edge("repair", "invoke_model")
        builder.add_edge("fail", END)
        checkpointer = InMemorySaver() if self.config.checkpoint == "memory" else False
        return builder.compile(checkpointer=checkpointer, name="review-workflow")

    async def run(
        self,
        prompt: RenderedPrompt,
        output_model: type[T],
        thread_id: str | None = None,
    ) -> T:
        run_id = self.events.start_run()
        thread = thread_id or run_id
        self.events.run_started(
            prompt=prompt.text,
            output_model=output_model.__name__,
            metadata={
                "prompt_id": prompt.id,
                "prompt_version": prompt.version,
                "definition_sha256": prompt.definition_sha256,
                "variable_names": list(prompt.variable_names),
                "sensitive_variables": sorted(prompt.sensitive_variables),
            },
        )
        self.events.emit("graph_started", run_id=run_id, thread_id=thread)
        context = ReviewContext(self.model, output_model, self.events)
        try:
            graph_result = await self.graph.ainvoke(
                _graph_input(prompt, self.config.max_attempts),
                config={
                    "configurable": {"thread_id": thread},
                    "recursion_limit": self.config.recursion_limit,
                },
                context=context,
                version="v2",
            )
        except Exception as error:
            self.events.emit(
                "graph_failed",
                level=40,
                error_type=type(error).__name__,
                error=redact_text(str(error))[:1000],
            )
            raise
        if graph_result.interrupts:
            self.events.emit("graph_interrupted", count=len(graph_result.interrupts))
            raise LangGraphOutputError("Graph interrupted before producing a result")
        value = graph_result.value
        if value["status"] != "valid" or value["result"] is None:
            self.events.emit("graph_failed", errors=value["validation_errors"])
            raise LangGraphOutputError(
                f"LangGraph output validation failed after {self.config.max_attempts} attempts"
            )
        result = output_model.model_validate(value["result"])
        self.events.emit("graph_finished", status="valid", thread_id=thread)
        return result

    @property
    def node_names(self) -> frozenset[str]:
        return frozenset(self.graph.get_graph().nodes)


def _graph_input(prompt: RenderedPrompt, max_attempts: int) -> ReviewInput:
    return {
        "prompt_id": prompt.id,
        "prompt_version": prompt.version,
        "definition_sha256": prompt.definition_sha256,
        "instructions": prompt.instructions,
        "prompt_text": prompt.text,
        "max_attempts": max_attempts,
    }


def _usage_metadata(message: object) -> dict[str, int | float]:
    usage = getattr(message, "usage_metadata", None)
    if not isinstance(usage, dict):
        return {}
    return {
        str(key): value
        for key, value in usage.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }
