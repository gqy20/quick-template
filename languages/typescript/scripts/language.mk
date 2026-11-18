install:
	pnpm install

check:
	pnpm exec biome check .

format:
	pnpm exec biome format --write .

typecheck:
	pnpm exec tsc --noEmit

test:
	pnpm exec vitest run

test-cov:
	pnpm exec vitest run --coverage

run:
	pnpm run dev

clean:
	rm -rf dist/ node_modules/ coverage/

build:
	pnpm run build
