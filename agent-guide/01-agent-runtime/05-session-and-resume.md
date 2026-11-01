# Session 与状态隔离

Claude Agent SDK 会在 `CLAUDE_CONFIG_DIR` 下保存会话状态。这个目录从哪来、
运行后是否保留，由 `runtime_state.mode` 决定。

## 三种模式

| 模式 | `CLAUDE_CONFIG_DIR` | 运行后 | 用途 |
|---|---|---|---|
| `ephemeral`（默认） | 临时目录 | 删除 | 单次任务，互不干扰 |
| `project` | `.agent-state/claude` | 保留 | 需要 resume 的重复会话 |
| `default` | 不设置 | — | 沿用用户 `~/.claude` 的登录和设置 |

```yaml
runtime_state:
  mode: project
  project_path: .agent-state/claude
```

目录以 `0o700` 权限创建。`default` 模式不设置 `CLAUDE_CONFIG_DIR`，Agent
直接读用户全局配置。

## 为什么默认 ephemeral

每次运行用独立的临时目录，意味着：

- 两次运行不会互相污染会话历史
- 不会把用户 `~/.claude` 的配置、Skill、MCP 带进任务
- 结束后不留残留，适合 CI 和批处理

代价是**不能跨运行 resume** —— 会话状态已删除。

## 需要 resume 时

改成 `project` 模式，状态写入项目内固定目录：

```yaml
runtime_state:
  mode: project
  project_path: .agent-state/claude
```

这个目录应加入 `.gitignore`：它包含完整 transcript，可能有敏感上下文。

注意 `project` 模式只是**保留状态**，不代表自动 resume。是否复用某个
会话仍由 SDK 的 session 参数控制。

## default 模式的代价

`default` 模式下 Agent 会读到：

- 用户的全局 `~/.claude` 设置
- 用户登录的 Claude 账号
- 用户全局安装的 Skill 和 MCP 配置

这在**你自己本机调试**时方便，但在自动化、CI 或多人环境里会让结果不可
复现。只有明确需要沿用登录态时才用。

## 与 `.claude/` 的区别

项目内的 `.claude/` 目录（`settings.json`、`skills/`、`commands/`）是
**项目配置**，随仓库提交，所有使用者共享。

`.agent-state/` 是**运行时状态**，不提交。两者不要混：

- `.claude/skills/<name>/SKILL.md` → 项目 Skill，入库
- `.agent-state/claude/` → 会话 transcript，不入库

## 检查清单

部署前确认：

- [ ] 生产/CI 环境用 `ephemeral` 或 `project`，不用 `default`
- [ ] `.agent-state/` 在 `.gitignore` 里
- [ ] 需要跨运行恢复时才设 `project`，并确认状态目录的清理策略
- [ ] 日志的 `debug_file` 为 `null`（它会记录完整上下文）
