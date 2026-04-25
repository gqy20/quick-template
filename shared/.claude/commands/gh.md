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

# GitHub CLI 场景化助手

你是 GitHub CLI (gh) 的专家助手。请根据用户需求，引导完成 GitHub 相关操作。

---

## 前置检查

**执行任何操作前：**
1. 确认是否在 git 仓库：`git rev-parse --is-inside-work-tree`
2. 确认 gh 是否已登录：`gh auth status`
3. 如未登录执行：`gh auth login`
4. 获取当前 owner/repo：`gh repo view --json owner,name -q '.owner.login + "/" + .name'`

---

## 📊 仪表盘

```bash
gh status                                                      # 查看综合状态（issues/PRs/通知）
gh repo view                                                   # 查看当前仓库信息
gh repo view --json name,description,visibility,defaultBranchRef,owner,issues  # JSON 格式查看（使用 issues.totalCount 获取 issue 数量）
gh browse                                                      # 打开仓库主页
gh browse issues                                               # 打开 Issues 页面
gh browse pulls                                                # 打开 PRs 页面
gh browse actions                                              # 打开 Actions 页面
```

---

## 🔍 搜索与查询

```bash
# Issues 搜索
gh search issues --state open --limit 20                       # 基础搜索
gh search issues --label "bug,high-priority"                   # 按标签搜索
gh search issues --author <username>                           # 按作者搜索
gh issue list --state open --limit 20                          # 当前仓库搜索
gh issue list --state all --assignee @me                       # 我的 issues
# PRs 搜索
gh search prs --state open --limit 20                          # 基础搜索
gh search prs --reviewer <username>                            # 按审查者搜索
gh search prs --state merged --limit 20                        # 已合并 PR
gh pr list --state open --limit 20                             # 当前仓库 PR
gh pr list --author @me                                        # 我创建的 PR
gh pr list --reviewer @me                                      # 需要我审查的 PR
# 仓库搜索
gh search repos --language <language> --stars ">100"           # 按语言/星标搜索
gh search repos --topic "machine-learning"                     # 按主题搜索
gh search repos --org <organization>                           # 按组织搜索
# 查看详情
gh issue view <number>                                         # Issue 详情
gh issue view <number> --json title,body,state,labels,author   # Issue JSON 详情
gh pr view <number>                                            # PR 详情
gh pr view <number> --json title,body,state,author,reviewDecision,additions,deletions  # PR JSON 详情
gh pr diff <number>                                            # PR Diff
gh pr view <number> --json files --jq '.files[].path'         # PR 文件变更
gh pr view <number> --comments                                 # PR 评论
gh pr view <number} --json reviews --jq '.reviews[] | {author, state, body}'  # PR 审查
```

---

## 📝 Issue 管理

```bash
# 创建 Issue
gh issue create                                               # 交互式创建（推荐用于多行内容）
gh issue create --title "标题" --body "描述"                   # 简单单行
gh issue create --web                                         # 在浏览器中创建（处理复杂格式）
gh issue create -F issue.md                                  # 从文件读取 body
gh issue create --title "标题" -F -                           # 从 stdin 读取 body（echo "..." | gh issue create ... -F -）
gh issue create --title "Bug: 登录失败" --body "单行描述" --label "bug,high-priority" --assignee @me  # 带标签和指派
gh issue create --title "功能请求" --body "单行描述" --milestone "v1.2.0"  # 指定 milestone

# 多行 body 的安全方法
cat <<EOF | gh issue create --title "多行 Issue" -F -
## 功能描述

详细描述...

- 要点 1
- 要点 2
EOF
# 编辑 Issue
gh issue edit <number> --title "新标题"                        # 修改标题
gh issue edit <number> --body "新描述"                         # 修改描述
gh issue edit <number> --add-label "bug,urgent"                # 添加标签
gh issue edit <number> --remove-label "wontfix"                # 移除标签
gh issue edit <number> --assignee @me                          # 指派给某人
gh issue edit <number> --remove-assignee @me                   # 取消指派
gh issue edit <number> --milestone "v2.0.0"                    # 设置 milestone
gh issue comment <number> --body "评论内容"                    # 添加评论
# 关闭/重新打开
gh issue close <number>                                        # 关闭 issue
gh issue reopen <number>                                       # 重新打开
# Sub-issues 需要通过 API 管理（GraphQL 或 Projects API）
```

---

## 🔀 Pull Request 管理

