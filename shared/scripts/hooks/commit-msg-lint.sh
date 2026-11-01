#!/usr/bin/env bash
# commit-msg：Conventional Commits 宽松校验（允许中文描述；放行 merge/revert/注释行）。
set -euo pipefail
msg_file="${1:?用法: commit-msg-lint.sh <msg-file>}"

# 取第一条非空、非注释行作为 subject
first=$(grep -m1 -vE '^[[:space:]]*(#|$)' "$msg_file" || true)
[[ -n "$first" ]] || { echo "❌ commit-msg：提交信息为空" >&2; exit 1; }

# 放行 git 自动提交
case "$first" in
  'Merge '* | 'Revert '* | 'Cherry-pick '* | 'fixup!'* | 'squash!'*) exit 0 ;;
esac

# 宽松 Conventional Commits：type(scope)?!: 描述（描述允许任意语言）
pat='^(feat|fix|chore|docs|refactor|style|test|perf|build|ci|revert)(\([^)]+\))?!?: .+'
if [[ ! "$first" =~ $pat ]]; then
  cat >&2 <<EOF
❌ commit-msg：首行不符合 Conventional Commits：
    $first
  期望： <type>(<scope>)?: <描述>   （描述允许任意语言）
  type ∈ feat | fix | chore | docs | refactor | style | test | perf | build | ci | revert
  示例：
    feat: 增加 LangGraph 工具调用层
    fix(engine): 保留旧模板目录的 api.py
    chore: 收紧 gitignore
  跳过单次校验: git commit --no-verify
EOF
  exit 1
fi
