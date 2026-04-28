#!/usr/bin/env python3
"""测试 quick-template 模板生成。CI 中通过 uv run 调用。"""

import sys
import tempfile
from pathlib import Path

from scaffold.files import copy_template_dir
from scaffold.variables import ProjectVars

TEMPLATE_ROOT = Path(__file__).resolve().parent


def test_generate(language: str, add_api: bool = True, add_cli: bool = False) -> Path:
    """使用 scaffold 引擎生成项目。"""
    extra = {
        "project_name": "Test Project",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "description": "A test project",
        "version": "0.1.0",
        "license": "MIT",
        "line_length": 88,
    }
    if language == "python":
        extra["python_version"] = "3.13"
    elif language == "golang":
        extra["go_version"] = "1.24"
    elif language == "typescript":
        extra["node_version"] = "22"

    vars_dict = ProjectVars.build(None, language, add_api, extra).to_dict()

    dst = Path(tempfile.mkdtemp(prefix=f"quick-test-{language}-"))
    print(f"  生成 {language} 项目 → {dst}")

    lang_dir = TEMPLATE_ROOT / "languages" / language
    shared_dir = TEMPLATE_ROOT / "shared"

    if lang_dir.exists():
        copy_template_dir(lang_dir, dst, vars_dict)
    if shared_dir.exists():
        copy_template_dir(shared_dir, dst, vars_dict)

    return dst


def main():
    language = sys.argv[1] if len(sys.argv) > 1 else "python"
    add_api = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else True
    add_cli = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    dst = test_generate(language, add_api, add_cli)
    print(f"OK:{dst}")


if __name__ == "__main__":
    main()
