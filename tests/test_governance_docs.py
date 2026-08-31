"""生成项目治理文档的验收测试。"""

import json
from pathlib import Path

import pytest
import yaml

from scaffold.files import copy_template_dir
from scaffold.variables import ProjectVars

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]


def generate_template(tmp_path, language, add_api):
    output = tmp_path / f"{language}-{add_api}"
    variables = ProjectVars.build(
        None,
        language,
        add_api,
        {
            "project_name": "Test Project",
            "author_name": "Test Author",
            "repository_username": "test-author",
        },
    ).to_dict()
    copy_template_dir(TEMPLATE_ROOT / "shared", output, variables)
    copy_template_dir(TEMPLATE_ROOT / "languages" / language, output, variables)
    return output


@pytest.mark.parametrize(
    ("language", "add_api"),
    [
        ("python", True),
        ("python", False),
        ("golang", True),
        ("golang", False),
        ("typescript", True),
        ("typescript", False),
    ],
)
def test_generated_agent_contract_is_complete(tmp_path, language, add_api):
    output = generate_template(tmp_path, language, add_api)
    content = (output / "AGENTS.md").read_text()

    assert f"语言：{language}" in content
    assert "## 指令优先级" in content
    assert "## 按请求类型确定授权" in content
    assert "## 事实源与文档路由" in content
    assert "## 工作区与 Git 安全" in content
    assert "## 验证阶梯" in content
    assert "## Code Review Rules" in content
    assert "## 完成标准" in content
    assert ("API：启用" if add_api else "API：未启用") in content
    assert "{{#" not in content
    assert len(content.encode()) < 24 * 1024


def test_generated_design_contract_has_semantic_sections(tmp_path):
    output = generate_template(tmp_path, "typescript", True)
    content = (output / "DESIGN.md").read_text()

    assert "# Design System: Test Project" in content
    assert "## 1. 设计北极星" in content
    assert "## 2. 语义 Token" in content
    assert "## 6. 响应式与无障碍" in content
    assert "## 9. 禁止模式" in content
    assert "## 10. Design QA" in content
    assert "prefers-reduced-motion" in content
    assert "{{#" not in content

    frontmatter = content.split("---", 2)[1]
    metadata = yaml.safe_load(frontmatter)
    assert metadata["status"] == "baseline"
    assert metadata["colors"]["accent"] == "#B04A5A"


def test_generated_claude_instructions_route_to_canonical_contracts(tmp_path):
    output = generate_template(tmp_path, "python", False)
    content = (output / ".claude" / "CLAUDE.md").read_text()

    assert "AGENTS.md" in content
    assert "DESIGN.md" in content
    assert "唯一事实源" in content
    assert "## 常用命令" not in content


def test_python_agent_uses_native_mcp_skills_and_logging_config(tmp_path):
    output = generate_template(tmp_path, "python", False)

    config = yaml.safe_load((output / "config" / "agent.yaml").read_text())
    mcp = json.loads((output / ".mcp.json").read_text())
    pyproject = (output / "pyproject.toml").read_text()

    assert config["mcp_config"] == ".mcp.json"
    assert config["strict_mcp_config"] is True
    assert config["skills"] == []
    assert config["setting_sources"] == ["project"]
    assert config["logging"]["jsonl_path"] == "logs/agent/events.jsonl"
    assert config["runtime_state"]["mode"] == "ephemeral"
    assert mcp == {"mcpServers": {}}
    assert "claude-agent-sdk==0.2.148" in pyproject
    assert "langgraph==1.2.11" in pyproject
    assert "langchain-anthropic==1.7.0" in pyproject
    assert "langchain-mcp-adapters==0.3.2" in pyproject
    assert (output / "src" / "test_project" / "agent_log.py").is_file()
    assert (output / ".claude" / "skills" / "README.md").is_file()
    assert (output / "config" / "prompts" / "default.yaml").is_file()
    assert (output / "src" / "test_project" / "prompt.py").is_file()
    assert (output / "src" / "test_project" / "agent_state.py").is_file()
    assert (output / "src" / "test_project" / "agent_models.py").is_file()
    assert (output / "src" / "test_project" / "langgraph_agent.py").is_file()
    assert (output / "src" / "test_project" / "langgraph_tools.py").is_file()
    assert (output / "config" / "runtimes" / "langgraph.yaml").is_file()
    assert (output / "examples" / "langgraph_review.py").is_file()
    langgraph_config = yaml.safe_load(
        (output / "config" / "runtimes" / "langgraph.yaml").read_text()
    )
    assert langgraph_config["mcp_allowed_tools"] == []
    assert langgraph_config["tool_name_prefix"] is True
