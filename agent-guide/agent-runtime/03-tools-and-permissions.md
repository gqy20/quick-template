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
| `dontAsk` | 自动拒绝本应询问的调用，无需批准的读取仍执行 | 无人值守的批处理 |
| `default` | 首次使用每个工具时询问 | 交互式开发 |
| `acceptEdits` | 自动接受工作目录内的文件编辑，其余仍询问 | 允许改代码的助手 |
| `plan` | 只读探索：读文件和运行只读命令，不改源码 | 只分析不动手 |
| `auto` | 不弹常规提示，后台分类器判断动作是否符合请求 | 可信环境里的自动化 |
| `bypassPermissions` | 跳过提示，但仍有任何模式都不自动批准的动作 | 仅在完全受控的容器内 |

`bypassPermissions` 会让 Agent 无确认地执行大多数工具调用。模板默认
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

## 确定性拦截：Hooks

允许列表决定「模型能碰哪些工具」，hooks 决定「这次调用能不能通过」。
前者是静态范围，后者可以看参数、改参数、直接阻断。

```python
from claude_agent_sdk import HookMatcher

from your_package.agent import AgentRunner, output_format_schema


async def deny_outside_root(payload, tool_use_id, context):
    target = (payload.get("tool_input") or {}).get("file_path")
    if isinstance(target, str) and Path(target).resolve().parent != ROOT:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"工作目录外: {target}",
            }
        }
    return {}


runner = AgentRunner(
    schema=output_format_schema(SummaryOutput),
    hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[deny_outside_root])]},
)
```

可用的 hook 事件：

| 事件 | 用途 |
|---|---|
| `PreToolUse` / `PostToolUse` / `PostToolUseFailure` | 拦截、改参数、记录结果 |
| `UserPromptSubmit` | 提交前检查或补充上下文 |
| `PermissionRequest` | 在权限询问发生前介入 |
| `Stop` / `SubagentStop` / `SubagentStart` | 回合与子代理边界 |
| `PreCompact` / `Notification` | 压缩前与通知 |

`HookMatcher(matcher=...)` 可按工具名过滤，`None` 表示全部匹配。

**与允许列表的分工**：能用 `allowed_tools` 表达的就用允许列表——静态、可
审阅、不写代码。只有需要看参数才知道该不该放行时才写 hook。

## 人在回路：can_use_tool

每次工具调用前回调，问人，或者按策略自动决定：

```python
async def confirm(tool_name, tool_input, context):
    if tool_name == "Read":
        return {"behavior": "allow", "updated_input": tool_input}
    answer = input(f"允许 {tool_name}? [y/N] ").strip().lower()
    if answer == "y":
        return {"behavior": "allow", "updated_input": tool_input}
    return {"behavior": "deny", "message": "用户拒绝", "interrupt": True}


runner = AgentRunner(schema=..., can_use_tool=confirm)
```

| 返回 | 效果 |
|---|---|
| `{"behavior": "allow", "updated_input": {...}}` | 放行；可顺手改写参数 |
| `{"behavior": "deny", "message": "..."}` | 拒绝，模型收到原因 |
| `{"behavior": "deny", "interrupt": True}` | 拒绝并结束本回合 |

配合 `permission_mode: default` 使用；`dontAsk` 下不会走到这个回调。

**服务端要注意**：回调是 async 的，但真实审批往往跨请求。需要在回调里把
待审请求存下来、等待外部决定（或直接返回 deny），不要把 HTTP 请求挂在那里。

完整可运行示例见生成项目的 `examples/claude_agent_guard.py`。
