"""模板变量管理。"""

import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DEFAULTS: dict[str, Any] = {
    "project_name": "My Project",
    "version": "0.1.0",
    "description": "A short description",
    "author_name": "Your Name",
    "author_email": "your.email@example.com",
    "license": "MIT",
    "language": "python",
    "python_version": "3.13",
    "go_version": "1.27",
    "node_version": "24",
    "add_api": True,
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
    go_version: str = "1.27"
    node_version: str = "24"
    add_api: bool = True
    line_length: int = Field(default=88, ge=79, le=120)
    repository_provider: str = "https://github.com"

    project_slug: str | None = None
    package_name: str | None = None
    repository_username: str | None = None
    copyright_date: str | None = None
    python_version_no_dot: str | None = None

    @field_validator("project_name", "author_name", "author_email")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value

    @field_validator("project_slug")
    @classmethod
    def validate_project_slug(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError("project_slug must use lowercase letters, numbers, and hyphens")
        return value

    @field_validator("package_name")
    @classmethod
    def validate_package_name(cls, value: str | None) -> str | None:
        if value is not None and not value.isidentifier():
            raise ValueError("package_name must be a valid identifier")
        return value

    @field_validator("repository_provider")
    @classmethod
    def normalize_repository_provider(cls, value: str) -> str:
        return value.rstrip("/")

    @classmethod
    def build(
        cls,
        data_file: Path | None,
        language: str,
        add_api: bool,
        extra: dict[str, Any] | None = None,
    ) -> "ProjectVars":
        """构建完整变量模型。"""
        from .files import load_data_file

        values: dict[str, Any] = {}
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
    def _compute_derived(values: dict[str, Any]) -> dict[str, str]:
        """根据基础字段值计算所有派生字段。"""
        name = str(values.get("project_name", ""))
        slug = str(values.get("project_slug") or slugify(name))
        package_name = str(values.get("package_name") or slug.replace("-", "_"))
        if package_name[0].isdigit():
            package_name = f"project_{package_name}"
        return {
            "project_slug": slug,
            "package_name": package_name,
            "repository_username": str(
                values.get("repository_username") or slugify(str(values.get("author_name", "")))
            ),
            "copyright_date": str(date.today().year),
            "python_version_no_dot": str(values.get("python_version", "")).replace(".", ""),
        }

    def to_dict(self) -> dict[str, Any]:
        """导出为 dict（用于 engine.py）。"""
        return self.model_dump()


def slugify(value: str) -> str:
    """将人类可读名称转换为稳定的 ASCII slug。"""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "project"
