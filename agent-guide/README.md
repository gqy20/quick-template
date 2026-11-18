# Agent 开发指南

执行 `quick-template --language python --with-agent` 生成示例项目。将示例中的 `your_package` 替换为生成的 Python 包名。

首次运行见 [Claude SDK 快速开始](agent-runtime/01-quickstart.md) 或 [LangGraph 快速开始](langgraph/01-quickstart.md)。

## 目录

| 专题 | 内容 |
|---|---|
| [agent-runtime](agent-runtime/) | Claude Agent SDK：配置、工具权限、MCP 与 Skills、Session |
| [langgraph](langgraph/) | LangGraph：StateGraph、工具循环、中断恢复 |
| [prompts](prompts/) | Prompt Registry：变量契约、版本、渲染 |
| [structured-output](structured-output/) | Pydantic 输出模型与校验 |
| [logging](logging/) | JSONL 事件日志与脱敏 |
| [sandbox](sandbox/) | 工具在沙箱里执行：边界、策略与两个常见故障 |

## 两种 Runtime 怎么选

| 能力 | Claude Agent SDK | LangGraph |
|---|---|---|
| 适用任务 | 模型选择工具来完成任务 | 程序显式控制步骤、分支和暂停点 |
| 安装 | `uv sync --extra agent` | `uv sync --extra agent-langgraph` |
| 内置工具（Read/Edit/Bash 等） | ✅ | ❌ 只有你传入的 |
| Skills / MCP | ✅ 原生 | MCP 经 Adapter |
| 工具调用拦截 | ✅ `hooks`（10 个事件） | ✅ 节点内代码 |
| 人工审批 | ✅ `can_use_tool` 回调 | ✅ `interrupt()` / `resume()` |
| 跨进程恢复 | ⚠️ `project` 状态 + SDK `resume` | ✅ checkpoint（可换持久实现） |
| OS 级沙箱 | ✅ `sandbox` 选项 | ❌ 需自行隔离 |
| 步骤与分支控制 | ❌ 交给模型 | ✅ 显式 StateGraph |
| 工具轮次上限 | `max_turns` | `max_tool_rounds` |

两者共享 Prompt Registry、Pydantic 输出模型和高层日志约定，但运行时不
可互换：Claude Agent SDK 的执行器没有实现 LangGraph 要求的模型协议
（`with_structured_output` 与 `bind_tools`），不能当作节点里的模型使用。

需要组合时，可以在 LangGraph 的某个节点内发起一次完整的 SDK 查询，把
返回值写回 State。代价是这次调用对图是黑盒——工具循环、重试和中断都在
SDK 内部，LangGraph 看不到也控制不了。

## 共同约定

- **默认离线。** 普通启动和测试不调用真实模型；只有显式开关才发起调用。
- **默认最小权限。** Claude 侧默认 `tools: []` + `permission_mode: dontAsk`；
  LangGraph 侧默认不连接 MCP（`mcp_allowed_tools: []`）。
- **日志不记正文。** 只记录工具名、参数键、状态、耗时和异常类型。
- **结构化输出经过校验。** 模型返回不符合 Schema 时抛错，不降级为自由文本。

## 相关文档

- 生成项目的文档组织约定：`shared/docs/README.md`
- 模板实现：`languages/python/src/{{package_name}}/`
- 可运行示例：`languages/python/examples/langgraph_review.py`
