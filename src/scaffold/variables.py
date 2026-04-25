"""模板变量管理。"""

from datetime import date

DEFAULTS: dict = {
    "project_name": "My Project",
    "version": "0.1.0",
    "description": "A short description",
    "author_name": "Your Name",
    "author_email": "your.email@example.com",
    "license": "MIT",
    "language": "python",
    "python_version": "3.13",
    "go_version": "1.24",
    "node_version": "22",
    "add_api": True,
    "add_cli": False,
    "line_length": 88,
    "repository_provider": "https://github.com",
}


def compute_derived(vars_dict: dict) -> None:
    """根据用户输入计算派生变量（原地修改）。"""
    name = vars_dict["project_name"]
    slug = name.lower().replace(" ", "-").replace("_", "-")
    vars_dict["project_slug"] = slug
    vars_dict["package_name"] = slug.replace("-", "_")
    vars_dict["repository_username"] = vars_dict["author_name"].lower().replace(" ", "-")
    vars_dict["copyright_date"] = str(date.today().year)
    vars_dict["python_version_no_dot"] = vars_dict["python_version"].replace(".", "")
