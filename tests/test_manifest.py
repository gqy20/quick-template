"""模板分发清单的单元测试。"""

from pathlib import Path

import pytest

from scaffold.files import MANIFEST_NAME, copy_template_dir, load_manifest

ROOT = Path(__file__).resolve().parents[1]
VARS = {"add_api": True, "has_frontend": True, "package_name": "demo"}


def test_manifest_render_paths_and_conditions(tmp_path):
    (tmp_path / MANIFEST_NAME).write_text(
        "files:\n  'src/{{ package_name }}/api.py': add_api\n  DESIGN.md: has_frontend\n"
    )

    assert load_manifest(tmp_path, VARS) == {
        "src/demo/api.py": True,
        "DESIGN.md": True,
    }
    off = load_manifest(tmp_path, {**VARS, "add_api": False, "has_frontend": False})
    assert off == {"src/demo/api.py": False, "DESIGN.md": False}


def test_manifest_absent_means_no_conditions(tmp_path):
    assert load_manifest(tmp_path, VARS) == {}


def test_manifest_rejects_non_mapping(tmp_path):
    (tmp_path / MANIFEST_NAME).write_text("- not a mapping\n")
    with pytest.raises(ValueError, match="mapping"):
        load_manifest(tmp_path, VARS)


def test_manifest_rejects_bad_entry(tmp_path):
    (tmp_path / MANIFEST_NAME).write_text("files:\n  A.md:\n    when: x\n")
    with pytest.raises(ValueError, match="path to a condition"):
        load_manifest(tmp_path, VARS)


def test_copy_skips_false_entries_and_manifest(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / MANIFEST_NAME).write_text("files:\n  keep.md: add_api\n  drop.md: has_frontend\n")
    (src / "keep.md").write_text("keep\n")
    (src / "drop.md").write_text("drop\n")
    (src / "always.md").write_text("always\n")

    out = tmp_path / "out"
    copy_template_dir(src, out, {"add_api": True, "has_frontend": False})

    assert sorted(p.name for p in out.iterdir()) == ["always.md", "keep.md"]
    assert not (out / MANIFEST_NAME).exists()


def test_copy_reports_manifest_path_that_does_not_exist(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / MANIFEST_NAME).write_text("files:\n  missing.md: add_api\n")
    (src / "real.md").write_text("real\n")

    with pytest.raises(ValueError, match="列出但不存在"):
        copy_template_dir(src, tmp_path / "out", VARS)


def test_every_template_manifest_matches_conditional_files():
    """清单必须覆盖模板中所有整文件条件，且不重复声明。"""
    manifest_files: set[str] = set()
    for root in [ROOT / "shared", *sorted((ROOT / "languages").iterdir())]:
        manifest = root / MANIFEST_NAME
        if not manifest.is_file():
            continue
        for line in manifest.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith("files:"):
                continue
            path = stripped.split(":")[0].strip().strip("'\"")
            assert path, manifest
            assert path not in manifest_files, f"重复声明: {path}"
            manifest_files.add(path)
    assert "DESIGN.md" in manifest_files
