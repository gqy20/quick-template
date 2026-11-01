"""智能体开发指南与 Python 模板实现的一致性测试。"""

import ast
import re
from pathlib import Path

from scaffold.engine import render
from scaffold.variables import ProjectVars

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "agent-guide"
PACKAGE = ROOT / "languages" / "python" / "src" / "{{package_name}}"

RENDER_VARS = ProjectVars.build(
    None,
    "python",
    True,
    {
        "project_name": "T",
        "author_name": "T",
        "author_email": "t@example.com",
        "python_version": "3.13",
    },
).to_dict()

IMPORT_RE = re.compile(
    r"^from your_package\.(?P<module>\w+) import (?P<names>[^\n]+)$",
    re.MULTILINE,
)
CODE_BLOCK_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _guide_text() -> str:
    return "\n".join(path.read_text() for path in sorted(GUIDE.rglob("*.md")))


def _public_names(module: str) -> set[str]:
    path = PACKAGE / f"{module}.py"
    tree = ast.parse(render(path.read_text(), RENDER_VARS))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_guide_imports_resolve_to_template_symbols() -> None:
    """指南里的每个包内导入都必须在模板实现中存在。"""
    text = _guide_text()
    imports = list(IMPORT_RE.finditer(text))
    assert imports, "指南未引用任何包内符号"

    missing: list[str] = []
    for match in imports:
        module = match.group("module")
        module_path = PACKAGE / f"{module}.py"
        if not module_path.is_file():
            missing.append(f"{module}.py 不存在")
            continue
        available = _public_names(module)
        for raw in match.group("names").split(","):
            name = raw.strip().split(" as ")[0].strip()
            if name and name not in available:
                missing.append(f"{module}.{name} 不存在")

    assert not missing, f"指南引用了不存在的符号: {sorted(set(missing))}"


def test_guide_python_blocks_are_valid_syntax() -> None:
    """Markdown 中的 Python 代码块必须能被解析。"""
    errors: list[str] = []
    for path in sorted(GUIDE.rglob("*.md")):
        for index, block in enumerate(CODE_BLOCK_RE.findall(path.read_text()), 1):
            try:
                ast.parse(block)
            except SyntaxError as error:
                errors.append(f"{path.relative_to(ROOT)} 第 {index} 块: {error.msg}")
    assert not errors, errors


def test_guide_links_resolve() -> None:
    """指南内部链接不能指向不存在的文件。"""
    broken: list[str] = []
    for path in sorted(GUIDE.rglob("*.md")):
        for link in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text()):
            if link.startswith(("http", "#", "mailto")):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.exists():
                broken.append(f"{path.relative_to(ROOT)} -> {link}")
    assert not broken, broken
