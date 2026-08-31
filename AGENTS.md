# quick-template development guide

## Architecture

- `src/scaffold/` contains the generator implementation.
- `languages/` and `shared/` are the only active template sources.
- Do not add a second rendered template tree.
- Template syntax is `{{variable}}` plus `{{#if}}`, `{{#elif}}`,
  `{{#else}}`, and `{{#endif}}`.

## Required checks

```bash
uv run ruff check src tests test_template.py
uv run pytest
```

Changes to a language template must also generate and validate both its API
and non-API variants. Keep generated commands aligned with
`.github/workflows/test.yml`.

## Conventions

- Preserve the unified Make targets across languages.
- Add a regression test before changing parser or file-copy behavior.
- Keep optional integrations out of the generator's core dependencies.
- Never edit generated output as the source of truth; edit `languages/` or
  `shared/`.
