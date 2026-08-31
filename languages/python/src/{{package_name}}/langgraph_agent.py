"""使用同一 Prompt 与输出模型的 LangGraph 结构化工作流。"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import (
    Annotated,
    Any,
    Awaitable,
    Callable,
    Literal,
    Protocol,
    Sequence,
    TypedDict,
    TypeVar,
)

import yaml
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphBubbleUp
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.runtime import Runtime
from langgraph.types import (
    Command,
    RetryPolicy,
    TimeoutPolicy,
    TracePolicy,
    omit_payload,
)
from pydantic import BaseModel, Field

from {{ package_name }}.agent_log import AgentEventLogger, redact_text
from {{ package_name }}.langgraph_tools import load_mcp_tools
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

    def bind_tools(self, tools: Sequence[BaseTool]) -> Any: ...


class LangGraphOutputError(RuntimeError):
    """Graph 正常结束但没有产生有效结构化结果。"""


class LangGraphInterruptError(LangGraphOutputError):
    """Graph 已持久化中断点，调用方可使用 thread_id 恢复。"""

    def __init__(self, thread_id: str, interrupts: tuple[Any, ...]) -> None:
        super().__init__(f"LangGraph interrupted on thread {thread_id}")
        self.thread_id = thread_id
        self.interrupts = interrupts


class LangGraphConfig(BaseModel):
    model: str = "claude-sonnet-4-6"
    temperature: float = 0
    max_attempts: int = Field(default=2, ge=1, le=5)
    provider_retry_attempts: int = Field(default=3, ge=1, le=5)
    model_timeout_seconds: float = Field(default=60, gt=0)
    recursion_limit: int = Field(default=24, ge=4)
    max_tool_rounds: int = Field(default=4, ge=1, le=20)
    checkpoint: Literal["memory", "none"] = "memory"
    mcp_config: Path | None = Path(".mcp.json")
    tool_name_prefix: bool = True
    mcp_allowed_tools: list[str] = Field(default_factory=list)
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
    max_tool_rounds: int


class ReviewState(ReviewInput, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    attempts: int
    tool_rounds: int
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
    tool_model: Any | None
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
        "tool_rounds": 0,
        "candidate": None,
        "result": None,
        "validation_errors": [],
        "status": "pending",
    }


async def _invoke_agent(
    state: ReviewState,
    runtime: Runtime[ReviewContext],
) -> dict[str, Any]:
    events = runtime.context.events
    events.emit(
        "node_started", node="invoke_agent", tool_round=state["tool_rounds"] + 1
    )
    if runtime.context.tool_model is None:
        raise RuntimeError("Tool model is not configured")
    response = await runtime.context.tool_model.ainvoke(state["messages"])
    if not isinstance(response, BaseMessage):
        raise TypeError("Tool-calling model must return a BaseMessage")
    tool_calls = getattr(response, "tool_calls", [])
    events.emit(
        "node_finished",
        node="invoke_agent",
        tool_call_count=len(tool_calls),
        tool_names=[call.get("name", "") for call in tool_calls],
        usage=_usage_metadata(response),
    )
    return {"messages": [response], "status": "running"}


def _route_after_agent(
    state: ReviewState,
) -> Literal["tools", "invoke_model", "tool_limit"]:
    if tools_condition(dict(state)) == "__end__":
        return "invoke_model"
    if state.get("tool_rounds", 0) >= state["max_tool_rounds"]:
        return "tool_limit"
    return "tools"


def _record_tool_round(
    state: ReviewState,
    runtime: Runtime[ReviewContext],
) -> dict[str, Any]:
    tool_rounds = state.get("tool_rounds", 0) + 1
    runtime.context.events.emit("tool_round_finished", tool_round=tool_rounds)
    return {"tool_rounds": tool_rounds}


def _tool_limit(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict[str, Any]:
    runtime.context.events.emit(
        "tool_round_limit_reached",
        level=40,
        tool_rounds=state.get("tool_rounds", 0),
    )
    return {"validation_errors": ["tool_round_limit"], "status": "failed"}


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
    """显式工具循环与结构化输出校验工作流。"""

    def __init__(
        self,
        model: StructuredModel,
        tools: Sequence[BaseTool] = (),
        config: LangGraphConfig | None = None,
        event_logger: AgentEventLogger | None = None,
    ) -> None:
        self.model = model
        self.tools = tuple(tools)
        tool_names = [tool.name for tool in self.tools]
        duplicate_names = sorted(
            name for name in set(tool_names) if tool_names.count(name) > 1
        )
        if duplicate_names:
            raise ValueError(f"Duplicate LangGraph tool names: {duplicate_names}")
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
        tools: Sequence[BaseTool] = (),
    ) -> "LangGraphReviewRuntime":
        from langchain_anthropic import ChatAnthropic

        resolved = config or LangGraphConfig.from_yaml()
        model = ChatAnthropic(
            model_name=resolved.model,
            temperature=resolved.temperature,
            timeout=resolved.model_timeout_seconds,
            stop=None,
        )
        return cls(
            model=model,
            tools=tools,
            config=resolved,
            event_logger=event_logger,
        )

    @classmethod
    async def with_anthropic_and_mcp(
        cls,
        config: LangGraphConfig | None = None,
        event_logger: AgentEventLogger | None = None,
        tools: Sequence[BaseTool] = (),
    ) -> "LangGraphReviewRuntime":
        """加载本地工具与 `.mcp.json` 工具后创建 Anthropic Runtime。"""
        resolved = config or LangGraphConfig.from_yaml()
        merged_tools = list(tools)
        if resolved.mcp_config is not None:
            merged_tools.extend(
                await load_mcp_tools(
                    resolved.resolve_path(resolved.mcp_config),
                    allowed_tools=resolved.mcp_allowed_tools,
                    tool_name_prefix=resolved.tool_name_prefix,
                )
            )
        return cls.with_anthropic(
            config=resolved,
            event_logger=event_logger,
            tools=merged_tools,
        )

    def _build_graph(self) -> Any:
        builder = StateGraph(
            ReviewState,
            context_schema=ReviewContext,
            input_schema=ReviewInput,
            output_schema=ReviewOutput,
        )
        builder.add_node("prepare", _prepare)
        if self.tools:
            builder.add_node(
                "invoke_agent",
                _invoke_agent,
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
            builder.add_node(
                "tools",
                ToolNode(
                    self.tools,
                    handle_tool_errors=False,
                    awrap_tool_call=self._audit_tool_call,
                ),
                trace_policy=TracePolicy(
                    process_inputs=omit_payload,
                    process_outputs=omit_payload,
                ),
            )
            builder.add_node("record_tool_round", _record_tool_round)
            builder.add_node("tool_limit", _tool_limit)
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
        if self.tools:
            builder.add_edge("prepare", "invoke_agent")
            builder.add_conditional_edges("invoke_agent", _route_after_agent)
            builder.add_edge("tools", "record_tool_round")
            builder.add_edge("record_tool_round", "invoke_agent")
            builder.add_edge("tool_limit", "fail")
        else:
            builder.add_edge("prepare", "invoke_model")
        builder.add_edge("invoke_model", "validate")
        builder.add_conditional_edges("validate", _route_after_validation)
        builder.add_edge("repair", "invoke_model")
        builder.add_edge("fail", END)
        checkpointer = InMemorySaver() if self.config.checkpoint == "memory" else False
        return builder.compile(checkpointer=checkpointer, name="review-workflow")

    async def _audit_tool_call(
        self,
        request: ToolCallRequest,
        execute: Callable[[ToolCallRequest], Awaitable[Any]],
    ) -> Any:
        call = request.tool_call
        tool_name = str(call.get("name", ""))
        tool_call_id = str(call.get("id", ""))
        args = call.get("args", {})
        started = monotonic()
        self.events.emit(
            "tool_call_started",
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            input_keys=sorted(args) if isinstance(args, dict) else [],
        )
        try:
            result = await execute(request)
        except GraphBubbleUp:
            self.events.emit(
                "tool_call_interrupted",
                tool_name=tool_name,
                tool_call_id=tool_call_id,
            )
            raise
        except Exception as error:
            self.events.emit(
                "tool_call_failed",
                level=40,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                error_type=type(error).__name__,
                duration_ms=round((monotonic() - started) * 1000),
            )
            return ToolMessage(
                content=f"Tool execution failed: {type(error).__name__}",
                name=tool_name,
                tool_call_id=tool_call_id,
                status="error",
            )
        self.events.emit(
            "tool_call_finished",
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            status=getattr(result, "status", "success"),
            duration_ms=round((monotonic() - started) * 1000),
        )
        return result

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
        return await self._invoke_graph(
            _graph_input(
                prompt,
                self.config.max_attempts,
                self.config.max_tool_rounds,
            ),
            output_model,
            thread,
        )

    async def resume(
        self,
        thread_id: str,
        resume_value: Any,
        output_model: type[T],
    ) -> T:
        """使用 checkpoint thread_id 恢复一次原生 LangGraph interrupt。"""
        if self.config.checkpoint == "none":
            raise LangGraphOutputError("Cannot resume when checkpoint is disabled")
        run_id = self.events.start_run()
        self.events.emit(
            "graph_resumed",
            run_id=run_id,
            thread_id=thread_id,
            output_model=output_model.__name__,
        )
        return await self._invoke_graph(
            Command(resume=resume_value),
            output_model,
            thread_id,
        )

    async def _invoke_graph(
        self,
        graph_input: ReviewInput | Command,
        output_model: type[T],
        thread: str,
    ) -> T:
        tool_model = self.model.bind_tools(self.tools) if self.tools else None
        context = ReviewContext(self.model, tool_model, output_model, self.events)
        try:
            graph_result = await self.graph.ainvoke(
                graph_input,
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
            raise LangGraphInterruptError(thread, tuple(graph_result.interrupts))
        value = graph_result.value
        if value["status"] != "valid" or value["result"] is None:
            self.events.emit("graph_failed", errors=value["validation_errors"])
            if "tool_round_limit" in value["validation_errors"]:
                raise LangGraphOutputError(
                    f"LangGraph tool loop exceeded {self.config.max_tool_rounds} rounds"
                )
            raise LangGraphOutputError(
                f"LangGraph output validation failed after {self.config.max_attempts} attempts"
            )
        result = output_model.model_validate(value["result"])
        self.events.emit("graph_finished", status="valid", thread_id=thread)
        return result

    @property
    def node_names(self) -> frozenset[str]:
        return frozenset(self.graph.get_graph().nodes)


def _graph_input(
    prompt: RenderedPrompt,
    max_attempts: int,
    max_tool_rounds: int,
) -> ReviewInput:
    return {
        "prompt_id": prompt.id,
        "prompt_version": prompt.version,
        "definition_sha256": prompt.definition_sha256,
        "instructions": prompt.instructions,
        "prompt_text": prompt.text,
        "max_attempts": max_attempts,
        "max_tool_rounds": max_tool_rounds,
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
