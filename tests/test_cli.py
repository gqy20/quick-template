"""CLI 入口的测试。"""

import ast
import json
import tomllib
from pathlib import Path

import pytest

from scaffold.cli import build_vars, get_template_root, main, parse_args, prepare_output_dir


class TestParseArgs:
    """CLI 参数解析。"""

    def test_defaults(self):
        args = parse_args([])
        assert args.language is None
        assert args.output_dir is None
        assert args.data_file is None
        assert args.add_api is None

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

    def test_frontend_flag_omitted(self):
        assert parse_args([]).with_frontend is None

    def test_with_frontend_flag(self):
        args = parse_args(["--with-frontend"])
        assert args.with_frontend is True

    def test_build_vars_carries_frontend_flag(self):
        assert build_vars(None, "python", True)["has_frontend"] is False
        assert build_vars(None, "python", True, True)["has_frontend"] is True

    def test_version_flag(self, capsys):
        from scaffold import __version__

        with pytest.raises(SystemExit, match="0"):
            parse_args(["--version"])
        # 程序名取自 argv[0]，在 pytest 下是 "pytest"；只断言版本号
        assert capsys.readouterr().out.strip().endswith(__version__)


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
        vars_dict = build_vars(None, "python", True)
        assert vars_dict["language"] == "python"
        assert vars_dict["add_api"] is True
        assert "project_slug" in vars_dict
        assert "package_name" in vars_dict

    def test_data_file_merges(self, tmp_path):
        data = {"project_name": "Custom", "add_api": False}
        f = tmp_path / "data.json"
        f.write_text(json.dumps(data))
        vars_dict = build_vars(f, "typescript", True)
        assert vars_dict["project_name"] == "Custom"
        # CLI --add-api should override data file
        assert vars_dict["add_api"] is True

    def test_golang_sets_go_version(self):
        vars_dict = build_vars(None, "golang", True)
        assert vars_dict["language"] == "golang"
        assert "go_version" in vars_dict

    def test_typescript_sets_node_version(self):
        vars_dict = build_vars(None, "typescript", True)
        assert vars_dict["language"] == "typescript"
        assert "node_version" in vars_dict


@pytest.mark.parametrize("link_path", ["pyproject.toml", "src"])
def test_force_checks_both_templates_before_writing(tmp_path, link_path):
    output = tmp_path / "project"
    output.mkdir()
    outside = tmp_path / "outside"
    if link_path == "src":
        outside.mkdir()
    else:
        outside.write_text("keep")
    (output / link_path).symlink_to(outside)
    with pytest.raises(ValueError, match="outside"):
        main(["--output-dir", str(output), "--force"])
    assert list(output.iterdir()) == [output / link_path]
    if outside.is_dir():
        assert not list(outside.iterdir())
    else:
        assert outside.read_text() == "keep"


def test_force_rejects_file_in_place_of_directory_before_writing(tmp_path):
    (tmp_path / "src").write_text("keep")
    with pytest.raises(NotADirectoryError):
        main(["--output-dir", str(tmp_path), "--force"])
    assert list(tmp_path.iterdir()) == [tmp_path / "src"]


@pytest.mark.parametrize("override", [False, True])
def test_cli_config_precedence(tmp_path, override):
    config = tmp_path / "config.yaml"
    config.write_text("language: typescript\nadd_api: false\nhas_frontend: true\n")
    output = tmp_path / "out"
    flags = ["--language", "python", "--add-api", "--no-frontend"] if override else []
    main(["--data-file", str(config), "--output-dir", str(output), *flags])
    assert (output / "package.json").exists() == (not override)
    assert (output / "DESIGN.md").exists() == (not override)
    assert (output / "src/my_project/api.py").exists() == override
    assert not (output / "src/api/router.ts").exists()


@pytest.mark.parametrize("language", ["python", "typescript"])
def test_metadata_round_trips(tmp_path, language):
    config = tmp_path / "config.json"
    value = 'A "small" service in C:\\tools\n第二行 */'
    config.write_text(
        json.dumps({"project_name": value, "description": value, "author_name": value})
    )
    output = tmp_path / "project"
    main(["--language", language, "--data-file", str(config), "--output-dir", str(output)])
    if language == "python":
        metadata = tomllib.loads((output / "pyproject.toml").read_text())["project"]
        assert metadata["authors"][0]["name"] == value
        for source in output.rglob("*.py"):
            ast.parse(source.read_text(), filename=str(source))
    else:
        metadata = json.loads((output / "package.json").read_text())
        assert metadata["author"].startswith(value + " <")
    assert metadata["description"] == value


def test_unsupported_license_fails_before_generation(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"license": "Apache-2.0"}')
    output = tmp_path / "project"
    with pytest.raises(ValueError, match="MIT"):
        main(["--data-file", str(config), "--output-dir", str(output)])
    assert not output.exists()


def test_python_keyword_package_names(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"project_name": "Class"}')
    output = tmp_path / "project"
    main(["--data-file", str(config), "--output-dir", str(output)])
    ast.parse((output / "src/project_class/main.py").read_text())
    config.write_text('{"package_name": "class"}')
    with pytest.raises(ValueError, match="package_name"):
        build_vars(config, "python", False)


def test_go_module_path_uses_repository_host_and_namespace(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text("repository_provider: https://gitlab.com\nrepository_username: acme/team\n")
    output = tmp_path / "project"
    main(["--language", "golang", "--data-file", str(config), "--output-dir", str(output)])
    module = "gitlab.com/acme/team/my-project"
    assert (output / "go.mod").read_text().splitlines()[0] == f"module {module}"
    assert f'"{module}/internal/handler"' in (output / "cmd/my-project/main.go").read_text()
    assert f"https://{module}" in (output / "README.md").read_text()


@pytest.mark.parametrize("language", ["python", "typescript", "golang"])
def test_release_requires_opt_in(tmp_path, language):
    for enabled in (False, True):
        output = tmp_path / str(enabled)
        main(
            [
                "--language",
                language,
                "--output-dir",
                str(output),
                *(["--with-publish"] if enabled else []),
            ]
        )
        workflows = output / ".github/workflows"
        assert len(list(workflows.glob("*.yml"))) == (2 if enabled else 1)
        assert (workflows / "ci.yml").is_file()


def test_base_python_omits_agent_runtime(tmp_path):
    main(["--no-add-api", "--output-dir", str(tmp_path)])
    metadata = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert "optional-dependencies" not in metadata["project"]
    assert not (tmp_path / "config").exists()
    assert not (tmp_path / ".mcp.json").exists()
    assert not list(tmp_path.rglob("*agent*.py"))
    assert "langgraph" not in (tmp_path / "AGENTS.md").read_text().lower()
    assert "--all-extras" not in (tmp_path / ".pre-commit-config.yaml").read_text()


def test_runtime_and_publish_flags_override_data(tmp_path):
    config = tmp_path / "project.json"
    config.write_text('{"with_agent": true, "with_publish": true}')
    enabled = tmp_path / "enabled"
    main(["--data-file", str(config), "--output-dir", str(enabled)])
    assert (enabled / "config/agent.yaml").is_file()
    assert (enabled / ".github/workflows/publish.yml").is_file()
    disabled = tmp_path / "disabled"
    main(["--data-file", str(config), "--no-agent", "--no-publish", "--output-dir", str(disabled)])
    assert not (disabled / "config").exists()
    assert not (disabled / ".github/workflows/publish.yml").exists()
    with pytest.raises(ValueError, match="requires Python"):
        main(["--language", "golang", "--with-agent", "--output-dir", str(tmp_path / "invalid")])
