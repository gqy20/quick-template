"""CLI 入口：参数解析、变量构建和脚手架执行。"""

import argparse
from pathlib import Path

from . import __version__
from .files import copy_template_dir
from .variables import ProjectVars


def get_template_root() -> Path:
    """返回 wheel 内模板目录，源码运行时回退到仓库根目录。"""
    package_root = Path(__file__).resolve().parent / "templates"
    if package_root.is_dir():
        return package_root
    return Path(__file__).resolve().parents[2]


def prepare_output_dir(output: Path, force: bool) -> None:
    """创建输出目录，并阻止意外覆盖已有项目。"""
    if output.is_dir() and any(output.iterdir()) and not force:
        raise FileExistsError(f"Output directory is not empty: {output}. Use --force to overwrite.")
    output.mkdir(parents=True, exist_ok=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Multi-language project scaffolding tool")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--language", choices=["python", "golang", "typescript"], default="python")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--data-file", type=Path, default=None)
    p.add_argument("--force", action="store_true", help="overwrite files in a non-empty output")
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
    vars_dict = build_vars(
        args.data_file,
        args.language,
        args.add_api,
        args.output_dir,
    )

    output = args.output_dir or Path.cwd() / vars_dict["project_slug"]
    prepare_output_dir(output, args.force)

    template_root = get_template_root()
    lang_dir = template_root / "languages" / args.language
    shared_dir = template_root / "shared"

    if not lang_dir.is_dir() or not shared_dir.is_dir():
        raise FileNotFoundError(f"Template resources not found in {template_root}")

    if shared_dir.exists():
        copy_template_dir(shared_dir, output, vars_dict)
    if lang_dir.exists():
        copy_template_dir(lang_dir, output, vars_dict)

    print(f"Project generated: {output}")
