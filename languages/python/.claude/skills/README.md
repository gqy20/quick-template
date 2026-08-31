# Project Skills

将项目 Skill 放在 `.claude/skills/<skill-name>/SKILL.md`。

在 `config/agent.yaml` 中通过 `skills: [skill-name]` 精确启用，或使用
`skills: all` 启用所有已发现 Skill。`skills: []` 表示明确禁用。

Skill 是上下文能力，不是安全沙箱。不要在 Skill 文件中保存 Secret；工具权限
仍由 `tools`、`allowed_tools`、`disallowed_tools`、permission mode 与 hooks 控制。
