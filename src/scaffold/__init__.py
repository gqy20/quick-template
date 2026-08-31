"""quick-template: 多语言项目脚手架工具。"""

from .cli import build_vars, get_template_root, parse_args, prepare_output_dir
from .engine import render
from .files import copy_template_dir, load_data_file, process_file
from .variables import ProjectVars

__all__ = [
    "ProjectVars",
    "build_vars",
    "copy_template_dir",
    "get_template_root",
    "load_data_file",
    "parse_args",
    "prepare_output_dir",
    "process_file",
    "render",
]
