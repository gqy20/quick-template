"""模板变量管理。"""

from datetime import date
from pathlib import Path
from pydantic import BaseModel, ConfigDict

_DEFAULTS: dict = {
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


class ProjectVars(BaseModel):
    """项目变量模型，带自动计算的派生字段。"""

    model_config = ConfigDict(extra="allow")

    project_name: str = "My Project"
    version: str = "0.1.0"
    description: str = "A short description"
    author_name: str = "Your Name"
    author_email: str = "your.email@example.com"
    license: str = "MIT"
    language: str = "python"
    python_version: str = "3.13"
    go_version: str = "1.24"
    node_version: str = "22"
    add_api: bool = True
    add_cli: bool = False
    line_length: int = 88
    repository_provider: str = "https://github.com"

    project_slug: str | None = None
    package_name: str | None = None
    repository_username: str | None = None
    copyright_date: str | None = None
    python_version_no_dot: str | None = None

    @classmethod
    def build(
        cls,
        data_file: Path | None,
        language: str,
        add_api: bool,
        extra: dict | None = None,
    ) -> "ProjectVars":
        """构建完整变量模型。"""
        from .files import load_data_file

        values: dict = {}
        values.update(_DEFAULTS)
        if data_file:
            values.update(load_data_file(data_file))
        values["language"] = language
        values["add_api"] = add_api
        if extra:
            values.update(extra)
        values.update(cls._compute_derived(values))
        return cls.model_validate(values)

    @staticmethod
    def _compute_derived(values: dict) -> dict:
        """根据基础字段值计算所有派生字段。"""
        name = values.get("project_name", "")
        slug = name.lower().replace(" ", "-").replace("_", "-")
        return {
            "project_slug": slug,
            "package_name": slug.replace("-", "_"),
            "repository_username": values.get("author_name", "").lower().replace(" ", "-"),
            "copyright_date": str(date.today().year),
            "python_version_no_dot": values.get("python_version", "").replace(".", ""),
        }

    def to_dict(self) -> dict:
        """导出为 dict（用于 engine.py）。"""
        return self.model_dump()
