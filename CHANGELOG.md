# Changelog

## [Unreleased]

### Added

- 将生成项目的 `AGENTS.md` 扩展为授权、安全、验证和完成标准的执行契约。
- 新增语义 Token、响应式、无障碍和 Design QA 驱动的 `DESIGN.md`。

### Changed

- `CLAUDE.md` 改为指向 `AGENTS.md` 与 `DESIGN.md`，避免重复规则漂移。

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
