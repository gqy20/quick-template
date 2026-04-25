"""核心模板引擎：变量替换 + 条件标记处理。

语法：
  {{var}}                        — 变量
  {{#if expr}}T{{#else}}F{{#endif}}  — 二选一
  {{#if expr}}T{{#endif}}           — 可选块
  {{#if e1}}A{{#elif e2}}B{{#else}}C{{#endif}} — 多路分支

表达式：varname | varname=='val' | varname!='val'
"""

import re


def substitute_vars(content: str, vars_dict: dict) -> str:
    return re.sub(
        r"\{\{\s*(\w+)\s*\}\}",
        lambda m: str(vars_dict.get(m.group(1).strip(), m.group(0))),
        content,
    )


def _eval_condition(expr: str, vars_dict: dict) -> bool:
    expr = expr.strip()
    if "==" in expr:
        k, v = expr.split("==", 1)
        return str(vars_dict.get(k.strip(), "")) == v.strip().strip("'\"")
    if "!=" in expr:
        k, v = expr.split("!=", 1)
        return str(vars_dict.get(k.strip(), "")) != v.strip().strip("'\"")
    return bool(vars_dict.get(expr, False))


def _process_branches(text: str, vars_dict: dict) -> str:
    """处理 if/elif/else/endif 链（正确处理嵌套）。"""
    parts = re.split(r"(\{\{#(?:if|elif|else|endif)[^}]*\}\})", text)

    branches = []
    cond = None
    buf: list[str] = []
    depth = 0

    for part in parts:
        if part.startswith("{{#if"):
            if cond is None:
                cond = part[6:-2].strip()
                buf = []
            else:
                depth += 1
                buf.append(part)
        elif part.startswith("{{#endif}"):
            if depth > 0:
                depth -= 1
                buf.append(part)
            else:
                branches.append((cond, buf))
                cond = None
                buf = []
        elif part.startswith("{{#elif"):
            if depth == 0:
                branches.append((cond, buf))
                cond = part[8:-2].strip()
                buf = []
            else:
                buf.append(part)
        elif part.startswith("{{#else"):
            if depth == 0:
                branches.append((cond, buf))
                cond = "__else__"
                buf = []
            else:
                buf.append(part)
        else:
            buf.append(part)

    if cond is not None:
        branches.append((cond, buf))

    for c, b in branches:
        if c == "__else__":
            return "".join(b)
        if _eval_condition(c, vars_dict):
            return "".join(b)
    return ""


def process_conditionals(content: str, vars_dict: dict) -> str:
    """多轮处理条件标记（每轮由外向内消去一层嵌套）。"""
    for _ in range(10):
        prev = content
        content = re.sub(
            r"\{\{#if\s+[\w'\"\=!]+\}\}.*\{\{#endif\}\}",
            lambda m: _process_branches(m.group(0), vars_dict),
            content,
            flags=re.DOTALL,
        )
        if content == prev:
            break
    return content


def render(content: str, vars_dict: dict) -> str:
    """先条件后变量的完整渲染。"""
    return substitute_vars(process_conditionals(content, vars_dict), vars_dict)
