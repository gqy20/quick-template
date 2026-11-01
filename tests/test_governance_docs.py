"""生成项目治理文档的验收测试。"""

import json
import re
from pathlib import Path

import pytest
import yaml

from scaffold.files import copy_template_dir
from scaffold.variables import ProjectVars

TEMPLATE_ROOT = Path(__file__).resolve().parents[1]


def generate_template(tmp_path, language, add_api, has_frontend=False):
    output = tmp_path / f"{language}-{add_api}-{has_frontend}"
    variables = ProjectVars.build(
        None,
        language,
        add_api,
        {
            "project_name": "Test Project",
            "author_name": "Test Author",
            "repository_username": "test-author",
            "has_frontend": has_frontend,
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
    output = generate_template(tmp_path, "typescript", True, has_frontend=True)
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
    claude_md = output / ".claude" / "CLAUDE.md"
    content = claude_md.read_text()

    # Claude Code 直接读 AGENTS.md；此处仅用 @ 引入作旧版本兜底，不复述规则。
    assert content.strip() == "@../AGENTS.md"
    assert (claude_md.parent / "../AGENTS.md").resolve() == (output / "AGENTS.md").resolve()
    assert "## 常用命令" not in content


def test_generated_docs_follow_directory_convention(tmp_path):
    """docs/ 承载按需查阅的文档，根目录只保留每次都要读的契约。"""
    output = generate_template(tmp_path, "typescript", True, has_frontend=True)

    assert (output / "AGENTS.md").is_file()
    assert (output / "DESIGN.md").is_file()
    assert (output / "README.md").is_file()

    docs = output / "docs"
    assert (docs / "README.md").is_file()
    assert (docs / "CHANGELOG.md").is_file()
    assert (docs / "PRODUCT.md").is_file()

    # CHANGELOG 与 PRODUCT 按需查阅，不占根目录
    assert not (output / "CHANGELOG.md").exists()
    assert not (output / "PRODUCT.md").exists()

    # 索引说明编号与命名规范
    index = (docs / "README.md").read_text()
    assert "90-archive" in index
    assert "kebab-case" in index

    # 前三个槽位固定，跨项目含义一致
    assert "01-product" in index
    assert "02-architecture" in index
    assert "03-operations" in index


@pytest.mark.parametrize("language", ["python", "golang", "typescript"])
def test_design_baseline_only_with_frontend(tmp_path, language):
    """没有前端时不生成 DESIGN.md，也不在契约里引用它。"""
    without = generate_template(tmp_path / "off", language, True, has_frontend=False)
    assert not (without / "DESIGN.md").exists()
    for name in ("AGENTS.md", "README.md"):
        assert "DESIGN.md" not in (without / name).read_text(), name
    assert "DESIGN.md" not in (without / "docs" / "README.md").read_text()

    with_ui = generate_template(tmp_path / "on", language, True, has_frontend=True)
    assert (with_ui / "DESIGN.md").is_file()
    assert "DESIGN.md" in (with_ui / "AGENTS.md").read_text()


def test_generated_docs_have_no_design_qa_special_path(tmp_path):
    """验收证据归入编号专题，不再有独立的 design-qa 路径。"""
    output = generate_template(tmp_path, "typescript", True)

    for path in output.rglob("*.md"):
        assert "design-qa" not in path.read_text(), path.relative_to(output)


def test_generated_docs_have_no_broken_links(tmp_path):
    """生成的文档内部链接与 @ 引入必须能解析。"""
    output = generate_template(tmp_path, "python", False)

    for path in output.rglob("*.md"):
        text = path.read_text()
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
            link = match.group(1)
            if link.startswith(("http", "#", "mailto")):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            assert target.exists(), f"{path.relative_to(output)} 链接失效: {link}"

        for line in text.splitlines():
            if line.startswith("@"):
                target = (path.parent / line[1:].strip()).resolve()
                assert target.exists(), f"{path.relative_to(output)} 引入失效: {line}"


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
    assert "claude-agent-sdk==0.2.176" in pyproject
    assert "langgraph==1.2.19" in pyproject
    assert "langchain-anthropic==1.7.7" in pyproject
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
