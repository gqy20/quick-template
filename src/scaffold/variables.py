"""模板变量管理。"""

import json
import keyword
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

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
    "has_frontend": False,
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
    license: Literal["MIT"] = "MIT"
    language: Literal["python", "golang", "typescript"] = "python"
    python_version: str = "3.13"
    go_version: str = "1.27"
    node_version: str = "24"
    add_api: bool = True
    has_frontend: bool = False
    with_agent: bool = False
    with_publish: bool = False
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
    def validate_package_name(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is not None and (
            not value.isidentifier()
            or (info.data.get("language") == "python" and keyword.iskeyword(value))
        ):
            raise ValueError("package_name must be a valid identifier")
        return value

    @model_validator(mode="after")
    def validate_runtime(self) -> "ProjectVars":
        if self.with_agent and self.language != "python":
            raise ValueError("--with-agent requires Python")
        return self

    @field_validator("repository_provider")
    @classmethod
    def normalize_repository_provider(cls, value: str) -> str:
        return value.rstrip("/")

    @classmethod
    def build(
        cls,
        data_file: Path | None,
        language: str | None,
        add_api: bool | None,
        extra: dict[str, Any] | None = None,
    ) -> "ProjectVars":
        """构建完整变量模型。"""
        from .files import load_data_file

        values: dict[str, Any] = {}
        values.update(_DEFAULTS)
        if data_file:
            values.update(load_data_file(data_file))
        if language is not None:
            values["language"] = language
        if add_api is not None:
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
        if not values.get("package_name") and (
            package_name[0].isdigit()
            or (values.get("language") == "python" and keyword.iskeyword(package_name))
        ):
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
        values = self.model_dump()
        # 双引号字符串内的文本片段；保留 Markdown 正文中的原始值。
        for key in (
            "project_name",
            "description",
            "author_name",
            "author_email",
            "version",
            "repository_provider",
            "repository_username",
        ):
            encoded = json.dumps(str(values[key]), ensure_ascii=False)
            values[f"{key}_escaped"] = encoded[1:-1].replace(chr(127), r"\u007f")
        if self.language == "golang":
            provider = self.repository_provider
            url = urlsplit(provider if "://" in provider else f"https://{provider}")
            module = f"{url.netloc}{url.path}/{self.repository_username}/{self.project_slug}"
            if (
                url.scheme not in {"http", "https"}
                or url.query
                or url.fragment
                or not re.fullmatch(r"[A-Za-z0-9.-]+(?:/[A-Za-z0-9_~.-]+)+", module)
                or any(part.startswith(".") or part.endswith(".") for part in module.split("/"))
            ):
                raise ValueError(
                    "repository_provider and repository_username must form a Go module path"
                )
            values["go_module_path"] = module
        return values


def slugify(value: str) -> str:
    """将人类可读名称转换为稳定的 ASCII slug。"""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-") or "project"
