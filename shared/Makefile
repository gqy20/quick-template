.PHONY: install check format test test-cov clean all help

# ---- 安装 ----
install:
{{#if language == 'python'}}
	uv venv
	uv sync --all-dev
	uv run pre-commit install
{{#elif language == 'golang'}}
	go mod download
{{#elif language == 'typescript'}}
	npm install
{{#endif}}

# ---- 代码检查 ----
check:
{{#if language == 'python'}}
	uv run ruff check .
{{#elif language == 'golang'}}
	golangci-lint run ./...
	go vet ./...
{{#elif language == 'typescript'}}
	npx biome check .
{{#endif}}

# ---- 格式化 ----
format:
{{#if language == 'python'}}
	uv run ruff format .
{{#elif language == 'golang'}}
	gofmt -w .
	goimports -w .
{{#elif language == 'typescript'}}
	npx biome format --write .
{{#endif}}

# ---- 类型检查 ----
typecheck:
{{#if language == 'python'}}
	uv run mypy src/{{ package_name }}
{{#elif language == 'golang'}}
	go build ./...
{{#elif language == 'typescript'}}
	npx tsc --noEmit
{{#endif}}

# ---- 测试 ----
test:
{{#if language == 'python'}}
	uv run pytest
{{#elif language == 'golang'}}
	go test ./... -race -count=1
{{#elif language == 'typescript'}}
	npx vitest run
{{#endif}}

test-cov:
{{#if language == 'python'}}
	uv run pytest --cov=src/{{ package_name }} --cov-report=html
{{#elif language == 'golang'}}
	go test ./... -race -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
{{#elif language == 'typescript'}}
	npx vitest run --coverage
{{#endif}}

# ---- 运行 ----
run:
{{#if language == 'python'}}
	{{#if add_api}}uv run python -m {{ package_name }}.api{{#else}}uv run python -m {{ package_name }}.main{{#endif}}
{{#elif language == 'golang'}}
	go run ./cmd/{{ project_slug }}
{{#elif language == 'typescript'}}
	npm run dev
{{#endif}}

# ---- 清理 ----
clean:
{{#if language == 'python'}}
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info .venv .mypy_cache .ruff_cache
{{#elif language == 'golang'}}
	rm -rf coverage.out coverage.html
	go clean -cache
{{#elif language == 'typescript'}}
	rm -rf dist/ node_modules/ coverage/
{{#endif}}

# ---- 全量检查 ----
all: check typecheck test

help:
	@echo "常用命令:"
	@echo "  make install    - 安装依赖"
	@echo "  make check      - 代码检查"
	@echo "  make format     - 格式化代码"
	@echo "  make typecheck  - 类型检查"
	@echo "  make test       - 运行测试"
	@echo "  make test-cov   - 测试 + 覆盖率"
	@echo "  make run        - 运行项目"
	@echo "  make clean      - 清理缓存"
	@echo "  make all        - 检查 + 类型检查 + 测试"
