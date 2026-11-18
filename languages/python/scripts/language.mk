install:
	uv sync --all-groups{{#if with_agent}} --all-extras{{#endif}}

check:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

typecheck:
	uv run{{#if with_agent}} --all-extras{{#endif}} mypy src/{{ package_name }}

test:
	uv run{{#if with_agent}} --all-extras{{#endif}} pytest

test-cov:
	uv run{{#if with_agent}} --all-extras{{#endif}} pytest --cov=src/{{ package_name }} --cov-report=html

run:
	{{#if add_api}}uv run python -m {{ package_name }}.api{{#else}}uv run python -m {{ package_name }}.main{{#endif}}

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ build/ *.egg-info .venv .mypy_cache .ruff_cache

build:
	uv build
