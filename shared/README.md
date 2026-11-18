# {{ project_name }}

{{ description }}

[源码仓库]({{ repository_provider }}/{{ repository_username }}/{{ project_slug }})

## 快速开始

{{#if language == 'python'}}
需要 Python {{ python_version }}+ 和 uv。
{{#elif language == 'golang'}}
需要 Go {{ go_version }}+，`make check` 使用 PATH 中的 golangci-lint v2.15.0。
{{#elif language == 'typescript'}}
需要 Node.js {{ node_version }}+ 和 pnpm。
{{#endif}}

在项目根目录运行：

```bash
make install
make all
make run
```

使用 `make build` 构建，`make help` 查看其他目标。初始化或克隆 Git 仓库后，执行以下命令启用提交检查：

```bash
{{#if language == 'python'}}
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
{{#else}}
pre-commit install --hook-type pre-commit --hook-type commit-msg
{{#endif}}
```
{{#if language != 'python'}}
此步骤需要已安装 [pre-commit](https://pre-commit.com)。
{{#endif}}

{{#if language == 'typescript'}}
{{#if add_api}}
本地 HTTP 服务的健康检查地址为 `http://127.0.0.1:3000/api/v1/health`。
可通过 `PORT` 指定端口。

{{#endif}}
{{#endif}}
{{#if with_agent}}
## Agent Runtimes（可选）

Claude Agent SDK：

```bash
uv sync --extra agent
```

LangGraph：

```bash
uv sync --extra agent-langgraph
```

共享契约：

- `config/prompts/*.yaml`：有版本和变量契约的 Runtime-neutral Prompt。
- `src/{{ package_name }}/agent_models.py`：共享 Pydantic 输出。
- `src/{{ package_name }}/agent_log.py`：共享脱敏 JSONL 日志。

Claude 原生入口：

- `config/agent.yaml`：模型、工具、权限、MCP/Skills、日志和状态模式。
- `.mcp.json`：Claude Code 原生 MCP server 配置。
- `.claude/skills/<name>/SKILL.md`：项目 Skills。
- `logs/agent/events.jsonl`：脱敏后的结构化 Agent 执行日志。
- `.agent-state/claude/`：仅在持久 Session 模式使用的完整 transcript。

LangGraph 入口：

- `config/runtimes/langgraph.yaml`：模型、工具轮次、MCP 授权、超时和 checkpoint。
- `src/{{ package_name }}/langgraph_agent.py`：显式结构化 StateGraph 与原生
  `ToolNode` 循环。
- `src/{{ package_name }}/langgraph_tools.py`：把共享 `.mcp.json` 连接配置交给
  `langchain-mcp-adapters`，不自行实现 MCP 协议。
- `examples/langgraph_review.py`：默认离线、显式 `--run` 的对照示例。

真实运行：

```bash
uv run --extra agent-langgraph python examples/langgraph_review.py --run
```

LangGraph 中，程序显式传入的本地 `BaseTool` 视为代码授权；MCP Server 配置
不等于工具授权。`mcp_allowed_tools` 默认为 `[]`，此时不会连接 MCP；启用
`tool_name_prefix` 后，授权名称使用 Adapter 暴露的 `server_tool` 形式。
工具调用只记录名称、参数键、状态、耗时和异常类型，不记录参数值或结果正文。
工具通过 `interrupt()` 暂停后，使用 `runtime.resume(thread_id, value, Model)`
从内存 checkpoint 恢复；进程重启恢复需要把默认 checkpointer 换成持久实现。

Claude 的 `skills` 使用 SDK 原生精确名称过滤；MCP 使用原生配置路径。
默认禁用内置工具和 Skills，permission mode 为 `dontAsk`。
普通 `main` 保持离线；只有显式运行 `python -m {{ package_name }}.main --agent-demo`
才会调用真实 Claude。

默认 `runtime_state.mode: ephemeral`，每次运行使用临时
`CLAUDE_CONFIG_DIR` 并在结束后删除。需要 resume 时改为 `project`；
只有明确需要沿用 Claude Code 用户登录和全局设置时才使用 `default`。

{{#endif}}
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
{{#if add_api}}│   ├── handler/
{{#endif}}│   ├── service/
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
│   ├── api/router.ts
│   └── server.ts
{{#else}}│   └── cli.ts
{{#endif}}
├── tests/
├── package.json
├── tsconfig.json
{{#endif}}
├── docs/                # 专题文档：产品边界、版本变化、专题索引
├── Makefile
├── AGENTS.md
{{#if has_frontend}}├── DESIGN.md
{{#endif}}└── README.md
```

## 代码规范

注释和文档使用中文，函数和类型使用英文命名。
{{#if language == 'python'}}Python 函数使用类型注解，文档字符串采用 Google 风格。
{{#endif}}

{{#if with_publish}}
## 发布

{{#if language == 'python'}}
在 PyPI 配置本仓库的 Trusted Publisher，工作流文件为 `publish.yml`、环境为 `pypi`。
推送与包版本一致的 `vX.Y.Z` 标签后，工作流上传 wheel 和 sdist，再将同一批文件附到 GitHub Release。
{{#elif language == 'typescript'}}
在 GitHub 的 `npm` 环境配置可发布此包的 `NPM_TOKEN`，并核对 package.json 的仓库地址。
推送与包版本一致的 `vX.Y.Z` 标签后，工作流将构建好的 tarball 公开发布到 npm，再附到 GitHub Release。
{{#else}}
推送 `vX.Y.Z` 标签会创建 GitHub Release，并使用提交历史生成版本说明。
{{#endif}}

{{#endif}}
## 许可证

{{ license }}

Copyright © {{ copyright_date }} {{ author_name }}
