# {{ project_name }} - Claude Code 指令

## 项目概述

{% if language == 'python' -%}
- **语言**: Python {{ python_version }}+
- **包管理**: uv（极速包管理器）
- **项目结构**: src layout
- **代码规范**: ruff（检查 + 格式化）
- **测试框架**: pytest
- **日志系统**: rich

{%- elif language == 'golang' -%}
- **语言**: Go {{ go_version }}+
- **包管理**: go mod
- **项目结构**: cmd / internal / pkg (标准 Go 布局)
- **代码规范**: golangci-lint
- **测试框架**: go test
- **日志系统**: log/slog

{%- elif language == 'typescript' -%}
- **语言**: TypeScript (Node.js {{ node_version }}+)
- **包管理**: npm
- **代码规范**: Biome（lint + format）
- **测试框架**: vitest
- **构建工具**: tsup
- **日志系统**: 自定义 console 封装

{%- endif %}

## 常用命令

```bash
# 安装依赖
make install

# 代码检查
make check

# 格式化
make format

# 测试
make test
make test-cov

# 运行所有检查
make all

# 运行项目
make run
```

## 代码规范

1. **语言**: 所有注释、文档字符串使用中文
2. **命名**: 函数和类使用英文
3. **类型注解**: 必需
4. **文档字符串**: Google 风格中文文档
5. **提交规范**: feat/fix/docs/refactor/test/chore

{% if add_api -%}
## API 开发

{% if language == 'python' -%}
```bash
# 启动 FastAPI 服务器
.venv/bin/python -m {{ package_name }}.api
```
{%- elif language == 'golang' -%}
```bash
# 启动 Gin 服务器
go run ./cmd/{{ project_slug }}
```
{%- elif language == 'typescript' -%}
```bash
# 启动 Hono 开发服务器
npm run dev
```
{%- endif %}
{%- endif %}

## 项目结构

{% if language == 'python' -%}
```
src/{{ package_name }}/
├── __init__.py    # 包初始化，导出公共 API
├── core.py        # 核心功能
├── logger.py      # 日志系统
{% if add_api -%}
├── api.py         # FastAPI 应用
{%- endif %}
└── main.py        # 主程序入口
```
{%- elif language == 'golang' -%}
```
cmd/{{ project_slug }}/
└── main.go           # 入口
internal/
├── handler/          # HTTP handler (Gin)
├── service/          # 业务逻辑
└── model/            # 数据模型
pkg/logger/            # 日志库
```
{%- elif language == 'typescript' -%}
```
src/
├── index.ts          # 入口导出
├── core.ts           # 核心功能
├── logger.ts         # 日志模块
{% if add_api -%}
└── api/router.ts     # Hono 路由
{%- endif %}
```
{%- endif %}
