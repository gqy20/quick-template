"""文件处理和 CLI 的测试。"""

import json
import os
import textwrap
from pathlib import Path

import pytest

from scaffold.engine import render
from scaffold.variables import ProjectVars


class TestProcessFile:
    """process_file: 读取模板内容 → 渲染 → 返回结果。"""

    def test_simple_template(self, tmp_path):
        tmpl = tmp_path / "hello.txt"
        tmpl.write_text("Hello, {{project_name}}!")
        result = render(tmpl.read_text(), {"project_name": "World"})
        assert result == "Hello, World!"

    def test_conditional_in_file(self, tmp_path):
        tmpl = tmp_path / "cond.txt"
        tmpl.write_text("{{#if add_api}}API ON{{#else}}API OFF{{#endif}}")
        assert render(tmpl.read_text(), {"add_api": True}) == "API ON"
        assert render(tmpl.read_text(), {"add_api": False}) == "API OFF"

    def test_nested_conditionals_in_file(self, tmp_path):
        tmpl = tmp_path / "nested.txt"
        tmpl.write_text(
            '{{#if language=="python"}}PY'
            '{{#if add_api}}+API{{#endif}}'
            '{{#elif language=="golang"}}GO'
            '{{#else}}TS{{#endif}}'
        )
        assert render(tmpl.read_text(), {"language": "python", "add_api": True}) == "PY+API"
        assert render(tmpl.read_text(), {"language": "python", "add_api": False}) == "PY"
        assert render(tmpl.read_text(), {"language": "golang"}) == "GO"
        assert render(tmpl.read_text(), {"language": "typescript"}) == "TS"


class TestCopyTemplateDir:
    """copy_template_dir: 递归复制目录并处理每个文件。"""

    def setup_method(self):
        from scaffold.files import process_file, copy_template_dir
        self.process_file = process_file
        self.copy_template_dir = copy_template_dir

    def test_copies_single_file(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "test.txt").write_text("Hello, {{name}}!")
        self.copy_template_dir(src, dst, {"name": "World"})
        assert (dst / "test.txt").read_text() == "Hello, World!"

    def test_copies_directory_tree(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        (src / "sub").mkdir(parents=True)
        (src / "a.txt").write_text("A")
        (src / "sub" / "b.txt").write_text("B{{x}}")
        self.copy_template_dir(src, dst, {"x": "_"})
        assert (dst / "a.txt").read_text() == "A"
        assert (dst / "sub" / "b.txt").read_text() == "B_"

    def test_processes_conditionals(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "feat.txt").write_text("{{#if flag}}ON{{#endif}}")
        self.copy_template_dir(src, dst, {"flag": True})
        assert (dst / "feat.txt").read_text() == "ON"

        dst2 = tmp_path / "dst2"
        self.copy_template_dir(src, dst2, {"flag": False})
        assert not (dst2 / "feat.txt").exists()

    def test_skips_pycache(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        (src / "__pycache__").mkdir(parents=True)
        (src / "__pycache__" / "cache.pyc").write_text("binary")
        (src / "real.txt").write_text("ok")
        self.copy_template_dir(src, dst, {})
        assert (dst / "real.txt").exists()
        assert not (dst / "__pycache__").exists()

    def test_filename_variable_substitution(self, tmp_path):
        src = tmp_path / "src"
        dst = tmp_path / "dst"
        src.mkdir()
        (src / "{{package_name}}.py").write_text("content")
        self.copy_template_dir(src, dst, {"package_name": "mypkg"})
        assert (dst / "mypkg.py").exists()


class TestLoadDataFile:
    """load_data_file: 加载 JSON/YAML 数据文件。"""

    def setup_method(self):
        from scaffold.files import load_data_file
        self.load_data_file = load_data_file

    def test_json_file(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"project_name": "Test", "add_api": True}))
        result = self.load_data_file(f)
        assert result["project_name"] == "Test"
        assert result["add_api"] is True

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            self.load_data_file(tmp_path / "nope.json")


class TestComputeDerived:
    """ProjectVars._compute_derived: 计算派生变量。"""

    def test_slug_from_name(self):
        values = {"project_name": "My Awesome Project"}
        derived = ProjectVars._compute_derived(values)
        assert derived["project_slug"] == "my-awesome-project"
        assert derived["package_name"] == "my_awesome_project"

    def test_repository_username(self):
        values = {"author_name": "John Doe"}
        derived = ProjectVars._compute_derived(values)
        assert derived["repository_username"] == "john-doe"

    def test_copyright_date(self):
        derived = ProjectVars._compute_derived({})
        assert derived["copyright_date"].isdigit()
        assert len(derived["copyright_date"]) == 4
