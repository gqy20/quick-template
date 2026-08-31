# quick-template

一个轻量的多语言项目脚手架 CLI，可生成 Python、Go 和 TypeScript 项目。

## 能力

| 语言 | 运行时 | 包管理 | Lint / 格式化 | 测试 | 可选 API |
|---|---|---|---|---|---|
| Python | 3.13+ | uv | Ruff + Mypy | pytest | FastAPI |
| Go | 1.27+ | Go Modules | golangci-lint | go test | Gin |
| TypeScript | Node.js 24+ | npm | Biome | Vitest | Hono |

生成结果统一提供 `make install/check/format/typecheck/test/run`，并包含 GitHub
Actions、Dependabot、项目文档和 Agent 开发指令。

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
```

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

## 项目结构

```text
src/scaffold/       # CLI、变量模型和模板引擎
languages/          # Python / Go / TypeScript 专属模板
shared/             # README、CI、Makefile 等公共模板
tests/              # 生成器单元测试
docs/               # GitHub Pages
```

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

## 当前边界

- 默认拒绝写入非空目录；确认需要覆盖时可显式传入 `--force`。
- 自研引擎暂不提供类似 `copier update` 的增量模板合并能力。

## License

[MIT](LICENSE)
