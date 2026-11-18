install:
	go mod tidy

check:
	@test -z "$$(gofmt -l .)" || { echo "未格式化（gofmt -w .）:"; gofmt -l .; exit 1; }
	go vet ./...
	golangci-lint run ./...

format:
	gofmt -w .

typecheck: build

test:
	go test ./... -race -count=1

test-cov:
	go test ./... -race -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html

run:
	go run ./cmd/{{ project_slug }}

clean:
	rm -rf coverage.out coverage.html
	go clean -cache

build:
	go build ./...
