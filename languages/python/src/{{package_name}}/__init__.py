"""{{package_name}}"""

{{#if with_agent}}import os
{{#endif}}from pathlib import Path

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

__version__ = "{{ version_escaped }}"


def load_environment(path: Path | str | None = None) -> None:
    """加载项目 .env，优先使用文件中显式提供的值。"""
    from dotenv import find_dotenv, load_dotenv

    resolved = path or find_dotenv(usecwd=True)
    if resolved:
        load_dotenv(resolved, override=True)
{{#if with_agent}}
    if os.environ.get("ANTHROPIC_API_KEY"):
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
{{#endif}}


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
