#!/usr/bin/env python3
"""测试 quick-template 模板生成。CI 中通过 uv run 调用。"""

import sys
import tempfile
from pathlib import Path

import copier

TEMPLATE_ROOT = Path(__file__).resolve().parent


def test_generate(language: str, add_api: bool = True, add_cli: bool = False) -> Path:
    """使用 copier Python API 生成项目，避免 CLI 的 Pydantic 验证问题"""
    data = {
        "language": language,
        "project_name": "Test Project",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "description": "A test project",
        "version": "0.1.0",
        "license": "MIT",
        "line_length": 88,
        "add_api": add_api,
        "add_cli": add_cli,
    }
    # 仅提供对应语言的版本变量
    if language == "python":
        data["python_version"] = "3.13"
    elif language == "golang":
        data["go_version"] = "1.24"
    elif language == "typescript":
        data["node_version"] = "22"

    dst = Path(tempfile.mkdtemp(prefix=f"quick-test-{language}-"))
    print(f"  生成 {language} 项目 → {dst}")

    copier.run_copy(
        str(TEMPLATE_ROOT),
        str(dst),
        data=data,
        defaults=True,
        overwrite=True,
        unsafe=True,
        vcs_ref="HEAD",
    )
    return dst


def main():
    language = sys.argv[1] if len(sys.argv) > 1 else "python"
    add_api = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else True
    add_cli = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False

    dst = test_generate(language, add_api, add_cli)
    print(f"OK:{dst}")


if __name__ == "__main__":
    main()
