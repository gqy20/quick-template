"""GitHub Pages static artifact tests."""

import subprocess
import sys
from pathlib import Path

CHECKER = Path("scripts/check_pages.py").resolve()


def test_pages_artifact_is_current_and_self_contained() -> None:
    result = subprocess.run(
        [sys.executable, str(CHECKER), "docs"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_pages_validator_detects_template_markers(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("<html>{{ project_slug }}</html>")

    result = subprocess.run(
        [sys.executable, str(CHECKER), str(docs)],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 1
    assert "template marker" in result.stdout
