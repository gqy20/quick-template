"""文件处理：模板渲染、目录复制、数据文件加载。"""

import json
from pathlib import Path
from typing import Any

import yaml

from .engine import evaluate_condition, render

_SKIP_DIRS = {"__pycache__", ".git", ".svn", "node_modules", ".venv"}
MANIFEST_NAME = ".template.yml"


def process_file(content: str, vars_dict: dict) -> str:
    """对文件内容执行完整渲染（条件 + 变量）。"""
    return render(content, vars_dict)


def load_manifest(src: Path, vars_dict: dict) -> dict[str, bool]:
    """读取模板根目录的分发清单，返回「相对路径 → 是否生成」。

    清单格式：

        files:
          DESIGN.md: has_frontend
          "src/{{package_name}}/api.py": add_api

    路径支持模板变量，值是与模板语法一致的条件表达式。未列出的文件始终生成。
    """
    path = src / MANIFEST_NAME
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    files = data.get("files") or {}
    if not isinstance(files, dict):
        raise ValueError(f"{path}: 'files' must be a mapping")
    resolved: dict[str, bool] = {}
    for raw_path, condition in files.items():
        if not isinstance(raw_path, str) or not isinstance(condition, str):
            raise ValueError(f"{path}: file entries must map a path to a condition")
        resolved[render(raw_path, vars_dict)] = evaluate_condition(condition, vars_dict)
    return resolved


def copy_template_dir(src_dir: Path | str, dst_base: Path | str, vars_dict: dict) -> None:
    """递归复制模板目录到目标，处理每个文件的内容和文件名。"""
    src = Path(src_dir)
    dst_base = Path(dst_base)
    manifest = load_manifest(src, vars_dict)
    seen: set[str] = set()

    for item in sorted(src.rglob("*")):
        if item.is_dir():
            if item.name in _SKIP_DIRS:
                continue
            continue

        rel = item.relative_to(src)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        if rel.name == MANIFEST_NAME:
            continue
        rendered_parts = [render(str(p), vars_dict) for p in rel.parts]
        rel_key = Path(*rendered_parts).as_posix()
        if rel_key in manifest:
            seen.add(rel_key)
            if not manifest[rel_key]:
                continue
        dst = dst_base / Path(*rendered_parts)

        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            content = item.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            dst.write_bytes(item.read_bytes())
            continue
        rendered = process_file(content, vars_dict)
        if not rendered.strip():
            continue
        dst.write_text(rendered, encoding="utf-8")

    missing = sorted(set(manifest) - seen)
    if missing:
        raise ValueError(f"{src / MANIFEST_NAME} 列出但不存在: {missing}")


def load_data_file(path: Path | str) -> dict[str, Any]:
    """加载 JSON 或 YAML 数据文件。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Data file not found: {p}")
    with open(p, encoding="utf-8") as file:
        if p.suffix.lower() == ".json":
            data = json.load(file)
        elif p.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(file)
        else:
            raise ValueError(f"Unsupported data file format: {p.suffix}")

    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError("Project configuration must be a mapping")
    return data
