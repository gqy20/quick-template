# Changelog

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
