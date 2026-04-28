"""CLI 入口：参数解析、变量构建和脚手架执行。"""

import argparse
from pathlib import Path

from .files import copy_template_dir
from .variables import ProjectVars

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent


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
    return ProjectVars.build(data_file, language, add_api).to_dict()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    vars_dict = build_vars(args.data_file, args.language, args.add_api, args.output_dir)

    output = args.output_dir or Path.cwd() / vars_dict["project_slug"]
    output.mkdir(parents=True, exist_ok=True)

    lang_dir = TEMPLATE_ROOT / "languages" / args.language
    shared_dir = TEMPLATE_ROOT / "shared"

    if shared_dir.exists():
        copy_template_dir(shared_dir, output, vars_dict)
    if lang_dir.exists():
        copy_template_dir(lang_dir, output, vars_dict)

    print(f"Project generated: {output}")
