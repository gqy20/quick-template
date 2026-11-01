"""核心模板引擎：变量替换 + 条件标记处理。

语法：
  {{var}}                        — 变量
  {{#if expr}}T{{#else}}F{{#endif}}  — 二选一
  {{#if expr}}T{{#endif}}           — 可选块
  {{#if e1}}A{{#elif e2}}B{{#else}}C{{#endif}} — 多路分支

表达式：varname | varname=='val' | varname!='val'
"""

import re

_IF_RE = re.compile(r"\{\{#if\s+.+?\}\}")
_ENDIF_RE = re.compile(r"\{\{#endif\}\}")


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


def _process_branches(text: str, vars_dict: dict, prefix: str = "") -> str:
    """处理 if/elif/else/endif 链（正确处理嵌套）。"""
    parts = re.split(r"(\{\{#(?:if|elif|else|endif)[^}]*\}\})", text)
    parts = _drop_marker_line_breaks(parts, prefix)

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
        if c is None or c == "__else__":
            return "".join(b)
        if _eval_condition(c, vars_dict):
            return "".join(b)
    return ""


def _marker_owns_line(content: str, marker_start: int) -> bool:
    """判断起始于 marker_start 的标记是否独占一行。"""
    line_start = content.rfind("\n", 0, marker_start) + 1
    return not content[line_start:marker_start].strip()


def _drop_marker_line_breaks(parts: list[str], prefix: str) -> list[str]:
    """删除独占一行的条件标记之后紧跟的换行。

    标记独占一行时，它的换行属于标记行而非内容；不删除会在渲染结果中
    多出空行。prefix 是 block 之前的内容，用于判断首个标记是否位于行首。
    """
    result = list(parts)
    for i, part in enumerate(result):
        if not part.startswith("{{#"):
            continue
        before = result[i - 1] if i > 0 else prefix
        if i > 0 and not before:
            # block 以标记开头：行首由 block 之前的内容决定
            before = prefix
        if before and not before.endswith("\n"):
            continue
        if i + 1 < len(result) and result[i + 1].startswith("\n"):
            result[i + 1] = result[i + 1][1:]
    return result


def _is_leaf_block(content: str) -> bool:
    """检查 {{#if...{{#endif}} 块内是否还有嵌套的 {{#if。"""
    # 排除已处理的内部标记（elif/else）
    inner_ifs = list(_IF_RE.finditer(content))
    for m in inner_ifs:
        # 跳过块自身的起始标记（位置 0 的 {{#if）
        if m.start() == 0:
            continue
        # 这个 {{#if 必须在当前块内（不在 elif/else 分支中）
        prefix = content[: m.start()]
        if "{{#elif" in prefix or "{{#else" in prefix:
            continue
        return True
    return False


def process_conditionals(content: str, vars_dict: dict) -> str:
    """多轮处理条件标记（每轮只处理叶子节点，由外向内逐层消去）。"""
    for _ in range(20):
        prev = content

        # 找到所有 {{#if...{{#endif}} 块（非贪婪，匹配最近的 endif）
        for m in reversed(list(_IF_RE.finditer(content))):
            start = m.start()
            end_m = _ENDIF_RE.search(content, m.end())
            if not end_m:
                continue
            end = end_m.end()

            block = content[start:end]
            # 只处理叶子节点（无嵌套 if）：块内的 {{#if 必须都在 elif/else 分支中
            has_nested = False
            for im in _IF_RE.finditer(block):
                if im.start() == 0:
                    continue
                prefix = block[: im.start()]
                if "{{#elif" in prefix or "{{#else" in prefix:
                    continue
                has_nested = True
                break
            if has_nested:
                continue

            processed = _process_branches(block, vars_dict, content[:start])
            tail = content[end:]
            # {{#endif}} 独占一行时，其后的换行属于标记行而非内容。
            if _marker_owns_line(content, end_m.start()) and tail.startswith("\n"):
                tail = tail[1:]
            content = content[:start] + processed + tail

        if content == prev:
            break
    return content


def render(content: str, vars_dict: dict) -> str:
    """先条件后变量的完整渲染。"""
    return substitute_vars(process_conditionals(content, vars_dict), vars_dict)
