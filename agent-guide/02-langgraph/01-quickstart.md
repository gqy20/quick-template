# LangGraph 快速开始

LangGraph 让你自己编排状态机：定义 State、节点和边，控制每一步做什么。
相比 Claude Agent SDK 的"给上下文要结果"，这里能表达多步骤、条件分支和
中途暂停。

## 安装

```bash
uv sync --extra agent-langgraph
```

## 最小示例

```python
import asyncio

from your_package.agent_models import CodeReviewOutput
from your_package.langgraph_agent import LangGraphReviewRuntime
from your_package.prompt import PromptRegistry

CODE = "def add(a, b):\n    return a + b\n"


async def main() -> None:
    prompts = PromptRegistry("config/prompts")
    prompt = prompts.render("code-review", language="Python", code=CODE)

    runtime = await LangGraphReviewRuntime.with_anthropic_and_mcp()
    result = await runtime.run(prompt, CodeReviewOutput)
    print(result.model_dump_json(indent=2))


asyncio.run(main())
```

要点：

- `run()` 接受 `RenderedPrompt`，不是裸字符串 —— 需要 Prompt 的版本和
  变量契约进入日志。
- 返回 `CodeReviewOutput` 实例，经过 Pydantic 校验。
- 需要 `ANTHROPIC_API_KEY`。默认 `mcp_allowed_tools: []`，此时不连接 MCP。

## 三种构造方式

| 方法 | 工具来源 | 用途 |
|---|---|---|
| `LangGraphReviewRuntime(model, tools)` | 直接传入 `BaseTool` 列表 | 完全自定义，测试用 |
| `.with_anthropic()` | 无，或代码传入的本地工具 | 不需要 MCP |
| `.with_anthropic_and_mcp()` | 本地工具 + `.mcp.json` 授权的 MCP 工具 | 默认形态 |

用假的 model 做离线测试：

```python
runtime = LangGraphReviewRuntime(model=FakeStructuredModel(), tools=[])
```

`FakeStructuredModel` 只需实现 `StructuredModel` 协议（`bind_tools` 和
结构化调用），不需要真实网络。

## 一次运行的完整链路

```
prepare → invoke_agent ─┬→ tools → record_tool_round → invoke_agent
                        └→ invoke_model → validate ─┬→ END
                                    ↑                └→ repair → invoke_model
                                    └────────────────────┘
```

没有工具时跳过 `invoke_agent` 和 `tools`，直接 `prepare → invoke_model`。

各步骤：

| 节点 | 作用 |
|---|---|
| `prepare` | 写入 Prompt 与轮次上限 |
| `invoke_agent` | 带工具调用模型 |
| `tools` | 原生 `ToolNode` 执行工具 |
| `record_tool_round` | 累计工具轮次，超限转入 `tool_limit` |
| `tool_limit` | 超出 `max_tool_rounds` 时失败 |
| `invoke_model` | 不带工具的最终结构化调用 |
| `validate` | 按 Pydantic Schema 校验输出 |
| `repair` | 校验失败时带上错误重试，最多 `max_attempts` |

## 配置

`config/runtimes/langgraph.yaml`：

```yaml
model: claude-sonnet-4-6
temperature: 0
max_attempts: 2              # 校验失败后的修复轮次
provider_retry_attempts: 3   # 网络/供应商错误的 SDK 重试
model_timeout_seconds: 60
recursion_limit: 24
max_tool_rounds: 4           # 工具循环上限
checkpoint: memory           # memory | none
mcp_config: .mcp.json
tool_name_prefix: true
mcp_allowed_tools: []
jsonl_path: logs/agent/langgraph.jsonl
```

## 下一步

- [写自己的 StateGraph](02-stategraph-basics.md) —— State、Context、节点
- [工具循环](03-tool-node-and-rounds.md) —— `ToolNode`、轮次上限、审计
- [中断与恢复](04-interrupt-and-resume.md) —— `interrupt()` 与 `resume()`
