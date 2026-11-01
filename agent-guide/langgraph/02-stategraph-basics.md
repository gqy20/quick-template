# 写自己的 StateGraph

LangGraph 的核心概念是三个东西：**State**（可 checkpoint 的数据）、
**Context**（不进 checkpoint 的依赖）、**节点**（函数）。

## 三个类型各管什么

```python
class ReviewState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    attempts: int
    result: dict[str, Any] | None
    validation_errors: Annotated[list[str], operator.add]
    status: Literal["pending", "running", "valid", "failed"]


@dataclass(frozen=True)
class ReviewContext:
    model: StructuredModel
    tool_model: Any
    output_model: type
    events: AgentEventLogger
```

| | State | Context |
|---|---|---|
| 会进 checkpoint | 是 | 否 |
| 需要可序列化 | 是 | 否 |
| 典型内容 | 消息、计数、中间结果 | model、logger、Schema |

**判据：能序列化且需要恢复的放 State，其余放 Context。** 把 model 放进
State 会让 checkpoint 失败 —— 它不是可序列化的数据。

## 累加 vs 覆盖

默认节点返回的字段**覆盖**原值。需要累加时用 `Annotated`：

```python
messages: Annotated[list[BaseMessage], add_messages]  # 追加消息
validation_errors: Annotated[list[str], operator.add]  # 追加错误
```

不用 `Annotated` 的字段，节点返回什么就是什么。

## 定义输入输出

```python
builder = StateGraph(
    ReviewState,
    context_schema=ReviewContext,
    input_schema=ReviewInput,  # 只暴露给调用方的字段
    output_schema=ReviewOutput,  # 只返回给调用方的字段
)
```

`input_schema` 和 `output_schema` 让内部 State 可以比外部契约大很多 ——
调用方只看到该看的字段。

## 节点是普通函数

```python
def _prepare(state: ReviewState, runtime: Runtime[ReviewContext]) -> dict:
    ctx = runtime.context
    return {
        "max_attempts": ctx.max_attempts,
        "status": "running",
    }
```

签名固定：`(state, runtime) -> dict`，返回要更新的字段。第二个参数是
`Runtime[ReviewContext]`，通过 `runtime.context` 拿到 Context。

异步节点同样写法，用 `async def`。

## 条件边

```python
def _route_after_validation(state: ReviewState, runtime) -> str:
    if state.get("result") is not None:
        return "done"
    if state.get("attempts", 0) >= runtime.context.max_attempts:
        return "fail"
    return "repair"


builder.add_conditional_edges("validate", _route_after_validation)
```

返回值是**节点名**，不是边名。路由函数只能读 State 和 Context，不能有
副作用。

## 编译

```python
checkpointer = InMemorySaver() if config.checkpoint == "memory" else False
graph = builder.compile(checkpointer=checkpointer, name="review-workflow")
```

`checkpointer=False` 时不能 `interrupt()` 恢复 —— 中断后状态无处保存。
需要人工介入的流程必须用 `InMemorySaver`（或持久实现）。

`InMemorySaver` 只在进程内存里，进程重启就没了。跨进程恢复要换成
`SqliteSaver`、`PostgresSaver` 等持久实现。

## 重试与超时

节点可以带策略：

```python
builder.add_node(
    "invoke_model",
    _invoke_model,
    retry_policy=RetryPolicy(max_attempts=config.provider_retry_attempts),
    timeout=TimeoutPolicy(run_timeout=config.model_timeout_seconds),
)
```

`retry_policy` 管**异常重试**，和 `max_attempts`（校验失败后的修复轮次）
是两回事：

| 配置 | 管什么 | 触发条件 |
|---|---|---|
| `provider_retry_attempts` | 网络/供应商错误 | 抛异常 |
| `max_attempts` | 输出不符合 Schema | 校验失败，不抛异常 |

两层重试叠加时，实际调用次数是乘积。控制住两层，别让它们互相放大。

## 常见错误

- **把 model 放进 State。** checkpoint 序列化失败。
- **忘记 `Annotated`。** 期望追加的字段被覆盖。
- **路由函数返回边名。** 要返回节点名。
- **`checkpoint: none` 却用 `interrupt()`。** 恢复时找不到状态。
- **混淆两层重试。** 供应商重试和 Schema 修复重试语义不同。
