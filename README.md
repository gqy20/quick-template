# quick-template

用 `quick-template` 生成 Python、Go 和 TypeScript 项目。

## 能力

| 语言 | 运行时 | 包管理 | Lint / 格式化 | 测试 | 可选 API |
|---|---|---|---|---|---|
| Python | 默认 3.13，最低 3.11 | uv | Ruff + Mypy | pytest | FastAPI |
| Go | 1.27+ | Go Modules | golangci-lint | go test | Gin |
| TypeScript | Node.js 24+ | pnpm | Biome | Vitest | Hono |

Go 项目的 `make check` 需要 PATH 中有 golangci-lint v2.15.0。

## 安装

生成器需要 Python 3.11 或更高版本。

从 GitHub 安装：

```bash
uv tool install git+https://github.com/gqy20/quick-template
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

## 交给 Agent 的开场白

在空目录中，将以下提示的最后一行替换为实际需求：

```text
用 quick-template 为我在当前目录生成项目，然后按项目自身的契约实现需求。

1. 安装：uv tool install git+https://github.com/gqy20/quick-template
2. 运行 quick-template --help，根据需求选语言和开关，用 --output-dir . 在当前目录生成项目。
3. 阅读生成的 AGENTS.md，执行 make install && make all，再实现需求。

需求：<写在这里>
```

## 生成选项与配置

| 需求 | CLI | 配置字段与默认值 |
|---|---|---|
| 选择语言 | `--language` | `language: python` |
| HTTP 服务或单次运行的 CLI | `--add-api` / `--no-add-api` | `add_api: true` |
| 生成前端设计规范 `DESIGN.md` | `--with-frontend` / `--no-frontend` | `has_frontend: false` |
| 加入 Claude SDK、LangGraph 示例和测试（仅 Python） | `--with-agent` / `--no-agent` | `with_agent: false` |
| 用版本标签发布到 PyPI、npm 或创建 Go 的 GitHub Release | `--with-publish` / `--no-publish` | `with_publish: false` |

`--data-file` 接受 JSON 或 YAML。显式 CLI 参数优先于文件值，省略的字段使用默认值。
例如，将以下配置保存为 `project.yaml`，执行 `quick-template --data-file project.yaml --output-dir ./my-service`：

```yaml
project_name: My Service
repository_username: gqy20
author_name: gqy20
line_length: 100
```

| 变量 | 默认 | 说明 |
|---|---|---|
| `project_name` | `My Project` | 人类可读名称 |
| `description` | `A short description` | 项目描述 |
| `author_name` / `author_email` | 占位值 | 作者信息，也用于派生仓库路径 |
| `repository_username` | 由作者名派生 | GitHub 用户名或组织 |
| `repository_provider` | `https://github.com` | 仓库托管地址 |
| `license` | `MIT` | 当前仅支持 MIT，与生成的 LICENSE 正文一致 |
| `version` | `0.1.0` | 初始版本号 |
| `python_version` / `go_version` / `node_version` | `3.13` / `1.27` / `24` | 运行时版本 |
| `line_length` | `88` | Ruff / Biome 行宽，79–120 |

Python 的导入名会避开关键字，例如项目名 `Class` 派生为 `project_class`。
Go 模块路径由仓库主机、命名空间和项目 slug 组成，例如 `gitlab.com/acme/team/my-service`。
仓库 URL 可自定义，生成的自动化使用 GitHub Actions。

## 项目结构

```text
src/scaffold/       # CLI、变量模型和模板引擎
languages/          # Python / Go / TypeScript 专属模板
shared/             # README、CI、Makefile 等公共模板
agent-guide/        # 智能体开发指南（Claude Agent SDK / LangGraph）
tests/              # 生成器单元测试
docs/               # GitHub Pages
```

## 开发与验证

```bash
uv sync
uv run quick-template --help
uv run ruff check src tests test_template.py
uv run pytest

# 生成单个项目进行调试
uv run test_template.py python true
```

CI 对生成器运行 Ruff、Mypy 和 pytest，并通过真实 CLI 验证 Python、Go、TypeScript 各自启用和关闭 API 的 6 种组合。

## Python Agent Runtimes

生成 Python 项目时加 `--with-agent`，普通启动与测试默认离线。两套运行时的选型、配置及调用示例见 [Agent 开发指南](agent-guide/)。

## 当前边界

- 默认拒绝写入非空目录；确认需要覆盖时可显式传入 `--force`。
- 写入前检查共享与语言模板的目标路径，指向输出目录外的符号链接会使生成失败。
- `--force` 只覆盖同名文件。要查看另一种变体的完整输出，请生成到新目录。

## License

[MIT](LICENSE)
