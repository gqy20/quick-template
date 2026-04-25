"""quick-template: 多语言项目脚手架工具。"""

from .cli import build_vars, parse_args
from .engine import render
from .files import copy_template_dir, load_data_file, process_file
from .variables import DEFAULTS, compute_derived

__all__ = [
    "DEFAULTS",
    "build_vars",
    "compute_derived",
    "copy_template_dir",
    "load_data_file",
    "parse_args",
    "process_file",
    "render",
]
