"""Claude Code CLI 运行状态目录的隔离生命周期。"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from pydantic import BaseModel


class RuntimeStateConfig(BaseModel):
    """完整 transcript 的存储策略。"""

    mode: Literal["ephemeral", "project", "default"] = "ephemeral"
    project_path: Path = Path(".agent-state/claude")


@contextmanager
def runtime_state_env(
    config: RuntimeStateConfig,
    project_root: Path,
) -> Iterator[dict[str, str]]:
    """生成传给 ClaudeAgentOptions.env 的隔离环境。"""
    client_env = {"CLAUDE_AGENT_SDK_CLIENT_APP": "{{project_slug}}/{{version}}"}
    if config.mode == "default":
        yield client_env
        return

    if config.mode == "project":
        state_dir = _prepare_private_dir(project_root / config.project_path)
        yield {**client_env, "CLAUDE_CONFIG_DIR": str(state_dir)}
        return

    with TemporaryDirectory(prefix="{{project_slug}}-claude-") as directory:
        state_dir = _prepare_private_dir(Path(directory))
        yield {**client_env, "CLAUDE_CONFIG_DIR": str(state_dir)}


def _prepare_private_dir(path: Path) -> Path:
    resolved = path.resolve()
    resolved.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        resolved.chmod(0o700)
    except OSError:
        pass
    return resolved
