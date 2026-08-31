"""版本化 YAML Prompt 的加载、校验和安全渲染。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, model_validator


class PromptVariable(BaseModel):
    """Prompt 输入变量契约。"""

    required: bool = True
    sensitive: bool = False
    default: str | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_default(self) -> "PromptVariable":
        if self.required and self.default is not None:
            raise ValueError("required variables cannot define a default")
        return self


class PromptSystem(BaseModel):
    """Claude SDK 原生 system prompt 表达。"""

    type: Literal["preset", "text"] = "preset"
    preset: Literal["claude_code"] | None = "claude_code"
    append: str | None = None
    text: str | None = None

    @model_validator(mode="after")
    def validate_variant(self) -> "PromptSystem":
        if self.type == "text" and not self.text:
            raise ValueError("text system prompts require text")
        if self.type == "preset" and self.preset != "claude_code":
            raise ValueError("preset system prompts require claude_code")
        return self

    def to_sdk(self) -> str | dict[str, str]:
        """转换为 ClaudeAgentOptions.system_prompt。"""
        if self.type == "text":
            return self.text or ""
        result = {"type": "preset", "preset": "claude_code"}
        if self.append:
            result["append"] = self.append
        return result


class PromptDefinition(BaseModel):
    """单个 Prompt YAML 的稳定契约。"""

    id: str = Field(pattern=r"^[a-z][a-z0-9-]*$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    system: PromptSystem = Field(default_factory=PromptSystem)
    user_template: str = Field(min_length=1)
    variables: dict[str, PromptVariable] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_template_variables(self) -> "PromptDefinition":
        template = Template(self.user_template)
        if not template.is_valid():
            raise ValueError("user_template contains invalid placeholders")
        identifiers = set(template.get_identifiers())
        declared = set(self.variables)
        if identifiers != declared:
            missing = sorted(identifiers - declared)
            unused = sorted(declared - identifiers)
            raise ValueError(
                f"Prompt variable contract mismatch: undeclared={missing}, unused={unused}"
            )
        return self


@dataclass(frozen=True)
class RenderedPrompt:
    """带 provenance 的渲染结果。"""

    id: str
    version: str
    description: str
    text: str
    system_prompt: str | dict[str, str]
    definition_sha256: str
    variable_names: tuple[str, ...]
    sensitive_variables: frozenset[str]


class PromptRegistry:
    """从固定目录加载一文件一 Prompt 的注册表。"""

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()

    def load(self, prompt_id: str) -> tuple[PromptDefinition, str]:
        """加载并校验 Prompt，返回定义及源文件摘要。"""
        if not re.fullmatch(r"[a-z][a-z0-9-]*", prompt_id):
            raise ValueError(f"Invalid prompt id: {prompt_id}")
        path = (self.root / f"{prompt_id}.yaml").resolve()
        if path.parent != self.root:
            raise ValueError("Prompt path escapes registry root")
        raw = path.read_bytes()
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            raise ValueError("Prompt definition must be a mapping")
        definition = PromptDefinition.model_validate(data)
        if definition.id != prompt_id:
            raise ValueError(
                f"Prompt id {definition.id!r} does not match filename {prompt_id!r}"
            )
        return definition, hashlib.sha256(raw).hexdigest()

    def render(self, prompt_id: str, **values: Any) -> RenderedPrompt:
        """校验输入变量并使用 string.Template 安全渲染。"""
        definition, source_hash = self.load(prompt_id)
        unknown = sorted(set(values) - set(definition.variables))
        if unknown:
            raise ValueError(f"Unknown prompt variables: {unknown}")

        resolved: dict[str, str] = {}
        missing: list[str] = []
        for name, variable in definition.variables.items():
            if name in values:
                resolved[name] = str(values[name])
            elif variable.default is not None:
                resolved[name] = variable.default
            elif variable.required:
                missing.append(name)
        if missing:
            raise ValueError(f"Missing prompt variables: {sorted(missing)}")

        text = Template(definition.user_template).substitute(resolved)
        sensitive = frozenset(
            name
            for name, variable in definition.variables.items()
            if variable.sensitive
        )
        return RenderedPrompt(
            id=definition.id,
            version=definition.version,
            description=definition.description,
            text=text,
            system_prompt=definition.system.to_sdk(),
            definition_sha256=source_hash,
            variable_names=tuple(sorted(resolved)),
            sensitive_variables=sensitive,
        )