```bash
# 创建 PR
gh pr create                                                   # 交互式创建（推荐用于多行内容）
gh pr create --fill                                            # 自动填充描述模板
gh pr create --web                                             # 在浏览器中创建（处理复杂格式）
gh pr create -F pr.md                                          # 从文件读取 body
gh pr create --title "功能" --body "单行描述"                   # 简单单行
gh pr create --base develop --title "功能" --body "单行"        # 指定 base 分支
gh pr create --draft --title "WIP: 功能开发中"                 # Draft PR
gh pr create --title "功能" --reviewer user1,user2 --body "单行"  # 指定审查者
gh pr create --title "功能" --label "enhancement" --body "单行"  # 指定标签

# 多行 body 的安全方法
cat <<EOF | gh pr create --title "功能标题" -F -
## 变更说明

详细描述...

## 测试
- 测试 1
- 测试 2
EOF
# Checkout PR
gh pr checkout 123                                             # PR 编号 checkout
gh pr checkout https://github.com/owner/repo/pull/123          # URL checkout
# 查看 PR
gh pr list --state open --limit 20                             # 列出 PR
gh pr list --author @me --state all                            # 我创建的 PR
gh pr list --reviewer @me                                      # 需要我审查的 PR
gh pr view 123                                                 # PR 详情
gh pr view 123 --json title,body,state,headRefName,baseRefName,additions,deletions,changedFiles  # PR JSON 详情
gh pr diff 123                                                 # PR 文件变更
gh pr checks 123                                               # PR 状态检查
# 更新 PR
gh pr edit 123 --title "新标题"                                # 修改标题
gh pr edit 123 --body "新描述"                                 # 修改描述
gh pr edit 123 --add-reviewer user1,user2                      # 添加审查者
gh pr edit 123 --add-label "ready-to-merge"                    # 添加标签
gh pr edit 123 --add-label "draft"                             # 转为 draft
gh pr edit 123 --remove-label "draft"                          # 标记为 ready
gh pr update 123                                               # 更新为最新 base 分支
# PR 审查
gh pr comment 123 --body "这里有个问题"                        # 添加评论
gh pr review 123 --comment --body "建议修改"                    # 审查评论
gh pr review 123 --approve --body "LGTM"                       # 批准
gh pr review 123 --request-changes --body "需要修改..."        # 请求更改
gh pr review 123 --body "一些意见..."                          # 通用评论
# 合并 PR
gh pr merge 123                                                # 默认方式合并
gh pr merge 123 --squash --message "合并信息"                   # Squash 合并
gh pr merge 123 --rebase                                       # Rebase 合并
gh pr merge 123 --delete-branch                                # 删除分支后合并
```

---

## 🏷️ Labels / Milestones / Projects

```bash
# Labels
gh label list                                                  # 列出标签
gh label create "bug" --color "d73a4a" --description "Bug report"  # 创建标签
gh label create "enhancement" --color "a2eeef" --description "New feature"  # 常用标签
gh label create "documentation" --color "0075ca" --description "Documentation"
gh label create "good first issue" --color "7057ff" --description "Good for newcomers"
gh label create "help wanted" --color "008672" --description "Extra attention"
gh label edit "bug" --color "ff0000" --description "Bug 问题"  # 编辑标签
gh label delete "wontfix"                                       # 删除标签
# Milestones
gh pr list --json milestoneNumber,title --jq '.[].milestone'   # 列出 PR 里程碑
gh issue list --json milestoneNumber,title --jq '.[].milestone'  # 列出 Issue 里程碑
gh api repos/:owner/:repo/milestones -f title="v1.0.0" -f state="open" -f description="第一个稳定版本"  # 创建里程碑
gh api repos/:owner/:repo/milestones/:number -X PATCH -f state="closed"  # 关闭里程碑
# Projects（需先执行：gh auth refresh -s project）
gh project list --owner @me                                    # 列出项目
gh project view <project_number> --owner @me                   # 查看项目详情
gh project item-list <project_number> --owner @me              # 列出项目 items
gh project item-add <project_number> --owner @me --url https://github.com/owner/repo/issues/<number>  # 添加 issue/PR
gh project field-list <project_number> --owner @me             # 列出项目字段
gh project item-create <project_number> --owner @me --title "标题" --body "内容"  # 创建项目 item
```

---

## 🚀 Actions & CI/CD

```bash
# Workflows
gh workflow list                                               # 列出 workflows
gh workflow view <workflow_name>                               # 查看 workflow 详情
gh workflow view <workflow_name> --yaml                        # 查看 workflow YAML
# Runs
gh run list --limit 20                                         # 列出运行记录
gh run list --workflow=<workflow_name> --limit 10              # 指定 workflow
gh run view <run_id>                                           # 查看运行详情
gh run view <run_id} --log                                     # 查看运行日志
gh run view <run_id} --log-failed                              # 查看失败日志
gh run watch <run_id}                                          # 实时查看日志
gh run rerun <run_id}                                          # 重新运行
gh run cancel <run_id}                                         # 取消运行
# Caches
gh cache list                                                  # 列出缓存
gh cache delete <cache_key>                                    # 删除指定缓存
gh cache delete --all                                          # 删除所有缓存
```

