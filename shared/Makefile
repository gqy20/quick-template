.DEFAULT_GOAL := install
.PHONY: install check format typecheck test test-cov build run clean all help

include scripts/language.mk

all: check typecheck test

help:
	@echo "常用命令:"
	@echo "  make install    - 安装依赖"
	@echo "  make check      - 代码检查"
	@echo "  make format     - 格式化代码"
	@echo "  make typecheck  - 类型检查"
	@echo "  make test       - 运行测试"
	@echo "  make test-cov   - 测试 + 覆盖率"
	@echo "  make build      - 构建项目"
	@echo "  make run        - 运行项目"
	@echo "  make clean      - 清理缓存"
	@echo "  make all        - 检查 + 类型检查 + 测试"
