# Changelog

## [Unreleased]

### Added

- 将生成项目的 `AGENTS.md` 扩展为授权、安全、验证和完成标准的执行契约。
- 新增语义 Token、响应式、无障碍和 Design QA 驱动的 `DESIGN.md`。
- 新增 Claude Agent SDK 的结构化 JSONL 日志、MCP、Skills 与项目配置。
- 新增版本化 YAML Prompt Registry 和 ephemeral/project/default Session 状态隔离。
- 新增 LangGraph 1.2.11 结构化工作流、离线 Fake Model 测试和显式运行示例。
- 为 LangGraph 增加原生 `ToolNode` 工具循环、MCP Adapter、默认拒绝的 MCP
  工具授权、轮次上限和脱敏工具审计日志。
- 为 Python、Go、TypeScript 模板补齐 pre-commit 提交门禁，包含提交信息
  约定式校验；Python 用 uv、TypeScript 用 pnpm 作为默认包管理器。

### Changed

- `CLAUDE.md` 改为指向 `AGENTS.md` 与 `DESIGN.md`，避免重复规则漂移。
- Claude Agent SDK 升级并固定到 `0.2.148`，普通应用启动不再自动调用模型。
- TypeScript 模板默认包管理器由 npm 改为 pnpm，CI 与 Makefile 同步改用
  `pnpm exec`；Biome 固定到 `2.5.11` 并限定只处理 TS/JS/JSON 文件。
- 模板引擎不再为独占一行的条件标记输出多余空行。

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
