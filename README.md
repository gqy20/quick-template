# quick-template

一个轻量的多语言项目脚手架 CLI，可生成 Python、Go 和 TypeScript 项目。

## 能力

| 语言 | 运行时 | 包管理 | Lint / 格式化 | 测试 | 可选 API |
|---|---|---|---|---|---|
| Python | 3.13+ | uv | Ruff + Mypy | pytest | FastAPI |
| Go | 1.27+ | Go Modules | golangci-lint | go test | Gin |
| TypeScript | Node.js 24+ | pnpm | Biome | Vitest | Hono |

生成结果统一提供 `make install/check/format/typecheck/test/run`，并包含 GitHub
Actions、Dependabot、Agent 执行契约和前端设计契约。

## 安装

从 GitHub 安装：

```bash
uv tool install git+https://github.com/gqy20/quick-template
```

在本仓库开发时：

```bash
uv sync
uv run quick-template --help
```

## 生成项目

```bash
# Python + FastAPI
quick-template --language python --output-dir ./my-python-app

# Go CLI，不生成 Gin API
quick-template --language golang --no-add-api --output-dir ./my-go-app

# TypeScript + Hono
quick-template --language typescript --output-dir ./my-ts-app

# 附加前端设计基线（DESIGN.md）
quick-template --language python --with-frontend --output-dir ./my-web-app
```

`DESIGN.md` 是一份 300 行的前端视觉与交互契约，只在 `--with-frontend`
时生成；纯后端或 CLI 项目不需要它。

## 交给 Agent 的开场白

新建空项目目录，把下面这段粘给任意编码 Agent，它会自己装工具、选变体、
生成项目，然后按项目自带的契约开始实现。把最后一行的需求换成你要的东西。

```text
用 quick-template 为我在当前目录生成项目，然后按项目自身的契约实现需求。

1. 安装：uv tool install git+https://github.com/gqy20/quick-template
2. 先看真实选项，不要猜：quick-template --help
3. 按需求选变体，在当前目录生成（空目录用 --output-dir .，非空加 --force）：
   quick-template --language <python|golang|typescript> [--no-add-api] [--with-frontend] --output-dir .
4. 安装并自检：make install && make all
5. 读 AGENTS.md，按其中的授权分层、变更门禁、验证阶梯和完成标准继续。

需求：<写在这里>
```

第 2 步让 Agent 读真实选项而不是凭印象编参数；第 5 步把控制权交给
`AGENTS.md`，规则只维护在那里。变体怎么选：

| 需求 | 变体 |
|---|---|
| 只要命令行工具 | `--no-add-api` |
| 需要 HTTP 服务 | 默认（生成 FastAPI / Gin / Hono） |
| 有界面要交付 | 追加 `--with-frontend`，生成 `DESIGN.md` |

可通过 JSON 或 YAML 文件覆盖项目变量：

```json
{
  "project_name": "My Service",
  "description": "Internal service",
  "author_name": "gqy20",
  "author_email": "your.email@example.com",
  "repository_username": "gqy20",
  "license": "MIT"
}
```

```bash
quick-template \
  --language python \
  --data-file project.json \
  --output-dir ./my-service
```

YAML 配置同样可用：

```yaml
project_name: My Service
repository_username: gqy20
author_name: gqy20
line_length: 100
```

可覆盖的变量（未提供的取默认值；`project_slug`、`package_name` 等由这些
自动派生，不需要手写）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `project_name` | `My Project` | 人类可读名称 |
| `description` | `A short description` | 项目描述 |
| `author_name` / `author_email` | 占位值 | 作者信息，也用于派生仓库路径 |
| `repository_username` | 由作者名派生 | GitHub 用户名或组织 |
| `repository_provider` | `https://github.com` | 仓库托管地址 |
| `license` | `MIT` | 许可证标识 |
| `version` | `0.1.0` | 初始版本号 |
| `python_version` / `go_version` / `node_version` | `3.13` / `1.27` / `24` | 运行时版本 |
| `line_length` | `88` | Ruff / Biome 行宽，79–120 |

`add_api` 与 `has_frontend` 也有对应命令行开关，通常直接传 flag 更直观。

## 项目结构

```text
src/scaffold/       # CLI、变量模型和模板引擎
languages/          # Python / Go / TypeScript 专属模板
shared/             # README、CI、Makefile 等公共模板
agent-guide/        # 智能体开发指南（Claude Agent SDK / LangGraph）
tests/              # 生成器单元测试
docs/               # GitHub Pages
```

生成项目中的 `AGENTS.md` 约束 Agent 的授权、范围、安全、验证和完成标准；
`DESIGN.md` 约束语义 Token、布局、组件、响应式、无障碍和 Design QA。

`languages/` 与 `shared/` 是唯一模板源。模板支持变量替换以及
`{{#if ...}}` / `{{#elif ...}}` / `{{#else}}` 条件块。

## 开发与验证

```bash
uv sync
uv run ruff check src tests test_template.py
uv run pytest

# 生成单个项目进行调试
uv run test_template.py python true
```

CI 会验证 Python、Go、TypeScript 各自启用和关闭 API 的 6 种组合。

## Python Agent Runtimes

Python 模板提供两种可选、可对照的 Agent Runtime：

- Claude Agent SDK：`claude-agent-sdk==0.2.176`，使用原生 Agent loop、
  MCP、Skills 与权限。
- LangGraph：`langgraph==1.2.19` + `langchain-anthropic==1.7.7` +
  `langchain-mcp-adapters==0.3.2`，使用显式 StateGraph、原生 `ToolNode`、
  校验重试和 checkpoint。

两者共享：

- `config/prompts/*.yaml` 中立 Prompt。
- `agent_models.py` Pydantic 输出模型。
- `agent_log.py` 脱敏结构化日志。

Claude 使用 `config/agent.yaml` 与 `.mcp.json`；LangGraph 使用
`config/runtimes/langgraph.yaml`，并把同一 `.mcp.json` 转换给官方 MCP
Adapter。LangGraph 工具路径为 `model → ToolNode → model → structured output`，
工具参数与结果正文不会写入默认审计日志。`.mcp.json` 只声明连接，MCP 工具
还必须在 `mcp_allowed_tools` 中按 Adapter 最终名称显式授权；空列表不会连接
任何 MCP Server。工具中的 `interrupt()` 会保留 checkpoint，可用 Runtime 的
`resume()` 和原 thread ID 恢复。LangGraph 示例位于
`examples/langgraph_review.py`，真实模型必须显式传入 `--run`。

Claude CLI 完整 transcript 默认写入临时目录并在运行后删除；需要恢复会话时
可显式切换到 gitignored 的 `.agent-state/claude/`。

安装：

```bash
uv sync --extra agent
uv sync --extra agent-langgraph
```

普通运行和测试保持离线，真实 Agent Demo 必须显式启用。

```bash
uv run --extra agent-langgraph python examples/langgraph_review.py --run
```

## 当前边界

- 默认拒绝写入非空目录；确认需要覆盖时可显式传入 `--force`。
- 自研引擎暂不提供类似 `copier update` 的增量模板合并能力。

## License

[MIT](LICENSE)
