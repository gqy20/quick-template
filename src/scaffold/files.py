"""文件处理：模板渲染、目录复制、数据文件加载。"""

import json
from pathlib import Path

from .engine import render

_SKIP_DIRS = {"__pycache__", ".git", ".svn", "node_modules", ".venv"}


def process_file(content: str, vars_dict: dict) -> str:
    """对文件内容执行完整渲染（条件 + 变量）。"""
    return render(content, vars_dict)


def copy_template_dir(src_dir: Path | str, dst_base: Path | str, vars_dict: dict) -> None:
    """递归复制模板目录到目标，处理每个文件的内容和文件名。"""
    src = Path(src_dir)
    dst_base = Path(dst_base)

    for item in sorted(src.rglob("*")):
        if item.is_dir():
            if item.name in _SKIP_DIRS:
                continue
            continue

        rel = item.relative_to(src)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        rendered_parts = [render(str(p), vars_dict) for p in rel.parts]
        dst = dst_base / Path(*rendered_parts)

        dst.parent.mkdir(parents=True, exist_ok=True)
        content = item.read_text(encoding="utf-8")
        rendered = process_file(content, vars_dict)
        if not rendered.strip():
            continue
        dst.write_text(rendered, encoding="utf-8")


def load_data_file(path: Path | str) -> dict:
    """加载 JSON 数据文件。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    with open(p, encoding="utf-8") as f:
        return json.load(f)
