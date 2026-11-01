# 运行配置

Claude Agent SDK 的项目配置在 `config/agent.yaml`，由
`your_package.agent.AgentConfig` 校验。字段直接映射 SDK 的
`ClaudeAgentOptions`，本模块只做项目化，不重新定义 SDK 语义。

## 加载

```python
from your_package.agent import AgentConfig

config = AgentConfig.from_yaml()  # 默认 config/agent.yaml
config = AgentConfig.from_yaml("config/other.yaml")  # 其他配置
```

`from_yaml` 会：

- 校验所有字段，类型或取值非法直接抛 `ValidationError`
- 把 `cwd` 设为配置文件所在项目的根目录（`config/` 的上级），
  因此配置里的相对路径都以项目根为基准
- `logging` 段映射到 `AgentLoggingConfig`，其余键与字段同名

`structured_query` 不传 `config_path` 时自动加载 `config/agent.yaml`；
文件不存在则使用字段默认值。

## 模型

| 键 | 默认 | 说明 |
|---|---|---|
| `model` | `null` | 主模型。`null` 时用 SDK 默认 |
| `fallback_model` | `null` | 主模型失败时的回退模型 |
| `max_turns` | `5` | 单次查询最大轮次，最小 1 |
| `max_budget_usd` | `null` | 单次查询预算上限，必须大于 0 |

`model` 为 `null` 时不传给 SDK；`max_budget_usd` 为 `null` 时不传。

## 工具与权限

| 键 | 默认 | 说明 |
|---|---|---|
| `tools` | `[]` | 开放给模型的工具。空数组表示禁用全部内置工具 |
| `allowed_tools` | `[]` | 允许使用的工具白名单 |
| `disallowed_tools` | `[]` | 禁止使用的工具黑名单 |
| `permission_mode` | `dontAsk` | 权限模式 |

需要完整的 Claude Code 工具集时，把 `tools` 改为 `claude_code`：

```yaml
tools: claude_code
```

`permission_mode` 取值：

| 值 | 含义 |
|---|---|
| `default` | 按 SDK 默认流程询问 |
| `acceptEdits` | 自动接受文件编辑 |
| `bypassPermissions` | 绕过全部权限检查 |
| `plan` | 只读规划 |
| `dontAsk` | 不询问，直接失败 |

默认 `dontAsk` 配合空工具列表：Agent 只能读取和推理，任何写操作都会被
拒绝。这是模板的默认安全姿态。

## MCP 与 Skills

| 键 | 默认 | 说明 |
|---|---|---|
| `mcp_config` | `.mcp.json` | MCP server 配置文件路径 |
| `strict_mcp_config` | `true` | 严格模式，忽略其他来源的 MCP 配置 |
| `skills` | `[]` | 启用的项目 Skill 名称 |
| `plugins` | `[]` | 插件配置 |
| `setting_sources` | `[project]` | 读取哪些层级的 Claude 设置 |

`skills` 接受精确名称列表或 `all`；`[]` 表示明确禁用。详见
[MCP 与 Skills](04-mcp-and-skills.md)。

`mcp_config` 与代码传入的 `mcp_servers` 互斥，同时设置抛 `ValueError`。

## Prompt

| 键 | 默认 | 说明 |
|---|---|---|
| `prompt_dir` | `config/prompts` | Prompt Registry 根目录 |
| `default_prompt` | `default` | 默认 Prompt id |

Prompt 文本独立维护在 `prompt_dir`，配置只声明目录和默认 id。

## 运行状态

| 键 | 默认 | 说明 |
|---|---|---|
| `runtime_state.mode` | `ephemeral` | Claude 状态目录策略 |
| `runtime_state.project_path` | `.agent-state/claude` | `project` 模式下的状态目录 |

`mode` 取值：

| 值 | 行为 |
|---|---|
| `ephemeral` | 每次运行用临时 `CLAUDE_CONFIG_DIR`，结束后删除 |
| `project` | 状态写入 `project_path`，可跨进程 resume |
| `default` | 沿用用户 `~/.claude` 的登录和全局设置 |

需要 resume 时用 `project`；只有明确要沿用用户登录态才用 `default`。
`default` 会让 Agent 读到用户全局配置，评估影响后再启用。

## 消息与子代理

| 键 | 默认 | 说明 |
|---|---|---|
| `include_partial_messages` | `false` | 是否投递流式部分消息 |
| `include_hook_events` | `true` | 是否投递 hook 事件 |
| `forward_subagent_text` | `false` | 是否转发子代理正文 |

默认不转发子代理正文：子代理输出可能包含中间推理，转发会增加上下文
消耗并可能带出敏感内容。需要观察子代理时再开启。

## 日志

`logging` 段映射到 `AgentLoggingConfig`：

| 键 | 默认 | 说明 |
|---|---|---|
| `level` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |
| `jsonl_path` | `logs/agent.jsonl` | JSONL 日志路径 |
| `capture_stderr` | `true` | 是否捕获 SDK 的 stderr |
| `debug_file` | `null` | SDK debug 文件路径 |
| `max_bytes` | `10485760` | 单个日志文件上限，最小 1024 |
| `backup_count` | `5` | 保留的历史文件数，1-20 |

`debug_file` 指向的文件可能含完整上下文，默认关闭且不得提交。

日志内容与脱敏规则见 [日志专题](../05-logging/01-events.md)。

## system_prompt

`system_prompt` 不在 YAML 中直接暴露，但 `AgentConfig` 支持它，值为字符串
或 SDK 的 preset 字典。默认使用 `claude_code` preset。传
`RenderedPrompt` 时，Prompt 的 `instructions` 会以 preset 的 `append`
方式追加到 system prompt，不覆盖 preset。
