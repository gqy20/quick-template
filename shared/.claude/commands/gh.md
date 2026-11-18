---
name: gh
description: GitHub CLI 专家助手，提供 gh 命令的场景化指导
version: 0.0.1
tags:
  - git
  - github
  - cli
  - devops
  - workflow
dependencies:
  gh: ">=2.0"
  git: "any"
---

# GitHub CLI

在仓库目录外或有多个远端时，用 `-R OWNER/REPO` 指定目标。读取仓库数据前可用 `gh auth status` 核对登录账户。写入范围按 `AGENTS.md` 和用户本次授权执行。

## 查询 Issue、PR 和 CI

```bash
gh issue list --state open --assignee @me
gh issue view 123 --comments
gh pr list --state open
gh pr view 42 --json title,baseRefName,headRefName,reviewDecision
gh pr diff 42
gh pr checks 42
gh run list --branch main --limit 5
gh run view RUN_ID --log-failed
```

需跟踪任务到结束时，使用 `gh run watch RUN_ID --exit-status`。脚本读取结果使用 `--json` 选字段，例如 `gh issue list --json number,title`。

## 创建或更新

多行正文保存在文件里，通过 `--body-file` 传入，保留 Markdown、反引号和换行。

```bash
gh issue create --title "标题" --body-file issue.md
gh pr create --base main --draft --title "标题" --body-file pr.md
gh pr edit 42 --body-file pr.md
```

## 其他操作

| 任务 | 查询当前版本支持的参数 |
|---|---|
| 审查或合并 PR | `gh pr review --help`、`gh pr merge --help` |
| 标签、里程碑、Projects | `gh label --help`、`gh api --help`、`gh project --help` |
| Actions、发布和仓库配置 | `gh workflow --help`、`gh release --help`、`gh repo --help` |
| Secrets、变量和密钥 | `gh secret --help`、`gh variable --help`、`gh ssh-key --help`、`gh gpg-key --help` |
| Codespaces、Gist、组织与扩展 | `gh codespace --help`、`gh gist --help`、`gh org --help`、`gh extension --help` |

出现 `No default remote repository` 时先指定 `-R`。遇到 403 时按错误信息核对目标仓库、账户权限和速率限制。
