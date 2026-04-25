"""CLI 入口：参数解析和变量构建。"""

import argparse
from pathlib import Path

from .files import load_data_file
from .variables import DEFAULTS, compute_derived


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Multi-language project scaffolding tool")
    p.add_argument("--language", choices=["python", "golang", "typescript"], default="python")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--data-file", type=Path, default=None)
    p.add_argument("--add-api", action="store_true", default=True)
    p.add_argument("--no-add-api", dest="add_api", action="store_false")
    return p.parse_args(argv)


def build_vars(
    data_file: Path | None,
    language: str,
    add_api: bool,
    output_dir: Path | None,
) -> dict:
    """构建完整变量字典：默认值 → 数据文件 → CLI 覆盖 → 派生变量。"""
    vars_dict = dict(DEFAULTS)

    if data_file:
        vars_dict.update(load_data_file(data_file))

    vars_dict["language"] = language
    vars_dict["add_api"] = add_api

    compute_derived(vars_dict)
    return vars_dict
