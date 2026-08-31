"""{{package_name}}"""

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

__all__ = [
    "greet",
    "add",
    "__version__",
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
