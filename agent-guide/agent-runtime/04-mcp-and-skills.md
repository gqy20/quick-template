# MCP 与 Skills

MCP 接外部工具服务，Skills 提供项目内的上下文能力。两者都默认关闭。

## MCP：声明与授权是两件事

`.mcp.json` 只声明连接，不代表工具可用：

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

配置里 `mcp_config: .mcp.json` 指向它。连接建立后，工具是否可调用由
`allowed_tools` 决定。

Claude Agent SDK 侧：

```yaml
mcp_config: .mcp.json
strict_mcp_config: true    # 忽略其他来源的 MCP 配置
tools: [Read, Grep]        # 内置工具
allowed_tools: [mcp__filesystem__read_file]
```

`strict_mcp_config: true` 时只读这份配置，不受用户全局 MCP 设置影响。
**默认开启，保持它。**

LangGraph 侧的授权更严格：`mcp_allowed_tools` 默认为 `[]`，此时根本不
连接 MCP。要启用必须显式列出 Adapter 暴露的最终工具名：

```yaml
mcp_config: .mcp.json
tool_name_prefix: true
mcp_allowed_tools:
  - filesystem__read_file
```

## 工具名的两种形态

| 路径 | 授权名 | 说明 |
|---|---|---|
| Claude Agent SDK | `mcp__<server>__<tool>` | SDK 原生命名 |
| LangGraph（`tool_name_prefix: true`） | `<server>__<tool>` | Adapter 加前缀 |

写错名字不会报错，只是工具不可用。启用前先用 Adapter 的
`client.get_tools()` 打印实际名称确认。

## Skills

Skills 是放在 `.claude/skills/<skill-name>/SKILL.md` 的项目能力：

```
.claude/skills/
└── code-review/
    └── SKILL.md
```

在 `config/agent.yaml` 中按精确名称启用：

```yaml
skills: [code-review]   # 只启用指定 Skill
skills: all             # 启用所有已发现的 Skill
skills: []              # 明确禁用（默认）
```

**Skill 是上下文能力，不是安全沙箱。** 它能让模型看到更多项目知识，
但不限制它能做什么 —— 工具权限仍由 `tools`、`allowed_tools`、
`disallowed_tools` 和 `permission_mode` 控制。

不要在 `SKILL.md` 中写 Secret。Skill 内容会进入模型上下文。

## 选 MCP 还是 Skill

| | MCP | Skill |
|---|---|---|
| 提供什么 | 外部工具调用能力 | 项目知识与流程说明 |
| 运行位置 | 独立进程 / 远程服务 | 模型上下文内 |
| 需要授权 | 是，按工具名 | 否，按名称启用 |
| 典型用途 | 查数据库、调 API、读外部系统 | 编码规范、审查清单、领域知识 |

判断很简单：**要执行动作选 MCP，要补充知识选 Skill。**

## 常见错误

- **只改 `.mcp.json` 就期待工具可用。** 声明不等于授权，还要配
  `allowed_tools`（SDK）或 `mcp_allowed_tools`（LangGraph）。
- **在 LangGraph 里用 SDK 的工具名。** 前缀不一样，名字对不上。
- **以为 Skill 能限制权限。** 它只影响上下文，不影响工具可用性。
- **把密钥写进 `SKILL.md`。** 它会进入模型上下文和日志。