---

## 🔐 Secrets / Variables

```bash
# 仓库 Secrets
gh secret list                                                 # 列出 secrets
gh secret set MY_SECRET                                        # 设置 secret（交互式）
echo -n "value" | gh secret set MY_SECRET                      # 从环境变量设置
gh secret set MY_SECRET < secret_file.txt                      # 从文件设置
gh secret delete MY_SECRET                                     # 删除 secret
# 组织 Secrets
gh secret list --org <organization>                            # 列出组织 secrets
gh secret set ORG_SECRET --org <org>                           # 设置组织 secret
gh secret set ORG_SECRET --org <org> --visibility "private"    # 设置可见性（private/all/selected）
# 环境 Secrets
gh secret list --env <environment_name>                        # 列出环境 secrets
gh secret set ENV_SECRET --env <environment_name>              # 设置环境 secret
# 用户 Secrets（Codespaces）
gh secret list --user                                          # 列出用户 secrets
gh secret set USER_SECRET --user                               # 设置用户 secret
# Variables（Actions）
gh variable list                                               # 列出变量
gh variable set MY_VAR --body "value"                          # 设置变量
gh variable set MY_VAR < variable_file.txt                     # 从文件设置
gh variable delete MY_VAR                                      # 删除变量
```

---

## 💻 Codespaces

```bash
# 创建
gh codespace create                                            # 默认配置创建
gh codespace create --repo owner/repo --branch main            # 指定仓库和分支
gh codespace create --machine "premiumLinux"                   # 指定机器类型
gh codespace create --repo owner/repo --display-machine        # 显示可用机器类型
# 启动/停止
gh codespace list                                              # 列出 codespaces
gh codespace stop <codespace_name>                             # 停止
gh codespace create                                            # 启动（如已存在则直接使用）
# 连接
gh codespace ssh <codespace_name>                              # SSH 连接
gh codespace code <codespace_name>                             # 在 VS Code 中打开
gh codespace jupyter <codespace_name>                          # 在 JupyterLab 中打开
gh codespace view <codespace_name> --web                       # 在浏览器中打开
# 文件操作
gh codespace cp ./local-file.txt <cs_name>:/home/codespace/    # 本地→远程
gh codespace cp <cs_name>:/home/codespace/file.txt ./          # 远程→本地
# 日志/调试
gh codespace logs <codespace_name>                             # 查看日志
gh codespace view <codespace_name>                             # 查看详情
gh codespace ports <codespace_name>                            # 查看端口
# 重建/删除
gh codespace rebuild <codespace_name>                          # 重建容器
gh codespace delete <codespace_name>                           # 删除
gh codespace delete --all                                      # 删除所有
```

---

## 📦 Release 管理

```bash
# 创建
gh release create v1.0.0 --title "v1.0.0" --notes "第一个版本"  # 基础创建
gh release create v1.0.0 --notes-file RELEASE_NOTES.md         # 从文件读取 notes
gh release create v1.0.0 --generate-notes                      # 自动生成 notes
gh release create v1.0.0 --draft --notes "..."                  # Draft release
gh release create v1.0.0 --prerelease --notes "..."             # Pre-release
gh release create v1.0.0 ./dist/app.zip ./dist/installer.pkg   # 上传资产
# 查看/下载
gh release list                                                # 列出 releases
gh release view                                                # 查看最新 release
gh release view v1.0.0                                         # 查看指定 release
gh release download v1.0.0                                     # 下载资产
gh release download v1.0.0 --pattern "*.zip" --dist ./downloads/  # 按模式下载
# 删除
gh release delete v1.0.0 --yes                                 # 删除 release
```

---

## 🏠 仓库管理

