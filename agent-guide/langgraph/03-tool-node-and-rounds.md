# 工具循环

LangGraph 用原生 `ToolNode` 执行工具调用，循环次数有上限，每次调用都记审计。

## 循环结构

```
invoke_agent ─┬→ tools → record_tool_round → invoke_agent
              └→ invoke_model（无工具调用时）
```

模型返回工具调用 → 执行工具 → 累计轮次 → 回到模型。模型不再调工具时
进入最终结构化输出。

## 注册工具

```python
from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """读取项目内文件内容。"""
    return Path(path).read_text()


runtime = LangGraphReviewRuntime(
    model=model,
    tools=[read_file],
    config=config,
)
```

有工具时图会加入 `invoke_agent`、`tools`、`record_tool_round`、
`tool_limit` 四个节点；没有工具时直接 `prepare → invoke_model`。

工具名必须唯一，重复抛 `ValueError`。

## 轮次上限

`max_tool_rounds`（默认 4，范围 1-20）限制工具循环次数：

```yaml
max_tool_rounds: 4
```

超出后进入 `tool_limit` 节点并失败。**这不是异常重试，是防死循环的硬
上限** —— 达到上限说明任务设计有问题或模型在无效循环，应该失败而不是
继续消耗。

调高上限前先问：为什么需要这么多轮？通常是工具粒度太细或 Prompt 没
说清目标。

## 工具审计

每次工具调用通过 `awrap_tool_call` 记录：

```python
async def _audit_tool_call(self, request, execute):
    call = request.tool_call
    args = call.get("args", {})
    self.events.emit(
        "tool_call_started",
        tool_name=str(call.get("name", "")),
        tool_call_id=str(call.get("id", "")),
        input_keys=sorted(args) if isinstance(args, dict) else [],
    )
    ...
```

记录内容：

| 字段 | 记录 |
|---|---|
| `tool_name` | 是 |
| `tool_call_id` | 是 |
| `input_keys` | 是（只有键名） |
| 参数**值** | 否 |
| 结果**内容** | 否 |
| `duration_ms` | 是 |
| `error_type` | 是 |

不记参数值和结果正文：它们可能含用户数据、路径、密钥。排障需要时通过
`tool_call_id` 关联其他日志。

## 错误处理

`ToolNode(handle_tool_errors=False)` —— 工具异常向上传播，由节点策略
处理，不静默返回错误文本给模型。

区别：

| 设置 | 行为 |
|---|---|
| `handle_tool_errors=False` | 异常抛出，触发节点的 `retry_policy` |
| `handle_tool_errors=True` | 异常转成文本返回给模型，由模型消化 |

默认用 `False`：让失败明确暴露，而不是让模型猜测错误。

## 本地工具 vs MCP 工具

```python
# 本地工具：代码即授权
tools = [read_file, query_db]

# MCP 工具：还要 mcp_allowed_tools 显式授权
runtime = await LangGraphReviewRuntime.with_anthropic_and_mcp()
```

本地 `BaseTool` 传进去就能用，视为代码授权。MCP 工具即使配置了连接，
`mcp_allowed_tools: []` 时也不会加载 —— 声明和授权分离。

详见 [MCP 与 Skills](../agent-runtime/04-mcp-and-skills.md)。

## 追踪脱敏

```python
trace_policy = TracePolicy(
    process_inputs=omit_payload,
    process_outputs=omit_payload,
)
```

LangGraph 自己的 trace 会记录节点输入输出。用 `omit_payload` 把内容替换
成占位符，避免把 prompt 全文和工具结果写进 trace。

这和 `AgentEventLogger` 是两套东西：trace 给 LangGraph 的观测工具，
JSONL 日志给项目自己的排障。两边都要脱敏。
