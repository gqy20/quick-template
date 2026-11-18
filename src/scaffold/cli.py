"""CLI 入口：参数解析、变量构建和脚手架执行。"""

import argparse
import shlex
from pathlib import Path

from . import __version__
from .files import copy_template_dirs
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
    p.add_argument("--language", choices=["python", "golang", "typescript"])
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--data-file", type=Path, default=None)
    p.add_argument("--force", action="store_true", help="overwrite files in a non-empty output")
    p.add_argument("--add-api", action="store_true", default=None)
    p.add_argument("--no-add-api", dest="add_api", action="store_false", default=None)
    p.add_argument(
        "--with-frontend",
        action="store_true",
        default=None,
        help="generate the frontend design baseline (DESIGN.md)",
    )
    p.add_argument("--no-frontend", dest="with_frontend", action="store_false", default=None)
    p.add_argument(
        "--with-agent",
        dest="with_agent",
        action="store_true",
        default=None,
        help="include the Python Claude SDK and LangGraph examples",
    )
    p.add_argument("--no-agent", dest="with_agent", action="store_false", default=None)
    p.add_argument(
        "--with-publish",
        dest="with_publish",
        action="store_true",
        default=None,
        help="include tag-triggered release automation",
    )
    p.add_argument("--no-publish", dest="with_publish", action="store_false", default=None)
    return p.parse_args(argv)


def build_vars(
    data_file: Path | None,
    language: str | None,
    add_api: bool | None,
    has_frontend: bool | None = None,
    with_agent: bool | None = None,
    with_publish: bool | None = None,
) -> dict:
    """构建完整变量字典：默认值 → 数据文件 → CLI 覆盖 → 派生变量。"""
    flags = {"has_frontend": has_frontend, "with_agent": with_agent, "with_publish": with_publish}
    extra = {key: value for key, value in flags.items() if value is not None}
    return ProjectVars.build(data_file, language, add_api, extra).to_dict()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    vars_dict = build_vars(
        args.data_file,
        args.language,
        args.add_api,
        args.with_frontend,
        args.with_agent,
        args.with_publish,
    )

    output = args.output_dir or Path.cwd() / vars_dict["project_slug"]
    prepare_output_dir(output, args.force)

    template_root = get_template_root()
    lang_dir = template_root / "languages" / vars_dict["language"]
    shared_dir = template_root / "shared"

    if not lang_dir.is_dir() or not shared_dir.is_dir():
        raise FileNotFoundError(f"Template resources not found in {template_root}")

    copy_template_dirs((shared_dir, lang_dir), output, vars_dict)

    print(f"Project generated: {output}")
    prefix = (
        "" if output.resolve() == Path.cwd().resolve() else f"cd {shlex.quote(str(output))} && "
    )
    print(f"下一步：{prefix}make install && make all")
    print("然后读 AGENTS.md —— 它是这个项目的执行契约。")
