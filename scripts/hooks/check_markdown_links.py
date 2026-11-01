#!/usr/bin/env python3
"""校验 Markdown 内部链接与 @ 引入指向存在的文件。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "#", "mailto:")


def check(paths: list[Path], root: Path) -> list[str]:
    problems: list[str] = []
    for path in paths:
        if path.suffix.lower() not in {".md", ".mdx"}:
            continue
        in_fence = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for target in LINK_RE.findall(line):
                if target.startswith(SKIP_PREFIXES) or "{{" in target:
                    continue
                resolved = (path.parent / target.split("#")[0]).resolve()
                if not resolved.exists():
                    problems.append(f"{path}:{line_number} 链接失效: {target}")
            stripped = line.strip()
            if stripped.startswith("@") and " " not in stripped:
                resolved = (path.parent / stripped[1:]).resolve()
                if not resolved.exists():
                    problems.append(f"{path}:{line_number} 引入失效: {stripped}")
    return problems


def main(argv: list[str]) -> int:
    if not argv:
        return 0
    root = Path.cwd()
    files = []
    for raw in argv:
        path = Path(raw).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        files.append(path)
    problems = check(files, root)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
