# 中断与恢复

LangGraph 的 `interrupt()` 让图在中途暂停等待外部输入，`Command(resume=...)`
从检查点继续。这是人工审批、确认危险操作的基础。

## 前提：需要 checkpointer

```yaml
checkpoint: memory
```

`checkpoint: none` 时状态无处保存，`resume()` 直接抛
`LangGraphOutputError("Cannot resume when checkpoint is disabled")`。

`memory` 用 `InMemorySaver`，只在进程内存里 —— **进程重启就恢复不了**。
跨进程恢复要换成 `SqliteSaver`、`PostgresSaver` 等持久实现。

## 在工具里中断

```python
from langgraph.types import interrupt


@tool
def delete_files(pattern: str) -> str:
    """删除匹配的文件，需要人工确认。"""
    approved = interrupt({"action": "delete", "pattern": pattern})
    if not approved:
        return "用户取消"
    ...
```

`interrupt()` 抛出的值会传回图的调用方，图暂停。恢复时传入的值成为
`interrupt()` 的返回值。

## 捕获中断

`run()` 遇到中断时抛 `LangGraphInterruptError`：

```python
from your_package.langgraph_agent import LangGraphInterruptError

try:
    result = await runtime.run(prompt, CodeReviewOutput, thread_id="job-42")
except LangGraphInterruptError as error:
    print(f"线程 {error.thread_id} 等待确认")
    for item in error.interrupts:
        print(item)
    # 外部确认后再 resume
    result = await runtime.resume("job-42", True, CodeReviewOutput)
```

`thread_id` 是恢复的钥匙 —— 不传时用当次 `run_id`，中断后无法再次定位。
**需要人工介入的流程必须显式传稳定的 `thread_id`**（如任务 ID）。

## 完整流程

```
run(prompt, Output, thread_id="job-42")
  → ... → interrupt(...) → LangGraphInterruptError(thread_id, interrupts)
  → 外部确认
  → resume("job-42", True, Output) → ... → END
```

## 并发与隔离

每个 `thread_id` 有独立的 checkpoint。并发任务用不同 `thread_id`，否则
状态会串。

`InMemorySaver` 的并发安全性依赖 LangGraph 实现，高并发下建议换持久
checkpointer —— 它同时提供进程隔离。

## 日志

中断和恢复都会记事件：

| 事件 | 时机 |
|---|---|
| `tool_call_interrupted` | 工具内触发 `interrupt()` |
| `graph_interrupted` | 图整体暂停，带中断数量 |
| `graph_resumed` | 调用 `resume()` 时 |

日志只记 `thread_id`、`run_id` 和中断数量，不记中断携带的值 —— 可能含
业务数据。

## 常见错误

- **不传 `thread_id`。** 中断后拿不到恢复句柄。
- **`checkpoint: none` 却期待恢复。** 直接报错。
- **进程重启后 `resume()`。** `InMemorySaver` 已清空，需要持久 checkpointer。
- **并发复用 `thread_id`。** 状态互相污染。
- **把中断值写进日志。** 可能含敏感数据。
