"""{{package_name}}"""

import os
from pathlib import Path

from .core import add, greet
from .logger import (
    console,
    get_logger,
    logger,
    print_error,
    print_header,
    print_info,
    print_section,
    print_success,
    print_warning,
    setup_logger,
)
{{#if add_api}}

try:
    from .api import app as api_app
except ImportError:
    api_app = None  # type: ignore[assignment]
{{#endif}}

__version__ = "{{version}}"


def load_environment(path: Path | str | None = None) -> None:
    """加载项目 `.env`，并消除互相冲突的模型认证变量。

    - `override=True`：`.env` 里出现的变量优先于宿主环境。宿主 shell 可能带着
      指向其他网关的 `ANTHROPIC_BASE_URL`，在 `.env` 中显式声明它即可覆盖。
      `.env` 未声明的变量仍会沿用宿主值。
    - 同时存在 `ANTHROPIC_API_KEY` 与 `ANTHROPIC_AUTH_TOKEN` 时移除后者：
      SDK 会同时发出两种认证头，只校验 `Authorization` 的网关会拒掉合法 Key。
    """
    from dotenv import find_dotenv, load_dotenv

    resolved = path or find_dotenv(usecwd=True)
    if resolved:
        load_dotenv(resolved, override=True)
    if os.environ.get("ANTHROPIC_API_KEY"):
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)


__all__ = [
    "greet",
    "add",
    "__version__",
    "load_environment",
    "logger",
    "get_logger",
    "setup_logger",
    "console",
    "print_success",
    "print_error",
    "print_warning",
    "print_info",
    "print_header",
    "print_section",
{{#if add_api}}    "api_app",
{{#endif}}]