```bash
# 创建
gh repo create my-new-repo --public                            # 创建公开仓库
gh repo create my-new-repo --private                           # 创建私有仓库
gh repo create my-repo --public --clone --description "描述" --source=. --push  # 创建并初始化
gh repo create my-repo --public --description "描述" --homepage "https://example.com" --clone  # 完整选项
# Fork/克隆
gh repo fork owner/repo                                        # Fork 到个人账户
gh repo fork owner/repo --org organization                     # Fork 到组织
gh repo fork owner/repo --clone                                # Fork 后克隆
gh repo clone owner/repo                                       # 克隆仓库
gh repo clone owner/repo my-directory                          # 克隆到指定目录
# 查看信息
gh repo view                                                   # 基础信息
gh repo view --json name,description,visibility,defaultBranchRef,licenseInfo,homepageUrl,issues,pullRequests  # JSON 格式（使用 issues.totalCount 和 pullRequests.totalCount 获取统计）
gh ruleset list                                                # 列出规则集
gh ruleset view <ruleset_id>                                   # 查看规则集详情
# 修改设置
gh repo edit --description "新描述" --homepage "https://..."    # 修改描述和主页
gh repo edit --visibility private                              # 修改可见性（private/public/internal）
gh repo edit --add-topic "python,api,rest"                     # 添加 topics
gh repo edit --remove-topic "deprecated"                       # 移除 topic
gh api repos/:owner/:repo -X PATCH -f has_wiki=true -f has_projects=true -f has_issues=false  # 启用/禁用功能
# 归档/删除
gh repo edit --archived true                                   # 归档（只读）
gh repo edit --archived false                                  # 取消归档
gh repo delete --yes                                           # 删除仓库（危险）
```

---

## 🗝️ 认证与密钥

```bash
# 登录/登出
gh auth login                                                  # 登录
gh auth logout                                                 # 登出
gh auth status                                                 # 查看状态
# SSH Keys
gh ssh-key list                                                # 列出 SSH keys
gh ssh-key add ~/.ssh/id_ed25519.pub --title "我的电脑"         # 添加 SSH key
gh ssh-key delete <key_id>                                     # 删除 SSH key
# GPG Keys
gh gpg-key list                                                # 列出 GPG keys
cat ~/.ssh/id_ed25519.pub | gh gpg-key add -                   # 添加 GPG key
gh gpg-key delete <key_id>                                     # 删除 GPG key
```

---

## 🏢 组织管理

```bash
gh org list                                                    # 列出组织
gh org view <organization>                                     # 查看组织详情
gh repo list <organization> --limit 50                         # 列出组织仓库
gh api orgs/<organization>/members --jq '.[].login'            # 列出组织成员
```

---

## 📦 Gists 管理

```bash
echo "代码" | gh gist create                                   # 创建 gist
gh gist create file.py --public --desc "Python 示例"           # 公开 gist
gh gist create file1.py file2.js --desc "多文件"                # 多文件 gist
gh gist list --limit 20                                        # 列出 gists
gh gist view <gist_id>                                         # 查看 gist
gh gist edit <gist_id> --file new_file.py                      # 编辑 gist
gh gist delete <gist_id}                                       # 删除 gist
```

---

## 🛠️ 高级功能（API）

```bash
# API 基础
gh api /user                                                   # GET 请求
gh api /repos/:owner/:repo/issues -f title="标题" -f body="内容"  # POST 请求
gh api /repos/:owner/:repo/issues/:number -X PATCH -f state="closed"  # PATCH 请求
gh api /repos/:owner/:repo/issues/:number -X DELETE            # DELETE 请求
gh api /repos/:owner/:repo/issues -f title="..." -f body='{"labels":["bug"]}' -H "Accept: application/vnd.github.v3+json"  # JSON body
gh api /user/repos --jq '.[].name'                            # jq 过滤
gh api /user/repos --paginate --jq '.[].full_name'            # 分页请求
# API 高级用法
gh api repos/:owner/:repo/pulls --paginate --jq '.[].title'   # 获取所有 PR 标题
gh api repos/:owner/:repo/issues -f title="..." -F labels[]=bug -F labels[]=urgent -F assignees[]=user1  # 复杂字段 issue
gh api repos/:owner/:repo -X PATCH -f allow_auto_merge=true -f delete_branch_on_merge=true  # 自动合并设置
gh api repos/:owner/:repo/branches/main/protection -X PUT -H "Accept: application/vnd.github.v3+json" -f required_pull_request_reviews='{"required_approving_review_count":1}' -f enforce_admins=true  # 分支保护
gh api repos/:owner/:repo/hooks --jq '.[].name'               # 查看 Webhooks
gh api repos/:owner/:repo/hooks -f name="web" -f active=true -f config='{"url":"https://example.com/webhook"}'  # 创建 webhook
# 别名
gh alias set prs 'pr list --state open --limit 20'             # 创建别名
gh alias set mine 'issue list --assignee @me'
gh alias set co 'pr checkout'
gh alias list                                                  # 查看别名
gh alias delete prs                                             # 删除别名
# 配置
gh config                                                      # 查看配置
gh config set git_protocol ssh                                 # 设置协议
gh config set editor vim                                       # 设置编辑器
gh config set prompt disabled                                  # 禁用提示
gh config get git_protocol                                     # 获取配置
# 扩展
gh extension search                                            # 搜索扩展
gh extension install owner/extension-repo                       # 安装扩展
gh extension list                                              # 列出已安装
gh extension upgrade <name>                                    # 升级扩展
gh extension remove <name}                                     # 删除扩展
```

