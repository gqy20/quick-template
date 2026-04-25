"""scaffold 引擎核心测试 — TDD 红绿重构。"""

import pytest

from scaffold.engine import render, substitute_vars, process_conditionals
from scaffold.variables import DEFAULTS, compute_derived


class TestSubstituteVars:
    """变量替换 {{variable}} → 实际值。"""

    def test_simple_var(self):
        assert substitute_vars("Hello {{name}}", {"name": "World"}) == "Hello World"

    def test_multiple_vars(self):
        result = substitute_vars("{{a}} and {{b}}", {"a": "1", "b": "2"})
        assert result == "1 and 2"

    def test_unknown_var_unchanged(self):
        assert substitute_vars("{{unknown}}", {}) == "{{unknown}}"

    def test_no_vars(self):
        assert substitute_vars("plain text", {}) == "plain text"

    def test_repeated_var(self):
        assert substitute_vars("{{x}}-{{x}}", {"x": "A"}) == "A-A"


class TestEvalCondition:
    """条件表达式评估。"""

    def test_truthy(self):
        from scaffold.engine import _eval_condition
        assert _eval_condition("add_api", {"add_api": True}) is True
        assert _eval_condition("add_api", {"add_api": False}) is False
        assert _eval_condition("missing", {}) is False

    def test_eq_string(self):
        from scaffold.engine import _eval_condition
        assert _eval_condition("lang=='python'", {"lang": "python"}) is True
        assert _eval_condition("lang=='python'", {"lang": "go"}) is False

    def test_neq_string(self):
        from scaffold.engine import _eval_condition
        assert _eval_condition("lang!='python'", {"lang": "go"}) is True
        assert _eval_condition("lang!='python'", {"lang": "python"}) is False


class TestProcessConditionals:
    """条件标记处理 {{#if}}...{{#endif}}。"""

    def test_if_true(self):
        assert process_conditionals("{{#if flag}}yes{{#endif}}", {"flag": True}) == "yes"

    def test_if_false(self):
        assert process_conditionals("{{#if flag}}yes{{#endif}}", {"flag": False}) == ""

    def test_if_else_true(self):
        tmpl = "{{#if flag}}on{{#else}}off{{#endif}}"
        assert process_conditionals(tmpl, {"flag": True}) == "on"

    def test_if_else_false(self):
        tmpl = "{{#if flag}}on{{#else}}off{{#endif}}"
        assert process_conditionals(tmpl, {"flag": False}) == "off"

    def test_elif_first_match(self):
        tmpl = "{{#if x==1}}a{{#elif x==2}}b{{#else}}c{{#endif}}"
        assert process_conditionals(tmpl, {"x": "1"}) == "a"

    def test_elif_second_match(self):
        tmpl = "{{#if x==1}}a{{#elif x==2}}b{{#else}}c{{#endif}}"
        assert process_conditionals(tmpl, {"x": "2"}) == "b"

    def test_elif_fallback(self):
        tmpl = "{{#if x==1}}a{{#elif x==2}}b{{#else}}c{{#endif}}"
        assert process_conditionals(tmpl, {"x": "3"}) == "c"

    def test_nested_if_inner_true(self):
        tmpl = "{{#if outer}}{{#if inner}}both{{#endif}}{{#endif}}"
        assert process_conditionals(tmpl, {"outer": True, "inner": True}) == "both"

    def test_nested_if_inner_false(self):
        tmpl = "{{#if outer}}{{#if inner}}both{{#else}}outer-only{{#endif}}{{#endif}}"
        assert process_conditionals(tmpl, {"outer": True, "inner": False}) == "outer-only"

    def test_nested_if_outer_false(self):
        tmpl = "{{#if outer}}{{#if inner}}both{{#endif}}{{#endif}}"
        assert process_conditionals(tmpl, {"outer": False, "inner": True}) == ""

    def test_nested_with_elif_and_add_api(self):
        """模拟 README.md 的嵌套：language + add_api。"""
        tmpl = (
            '{{#if language=="python"}}'
            '{{#if add_api}}py+api{{#else}}py{{#endif}}'
            '{{#elif language=="golang"}}go{{#else}}ts{{#endif}}'
        )
        assert process_conditionals(tmpl, {"language": "python", "add_api": True}) == "py+api"
        assert process_conditionals(tmpl, {"language": "python", "add_api": False}) == "py"
        assert process_conditionals(tmpl, {"language": "golang", "add_api": True}) == "go"
        assert process_conditionals(tmpl, {"language": "typescript"}) == "ts"


class TestRender:
    """完整渲染流程：先条件后变量。"""

    def setup_method(self):
        self.vars = dict(DEFAULTS)
        compute_derived(self.vars)

    def test_var_substitution(self):
        assert render("Hi {{project_name}}", self.vars) == "Hi My Project"

    def test_conditional_then_var(self):
        tmpl = "{{#if add_api}}API: {{project_name}}{{#endif}}"
        assert render(tmpl, self.vars) == "API: My Project"

    def test_conditional_false_removes_block(self):
        tmpl = "{{#if add_api}}HIDDEN{{#endif}}VISIBLE"
        assert render(tmpl, {**self.vars, "add_api": False}) == "VISIBLE"

    def test_derived_vars_available(self):
        assert render("slug: {{project_slug}}", self.vars) == "slug: my-project"
        assert render("pkg: {{package_name}}", self.vars) == "pkg: my_project"
