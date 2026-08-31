# {{ project_name }}

{{ description }}

[![CI]({{ repository_provider }}/{{ repository_username }}/{{ project_slug }}/actions/workflows/ci/badge.svg)]({{ repository_provider }}/{{ repository_username }}/{{ project_slug }}/actions)
{{#if language == 'python'}}
[![Python {{ python_version }}+](https://img.shields.io/badge/python-{{ python_version }}+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
{{#elif language == 'golang'}}
[![Go {{ go_version }}+](https://img.shields.io/badge/go-{{ go_version }}+%2300ADD8.svg)](https://go.dev/dl/)
[![golangci-lint](https://golangci-lint.run/badges/github.com/{{ repository_username }}/{{ project_slug }}.svg?style=flat)](https://golangci-lint.run/r/{{ repository_username }}/{{ project_slug }})
{{#elif language == 'typescript'}}
[![Node.js {{ node_version }}+](https://img.shields.io/badge/node-{{ node_version }}+%23339933.svg)](https://nodejs.org/)
[![Biome](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/biomejs/main/packages/website/static/img/badge_v2.json)](https://biomejs.dev/)
{{#endif}}

## 概述

{{#if language == 'python'}}
现代 Python 项目脚手架，使用 `uv` + `ruff` + `rich` 构建。
{{#elif language == 'golang'}}
现代 Go 项目脚手架，使用 `Gin` + `go mod` + `golangci-lint` 构建。
{{#elif language == 'typescript'}}
现代 TypeScript 项目脚手架，使用 `npm` + `Biome` + `vitest` 构建。
{{#endif}}

**核心特性：**
{{#if language == 'python'}}
- 📦 **uv** - 极速包管理器
- 🏗️ **src layout** - 标准项目结构
- ⚡ **ruff** - 代码检查和格式化
- ✅ **pytest** - 测试框架
- 📝 **rich** - 美观的日志和终端输出
- 🪝 **pre-commit** - 提交前检查
{{#elif language == 'golang'}}
- ⚡ **Go** - 高性能编译型语言
- 🌐 **Gin** - 高性能 Web 框架
- 🧰 **标准库 CLI** - 简洁、零额外依赖
- 🔍 **golangci-lint** - 一站式代码检查
- 📊 **slog** - 结构化日志
{{#elif language == 'typescript'}}
- 📦 **npm** - 包管理器
- ⚡ **Biome** - 代码检查和格式化（替代 ESLint + Prettier）
- ✅ **vitest** - 极速测试框架
- 🎯 **TypeScript** - 严格类型安全
- 📦 **tsup** - 轻量打包工具
{{#endif}}
- 🔄 **CI/CD** - GitHub Actions
{{#if add_api}}
{{#if language == 'python'}}
- 🚀 **FastAPI** - Web 开发示例
{{#elif language == 'golang'}}
- 🚀 **Gin** - Web API 示例
{{#elif language == 'typescript'}}
- 🚀 **Hono** - 轻量 Web 框架示例
{{#endif}}
{{#endif}}

{{#if language == 'python'}}
## Claude Agent SDK（可选）

安装可选依赖：

```bash
uv sync --extra agent
```

原生配置入口：

- `config/agent.yaml`：模型、工具、权限、MCP/Skills、日志和状态模式。
- `config/prompts/*.yaml`：有版本和变量契约的 Prompt。
- `.mcp.json`：Claude Code 原生 MCP server 配置。
- `.claude/skills/<name>/SKILL.md`：项目 Skills。
- `logs/agent/events.jsonl`：脱敏后的结构化 Agent 执行日志。
- `.agent-state/claude/`：仅在持久 Session 模式使用的完整 transcript。

`skills` 使用 SDK 原生精确名称过滤；MCP 使用 `mcp_servers` 原生配置路径。
默认禁用内置工具和 Skills，permission mode 为 `dontAsk`，不会自动批准未知操作。
普通 `main` 保持离线；只有显式运行 `python -m {{ package_name }}.main --agent-demo`
才会调用真实 Claude。

默认 `runtime_state.mode: ephemeral`，每次运行使用临时
`CLAUDE_CONFIG_DIR` 并在结束后删除。需要 resume 时改为 `project`；
只有明确需要沿用 Claude Code 用户登录和全局设置时才使用 `default`。

{{#endif}}
## 快速开始

**前置要求：**
{{#if language == 'python'}}
- Python {{ python_version }}+
- [uv](https://github.com/astral-sh/uv)
{{#elif language == 'golang'}}
- Go {{ go_version }}+
{{#elif language == 'typescript'}}
- Node.js {{ node_version }}+
- npm
{{#endif}}

```bash
# 克隆项目
git clone {{ repository_provider }}/{{ repository_username }}/{{ project_slug }}.git
cd {{ project_slug }}

# 安装依赖
make install

# 运行测试
make test
```

## 项目结构

```
{{ project_slug }}/
{{#if language == 'python'}}
├── src/{{ package_name }}/
│   ├── __init__.py
│   ├── core.py
│   ├── logger.py
{{#if add_api}}
│   ├── api.py
{{#endif}}
│   └── main.py
├── tests/
├── pyproject.toml
{{#elif language == 'golang'}}
├── cmd/{{ project_slug }}/
│   └── main.go
├── internal/
│   ├── handler/
│   ├── service/
│   └── model/
├── pkg/logger/
├── tests/
├── go.mod
{{#elif language == 'typescript'}}
├── src/
│   ├── index.ts
│   ├── core.ts
│   ├── logger.ts
{{#if add_api}}
│   └── api/router.ts
{{#endif}}
├── tests/
├── package.json
├── tsconfig.json
{{#endif}}
├── docs/
├── Makefile
├── AGENTS.md
├── DESIGN.md
└── README.md
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `make install` | 安装依赖 |
| `make check` | 代码检查 |
| `make format` | 格式化代码 |
| `make typecheck` | 类型检查 |
| `make test` | 运行测试 |
| `make test-cov` | 测试 + 覆盖率报告 |
| `make run` | 运行项目 |
| `make clean` | 清理缓存 |

## 代码规范

1. **语言**：注释和文档使用**中文**
2. **命名**：函数和类使用英文
3. **类型注解**：必需
4. **文档字符串**：Google 风格

## 许可证

{{ license }}

Copyright © {{ copyright_date }} {{ author_name }}
