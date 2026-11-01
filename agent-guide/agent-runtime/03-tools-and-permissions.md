# 工具与权限

工具决定模型能做什么，权限决定模型做什么时是否需要停下。两者独立配置：
开工具不自动放开权限，放权限也不自动开工具。

## 开放工具

`tools` 决定模型能看到的内置工具：

```yaml
tools: []          # 不开放任何内置工具（默认）

tools: claude_code # 开放完整 Claude Code 工具集

tools:             # 或列出具体工具名
  - Read
  - Grep
  - Glob
```

模板默认 `tools: []` —— Agent 只能读取和推理，任何写操作都会被拒绝。
需要它修改文件时显式开放，并把 `permission_mode` 一起调整。

## 白名单与黑名单

`allowed_tools` 和 `disallowed_tools` 在工具集之上进一步筛选：

```yaml
tools: claude_code
allowed_tools:
  - Read
  - Grep
  - Edit
disallowed_tools:
  - Bash
```

`disallowed_tools` 优先：工具即使在 `tools` 和 `allowed_tools` 里，只要出现
在 `disallowed_tools` 中就不会被调用。

## 权限模式

`permission_mode` 决定工具调用时是否需要人工确认：

| 值 | 行为 | 适用 |
|---|---|---|
| `dontAsk` | 不询问，不可用时直接失败 | 无人值守的批处理 |
| `default` | 按 SDK 默认流程询问 | 交互式开发 |
| `acceptEdits` | 文件编辑自动接受，其余仍询问 | 允许改代码的助手 |
| `plan` | 只读，不允许修改 | 只分析不动手 |
| `bypassPermissions` | 绕过全部检查 | 仅在完全受控的容器内 |

`bypassPermissions` 会让 Agent 无确认地执行任意工具调用。模板默认
`dontAsk` 是刻意的：要么给最小工具集，要么显式放开，不靠兜底放宽。

## 默认姿态

生成项目的默认配置：

```yaml
tools: []
allowed_tools: []
disallowed_tools: []
permission_mode: dontAsk
```

效果：Agent 能读文件、跑推理、给出结构化结果，但不能改文件、不能执行
命令。需要写权限时按最小范围逐步放开 —— 先加具体工具，再考虑调整
`permission_mode`。

## 代码里调用

配置决定默认值，也可以直接构造 `AgentConfig`：

```python
from your_package.agent import AgentConfig, structured_query

config = AgentConfig(
    tools=["Read", "Grep"],
    permission_mode="dontAsk",
)
result = await structured_query("检查这段代码的问题", CodeReviewOutput, config=config)
```

## 与 LangGraph 的差异

Claude Agent SDK 路径下，工具由 SDK 按 `tools` 和 `permission_mode` 管控；
LangGraph 路径下，工具是代码里显式传入的 `BaseTool` 列表，视为代码授权，
不走 SDK 的权限询问。

两种模型的差别在于**授权发生在哪**：SDK 侧是运行时权限系统，LangGraph
侧是代码本身。不要指望一份 `agent.yaml` 同时约束两条路径。

详见 [LangGraph 工具循环](../langgraph/03-tool-node-and-rounds.md)。
