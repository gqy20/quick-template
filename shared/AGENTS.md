# {{ project_name }} agent guide

## Stack

- Language: {{ language }}
- Project commands: `make install`, `make check`, `make typecheck`,
  `make test`
- Comments and user-facing documentation use Chinese; identifiers use
  community-standard English names.

## Working agreement

- Keep changes small and covered by tests.
- Run `make all` before opening a pull request.
- Do not commit secrets or local environment files.
- Update README and CHANGELOG when behavior or public interfaces change.