---

## 常见工作流

```bash
# 新功能开发
git checkout -b feature/new-feature && git add . && git commit -m "feat: 添加新功能" && git push -u origin feature/new-feature && gh pr create --title "添加新功能" --body "..." --base main
# Bug 修复
git checkout -b fix/bug-123 && git commit -m "fix: 修复 #123" && git push -u origin fix/bug-123 && gh pr create --title "修复 #123" --body "Fixes #123"
# 批量关闭已解决 issues
gh issue list --label "resolved" --json number --jq '.[].number' | xargs -I {} gh issue close {} --comment "已在 v1.2.0 中解决"
# 批量添加标签
gh issue list --state open --json number --jq '.[].number' | xargs -I {} gh issue edit {} --add-label "triaged"
```

---

## 注意事项

1. **占位符**：`:owner`、`:repo`、`<number>` 等需替换为实际值
2. **权限**：某些操作需要相应仓库权限
3. **速率限制**：API 请求有速率限制
4. **危险操作**：删除/合并前务必确认
5. **--help**：任何命令可加 `--help` 查看详情
6. **多行 body**：避免使用 `--body "$(cat <<EOF...EOF)"`，推荐方法：
   - 交互式：`gh issue create`（不提供 --body）
   - 文件：`gh issue create -F issue.md`
   - Stdin：`cat <<EOF | gh issue create -F -`
   - 浏览器：`gh issue create --web`

---

## 常见问题排查

### 权限相关
```bash
# 检查当前权限
gh auth status

# 添加缺少的 scope（如 project）
gh auth refresh -s project

# 添加多个 scope
gh auth refresh -s project:write,read:org

# Fine-grained token 问题：需要特定权限
# Organization 相关操作需要 "Organization members" 权限
```

### 仓库默认设置
```bash
# 报错：No default remote repository
gh repo set-default                                          # 设置默认仓库
gh repo set-default -u                                       # 取消默认设置

# 或者直接指定仓库
gh issue list --repo owner/repo
```

### Git 配置冲突
```bash
# gh auth login 后 git push 仍失败
# 检查 git credential 配置
git config --list | grep credential

# 重置为 gh 管理
git config --global credential.helper # 清空
gh auth setup-git                                            # 重新配置
```

### Token 问题
```bash
# 查看当前 token scopes
gh auth status

# Token 过期或权限不足
gh auth logout && gh auth login                              # 重新登录

# 手动设置 token（使用 GH_TOKEN 环境变量）
export GH_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 网络问题
```bash
# 连接超时/代理问题
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890

# 或配置 git 代理
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

### API 字段问题
```bash
# 错误：openIssuesCount 不是顶层字段
gh repo view --json openIssuesCount

# 正确：使用嵌套的 issues 对象
gh repo view --json issues --jq '.issues.totalCount'

# 类似地，PR 统计使用 pullRequests.totalCount
gh repo view --json pullRequests --jq '.pullRequests.totalCount'

# 一起获取多个统计
gh repo view --json issues,pullRequests,watchers,stargazerCount --jq '
  "Issues: \(.issues.totalCount)",
  "PRs: \(.pullRequests.totalCount)",
  "Stars: \(.stargazerCount)",
  "Watchers: \(.watchers.totalCount)"
'
```

### 常见错误码
| 错误 | 原因 | 解决方案 |
|-----|------|---------|
| `HTTP 403` | 权限不足/速率限制 | `gh auth status` 或等待后重试 |
| `HTTP 404` | 资源不存在/仓库名错误 | 检查 owner/repo 是否正确 |
| `unauthenticated` | Token 过期 | `gh auth login` |
| `No default remote` | 未设置默认仓库 | `gh repo set-default` 或 `--repo` 参数 |
| `Too many requests` | API 速率限制 | 等待一分钟后重试 |
| `Unknown JSON field` | 字段名错误或不存在 | 使用 `--json name,description` 查看可用字段 |

---

## 使用指南

当用户执行 `/gh` 时：
1. **检测上下文**：确认 git 仓库和 gh 登录状态
2. **理解需求**：询问用户想执行的操作类型
3. **提供命令**：给出对应命令，必要时解释参数
4. **确认执行**：危险操作先询问确认
5. **处理结果**：根据输出提供下一步建议
