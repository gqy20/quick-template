# Changelog

## [Unreleased]

### Added

- 将生成项目的 `AGENTS.md` 扩展为授权、安全、验证和完成标准的执行契约。
- 新增 `agent-guide/`，按专题说明如何用脚本调用 Claude Agent SDK 与
  LangGraph，覆盖配置、工具权限、MCP/Skills、Prompt、结构化输出和日志。
- 新增 `--with-frontend`，按需生成语义 Token、响应式、无障碍和 Design QA
  驱动的 `DESIGN.md`。
- 新增模板根目录的 `.template.yml` 分发清单，整文件条件不再靠文件首尾的
  `{{#if}}` 包裹；段落级条件仍用行内标记。
- 生成项目的 Python 模板在启动时加载 `.env`：`.env` 覆盖宿主同名变量，
  并在存在 `ANTHROPIC_API_KEY` 时移除 `ANTHROPIC_AUTH_TOKEN`，避免两种
  认证头冲突与网关地址被宿主环境改写。FastAPI 入口改为读取
  `API_HOST` / `API_PORT` / `DEBUG`。
- 生成项目的 Agent 失败按类型区分：`AgentError` 基类下新增
  `AgentConnectionError`、`AgentProcessError`、`AgentBudgetExceededError`、
  `AgentRateLimitError`，SDK 异常会映射为由 `__cause__` 保留原始错误的
  这些类型。
- 新增 Claude Agent SDK 的结构化 JSONL 日志、MCP、Skills 与项目配置。
- 新增版本化 YAML Prompt Registry 和 ephemeral/project/default Session 状态隔离。
- 新增 LangGraph 1.2.11 结构化工作流、离线 Fake Model 测试和显式运行示例。
- 为 LangGraph 增加原生 `ToolNode` 工具循环、MCP Adapter、默认拒绝的 MCP
  工具授权、轮次上限和脱敏工具审计日志。
- 为 Python、Go、TypeScript 模板补齐 pre-commit 提交门禁，包含提交信息
  约定式校验；Python 用 uv、TypeScript 用 pnpm 作为默认包管理器。

### Changed
- `agent-guide/` 新增沙箱专题：模型与工具的边界、策略取舍，以及并行
  工具调用的写后读竞态和环境变量改写模型流量两个故障的成因与修法。

- `CLAUDE.md` 不再复述规则，改为只用 `@` 引入 `AGENTS.md`。
- Claude Agent SDK 固定到 `0.2.176`，LangGraph 到 `1.2.19`、
  `langchain-anthropic` 到 `1.7.7`；普通应用启动不再自动调用模型。
- TypeScript 模板默认包管理器由 npm 改为 pnpm，CI 与 Makefile 同步改用
  `pnpm exec`；Biome 升到 `2.6.4` 并限定只处理 TS/JS/JSON 文件。
- TypeScript 模板的 Vitest 与覆盖率插件升到 5、tsup 升到 9；构建改为
  显式入口与 ESM 输出，修正 `main` 指向 `dist/index.js` 但产物是
  `dist/index.cjs` 的不一致。
- Go 模板的 Gin 升到 `v1.12.0`、cors 到 `v1.7.10`；CI 的 golangci-lint
  升到 `v2.15.0`。
- 根仓库依赖刷新：mypy `2.4.1`、ruff `0.17.3`、pytest `9.2.0`、
  pytest-bdd `9.0.1`、pydantic `2.14.2`；ruff pre-commit hook 同步到
  `v0.17.3`。
- 模板引擎不再为独占一行的条件标记输出多余空行。
- 生成项目的 `permission_mode` 补上 SDK 支持的 `auto`，并修正各模式的
  说明：`dontAsk` 是自动拒绝而非直接失败，`plan` 允许只读命令，
  `bypassPermissions` 仍有任何模式都不自动批准的动作。
- CI 增加 workflow 静态检查（含 shellcheck），并验证生成项目的提交门禁
  能安装、能拦截非法提交信息；生成矩阵加入 `--with-frontend` 维度。
- `DESIGN.md` 默认不再生成，只有 `--with-frontend` 时输出；相关的契约
  引用同步按条件渲染。
- `CHANGELOG.md` 与 `PRODUCT.md` 移入 `docs/`，根目录只保留每次工作都要
  读的契约。验收证据归入编号专题，取消独立的 design-qa 路径。
### Removed

- 删除仓库根的 `examples/claude_agent.py` 与 `examples/prompts/`。它是模板化
  之前的独立 Claude Agent SDK 封装原型，没有测试、没有文档引用，版本也停在
  `0.2.148`；其中可迁移的错误分类已并入模板的 `agent.py`。


## [0.3.0] - 2026-08-31

### Changed

- 完成从 Copier 到自研脚手架引擎的迁移。
- 将 `languages/` 与 `shared/` 设为唯一模板源。
- 更新 Python、Go、TypeScript 工具链与 GitHub Actions。

### Added

- wheel 内置模板资源及安装冒烟测试。
- JSON/YAML 项目配置。
- 项目字段校验、稳定 slug 和非空输出目录保护。
- 通用 `AGENTS.md` 与 MIT License。

### Removed

- 旧 Copier `template/` 目录。
- 过期的 Python 专属共享文档。
