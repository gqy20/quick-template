#!/usr/bin/env python3
"""测试 quick-template 模板生成。CI 中通过 uv run 调用。"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_generate(
    language: str,
    add_api: bool = True,
    has_frontend: bool = False,
    python_version: str = "3.13",
    with_agent: bool = False,
    with_publish: bool = False,
) -> Path:
    """通过已安装的 CLI 生成矩阵项目。"""
    config = {
        "project_name": "Test Project",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "description": "A test project",
        "python_version": python_version,
    }
    dst = Path(tempfile.mkdtemp(prefix=f"quick-test-{language}-"))
    with tempfile.TemporaryDirectory() as tmp:
        data_file = Path(tmp) / "project.json"
        data_file.write_text(json.dumps(config), encoding="utf-8")
        command = [
            "uv",
            "run",
            "quick-template",
            "--language",
            language,
            "--data-file",
            str(data_file),
            "--output-dir",
            str(dst),
        ]
        command.append("--add-api" if add_api else "--no-add-api")
        if has_frontend:
            command.append("--with-frontend")
        if with_agent:
            command.append("--with-agent")
        if with_publish:
            command.append("--with-publish")
        subprocess.run(command, check=True)
    return dst


def main():
    language = sys.argv[1] if len(sys.argv) > 1 else "python"
    add_api = sys.argv[2].lower() == "true" if len(sys.argv) > 2 else True
    has_frontend = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else False
    python_version = sys.argv[4] if len(sys.argv) > 4 else "3.13"
    with_agent = len(sys.argv) > 5 and sys.argv[5].lower() == "true"
    with_publish = len(sys.argv) > 6 and sys.argv[6].lower() == "true"
    dst = test_generate(language, add_api, has_frontend, python_version, with_agent, with_publish)
    print(f"OK:{dst}")


if __name__ == "__main__":
    main()
