# Quick Start Guide

本指南将帮助你快速上手 py_kit 项目。

## 5 分钟快速开始

### 1. 克隆并设置项目

```bash
# 克隆仓库
git clone https://github.com/gqy22/py_kit.git
cd py_kit

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 2. 运行示例程序

```bash
# 查看主程序演示
python -m py_kit.main

# 查看更多示例
python examples/demo.py
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 查看覆盖率
pytest --cov=src/py_kit --cov-report=html
open htmlcov/index.html
```

### 4. 代码质量检查

```bash
# 运行所有检查
python scripts/check.py

# 或单独运行
ruff check .
black --check .
isort --check-only .
```

## 使用日志功能

### 基础用法

```python
from py_kit import logger

logger.info("Application started")
logger.warning("This is a warning")
logger.error("An error occurred")
```

### 创建自定义 Logger

```python
from py_kit.logger import setup_logger
import logging

my_logger = setup_logger(
    name="my_app",
    level=logging.DEBUG,
    log_to_file=True
)

my_logger.debug("Debugging information")
```

### Rich 格式化输出

```python
from py_kit import console, print_success, print_error

print_success("Operation completed!")
print_error("Something went wrong")

# 使用 Rich Console
console.print("[bold green]Success![/bold green]")
```

### 创建表格

```python
from rich.table import Table
from py_kit import console

table = Table(title="Results")
table.add_column("Name", style="cyan")
table.add_column("Value", style="green")
table.add_row("Status", "✓ Success")
console.print(table)
```

## 开发工作流

### 1. 创建新功能

```bash
# 创建分支
git checkout -b feature/my-feature

# 编写代码
# src/py_kit/my_module.py

# 编写测试
# tests/test_my_module.py
```

### 2. 格式化代码

```bash
# 自动格式化
black .
isort .
ruff format .

# 自动修复问题
ruff check --fix .
```

### 3. 运行测试

```bash
# 运行测试
pytest -v

# 查看覆盖率
pytest --cov
```

### 4. 提交代码

```bash
git add .
git commit -m "feat: add new feature"
# pre-commit 会自动运行检查
```

### 5. 推送并创建 PR

```bash
git push origin feature/my-feature
# 在 GitHub 上创建 Pull Request
```

## 发布新版本

### 1. 更新版本号

编辑以下文件：
- `src/py_kit/__init__.py`: `__version__ = "0.2.0"`
- `pyproject.toml`: `version = "0.2.0"`

### 2. 更新 CHANGELOG

在 `CHANGELOG.md` 中添加新版本的更改：

```markdown
## [0.2.0] - 2025-10-22

### Added
- New feature X
- Enhancement Y

### Fixed
- Bug Z
```

### 3. 创建并推送标签

```bash
git add .
git commit -m "chore: bump version to 0.2.0"
git push origin main

git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin v0.2.0
```

### 4. 自动发布

推送标签后，GitHub Actions 会自动：
- ✅ 运行测试
- 📦 构建包
- 🎉 创建 GitHub Release
- 🚀 发布到 PyPI

## 常见任务

### 添加新依赖

1. 编辑 `pyproject.toml`：
```toml
dependencies = [
    "rich>=13.0.0",
    "new-package>=1.0.0",
]
```

2. 重新安装：
```bash
uv pip install -e ".[dev]"
```

### 更新依赖

```bash
# 更新所有包
uv pip install --upgrade -e ".[dev]"

# 更新 pre-commit hooks
pre-commit autoupdate
```

### 清理环境

```bash
# 删除虚拟环境
rm -rf .venv

# 清理缓存
rm -rf .pytest_cache .ruff_cache __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} +

# 重新创建环境
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## 故障排查

### 测试失败

```bash
# 运行单个测试文件
pytest tests/test_logger.py -v

# 运行特定测试
pytest tests/test_logger.py::TestLoggerSetup::test_setup_logger_basic -v

# 查看详细输出
pytest -vv -s
```

### 导入错误

```bash
# 确保以可编辑模式安装
uv pip install -e .

# 检查 Python 路径
python -c "import sys; print('\n'.join(sys.path))"
```

### Pre-commit 失败

```bash
# 手动运行 pre-commit
pre-commit run --all-files

# 跳过 pre-commit（不推荐）
git commit -m "message" --no-verify
```

## 更多资源

- [完整文档](README.md)
- [发布指南](RELEASE.md)
- [变更日志](CHANGELOG.md)
- [示例代码](examples/demo.py)

## 获取帮助

- GitHub Issues: https://github.com/gqy22/py_kit/issues
- 查看测试示例了解用法
- 阅读源码中的文档字符串

---
**开始编码吧！** 🚀
