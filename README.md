# quick-template

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-orange.json)](https://github.com/copier-org/copier)

> 多语言项目模板 - 支持 Python / Go / TypeScript，基于 Copier 秒级生成规范项目

一个专业的多语言项目脚手架模板，使用 [Copier](https://copier.readthedocs.io/) 生成规范化的项目。

## 支持的语言

| 语言 | 包管理 | Lint | 测试 | API 框架 |
|------|--------|------|------|----------|
| **Python** | uv | ruff | pytest | FastAPI |
| **Go** | go mod | golangci-lint | go test | Gin |
| **TypeScript** | npm | Biome | vitest | Hono |

## 特性

- 🌍 **多语言** - 一套模板支持 Python / Go / TypeScript
- 📦 **现代工具链** - 每种语言使用当前最佳工具
- 🏗️ **标准结构** - 遵循各语言社区推荐的项目布局
- ⚡ **统一命令** - `make install/check/test/run` 跨语言一致
- 🔄 **CI/CD** - GitHub Actions 自动化
- 🤖 **AI 友好** - 内置 Claude Code 指令配置
- 🔄 **模板更新** - 支持从模板合并更新

## 快速开始

### 安装 Copier

```bash
pip install copier
# 或
uv tool install copier
```

### 创建项目

```bash
# 从 GitHub 创建（推荐）
copier copy gh:gqy20/quick-template my-project

# 选择语言后自动生成对应的项目结构
```

Copier 会交互式询问：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `language` | 编程语言 | python |
| `project_name` | 项目名称 | My Project |
| `add_api` | 添加 API 示例 | true |
| `add_cli` | 添加 CLI 示例 | false |
| `license` | 开源协议 | MIT |

## 生成的项目结构

### Python 项目
```
my-project/
├── src/my_package/        # 源代码（src layout）
├── tests/                 # pytest 测试
├── pyproject.toml         # 项目配置（uv + ruff）
└── Makefile               # 统一构建命令
```

### Go 项目
```
my-project/
├── cmd/myapp/main.go      # 入口点
├── internal/              # 私有代码
│   ├── handler/           # HTTP handler (Gin)
│   ├── service/           # 业务逻辑
│   └── model/             # 数据模型
├── pkg/logger/            # 可导出库
├── tests/                 # 表驱动测试
├── go.mod                 # 模块定义
└── Makefile
```

### TypeScript 项目
```
my-project/
├── src/                   # 源码（ESM）
│   ├── index.ts           # 入口
│   ├── core.ts            # 核心功能
│   └── api/router.ts      # Hono 路由（可选）
├── tests/                 # vitest 测试
├── package.json           # npm 配置（Biome + vitest）
├── tsconfig.json          # TypeScript 配置
└── Makefile
```

## 统一的 Make 命令

无论选择哪种语言，都使用相同的命令接口：

```bash
make install    # 安装依赖
make check      # 代码检查
make format     # 格式化
make typecheck   # 类型检查
make test       # 运行测试
make test-cov   # 测试 + 覆盖率
make run        # 运行项目
make clean      # 清理缓存
make all        # 全量检查
```

## 模板更新

```bash
cd my-project
copier update
```

## 开发

查看 [CLAUDE.md](.claude/CLAUDE.md) 了解模板开发规范。

## 许可证

MIT

Copyright © {{ now().year }} gqy20

---

**GitHub:** https://github.com/gqy20/quick-template
