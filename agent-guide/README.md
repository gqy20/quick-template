# Agent 开发指南

用 Python 脚本调用和编写智能体的技术参考。覆盖 Claude Agent SDK 与
LangGraph 两种 Runtime、Prompt 管理、结构化输出和运行日志。

示例代码中的 `your_package` 指你项目的包名。由 quick-template 生成的
Python 项目代入自己的包名即可；其他项目按自己的模块结构替换。

## 阅读顺序

1. [Claude Agent SDK 快速开始](agent-runtime/01-quickstart.md) —— 一次
   结构化查询的最小完整示例。
2. [两种 Runtime 怎么选](#两种-runtime-怎么选) —— 决定用哪条路。
3. 按需查阅对应的配置、工具、Prompt、日志专题。

## 目录

| 专题 | 内容 |
|---|---|
| [agent-runtime](agent-runtime/) | Claude Agent SDK：配置、工具权限、MCP 与 Skills、Session |
| [langgraph](langgraph/) | LangGraph：StateGraph、工具循环、中断恢复 |
| [prompts](prompts/) | Prompt Registry：变量契约、版本、渲染 |
| [structured-output](structured-output/) | Pydantic 输出模型与校验 |
| [logging](logging/) | JSONL 事件日志与脱敏 |

## 两种 Runtime 怎么选

| | Claude Agent SDK | LangGraph |
|---|---|---|
| 定位 | 直接驱动 Claude Code 运行时 | 自己编排状态机 |
| 工具 | SDK 内置工具 + 权限模式管控 | 代码里显式传入 `BaseTool` |
| 状态 | Session 由 SDK 管理 | 自己定义 State，checkpoint 由你选 |
| 适合 | 需要文件读写、Skills、MCP 的助手型任务 | 需要明确步骤、分支、人工介入的流程 |
| 依赖 | `uv sync --extra agent` | `uv sync --extra agent-langgraph` |

判据：**任务能用"给一段上下文、要一个结构化结果"描述，用 Claude Agent
SDK；任务需要多步骤、条件分支或中途暂停，用 LangGraph。**

两者共享 Prompt Registry、Pydantic 输出模型和高层日志约定，但运行时不
可互换：Claude Agent SDK 的执行器没有实现 LangGraph 要求的模型协议
（`with_structured_output` 与 `bind_tools`），不能当作节点里的模型使用。

需要组合时，可以在 LangGraph 的某个节点内发起一次完整的 SDK 查询，把
返回值写回 State。代价是这次调用对图是黑盒——工具循环、重试和中断都在
SDK 内部，LangGraph 看不到也控制不了。

## 共同约定

两条路径都遵循同样的边界：

- **默认离线。** 普通启动和测试不调用真实模型；只有显式开关才发起调用。
- **默认最小权限。** Claude 侧默认 `tools: []` + `permission_mode: dontAsk`；
  LangGraph 侧默认不连接 MCP（`mcp_allowed_tools: []`）。
- **日志不记正文。** 只记录工具名、参数键、状态、耗时和异常类型。
- **结构化输出经过校验。** 模型返回不符合 Schema 时抛错，不降级为自由文本。

## 相关文档

- 生成项目的文档组织约定：`shared/docs/README.md`
- 模板实现：`languages/python/src/{{package_name}}/`
- 可运行示例：`languages/python/examples/langgraph_review.py`
