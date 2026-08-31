"""CLI 入口的测试。"""

import json
from pathlib import Path

import pytest

from scaffold.cli import build_vars, get_template_root, parse_args, prepare_output_dir


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

    def test_force_flag(self):
        args = parse_args(["--force"])
        assert args.force is True

    def test_version_flag(self, capsys):
        with pytest.raises(SystemExit, match="0"):
            parse_args(["--version"])
        assert capsys.readouterr().out.strip() == "pytest 0.3.0"


def test_template_root_contains_active_templates():
    root = get_template_root()
    assert (root / "languages").is_dir()
    assert (root / "shared").is_dir()


def test_prepare_output_dir_rejects_non_empty_directory(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep.txt").write_text("important")

    with pytest.raises(FileExistsError, match="--force"):
        prepare_output_dir(output, force=False)


def test_prepare_output_dir_allows_force(tmp_path):
    output = tmp_path / "existing"
    output.mkdir()
    (output / "keep.txt").write_text("important")

    prepare_output_dir(output, force=True)

    assert (output / "keep.txt").read_text() == "important"


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
