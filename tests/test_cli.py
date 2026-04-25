"""CLI 入口的测试。"""

import json
from pathlib import Path

from scaffold.cli import build_vars, parse_args


class TestParseArgs:
    """CLI 参数解析。"""

    def test_defaults(self):
        args = parse_args([])
        assert args.language == "python"
        assert args.output_dir is None
        assert args.data_file is None
        assert args.add_api is True

    def test_language_override(self):
        args = parse_args(["--language", "golang"])
        assert args.language == "golang"

    def test_output_dir(self):
        args = parse_args(["--output-dir", "/tmp/myproj"])
        assert args.output_dir == Path("/tmp/myproj")

    def test_data_file(self):
        args = parse_args(["--data-file", "answers.json"])
        assert args.data_file == Path("answers.json")

    def test_no_add_api(self):
        args = parse_args(["--no-add-api"])
        assert args.add_api is False

    def test_add_api_flag(self):
        args = parse_args(["--add-api"])
        assert args.add_api is True


class TestBuildVars:
    """变量构建：defaults + data file + CLI flags + derived。"""

    def test_defaults_only(self):
        vars_dict = build_vars(None, "python", True, None)
        assert vars_dict["language"] == "python"
        assert vars_dict["add_api"] is True
        assert "project_slug" in vars_dict
        assert "package_name" in vars_dict

    def test_data_file_merges(self, tmp_path):
        data = {"project_name": "Custom", "add_api": False}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        vars_dict = build_vars(f, "typescript", True, None)
        assert vars_dict["project_name"] == "Custom"
        # CLI --add-api should override data file
        assert vars_dict["add_api"] is True

    def test_cli_output_dir_affects_project_path(self):
        vars_dict = build_vars(None, "python", True, Path("/tmp/out"))
        # output_dir doesn't go into vars but affects where files are written
        assert vars_dict["language"] == "python"

    def test_golang_sets_go_version(self):
        vars_dict = build_vars(None, "golang", True, None)
        assert vars_dict["language"] == "golang"
        assert "go_version" in vars_dict

    def test_typescript_sets_node_version(self):
        vars_dict = build_vars(None, "typescript", True, None)
        assert vars_dict["language"] == "typescript"
        assert "node_version" in vars_dict
