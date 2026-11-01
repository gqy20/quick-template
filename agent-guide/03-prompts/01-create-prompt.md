# 创建 Prompt

Prompt 是独立 YAML 文件，一个文件一个 Prompt。它把**指令**（给模型的角色
和行为）和**模板**（带变量的用户消息）分开，并声明变量契约。

## 文件格式

`config/prompts/code-review.yaml`：

```yaml
id: code-review
version: 1.0.0
description: 结构化审查代码质量与风险
tags: [code, review]
instructions: |
  你是资深代码审查专家。
  优先检查正确性、安全、数据完整性和公共契约，再检查可维护性与性能。
  不要把格式问题作为主要结论。
user_template: |
  请审查以下 $language 代码，给出评分和具体问题：

  $code
variables:
  language:
    required: true
    sensitive: false
  code:
    required: true
    sensitive: true
```

## 字段

| 字段 | 必填 | 约束 |
|---|---|---|
| `id` | 是 | `^[a-z][a-z0-9-]*$`，必须与文件名一致 |
| `version` | 是 | 语义化版本 `X.Y.Z` |
| `description` | 是 | 非空 |
| `instructions` | 是 | 非空，作为 system prompt 追加 |
| `user_template` | 是 | 非空，`string.Template` 语法 |
| `tags` | 否 | 分类标签 |
| `variables` | 否 | 变量契约，见下 |

## 变量契约

每个变量声明：

| 键 | 默认 | 说明 |
|---|---|---|
| `required` | `true` | 是否必须提供 |
| `sensitive` | `false` | 是否敏感（影响日志记录） |
| `default` | `null` | 默认值；`required: true` 时不允许设 |
| `description` | `null` | 用途说明 |

**模板里的变量必须和 `variables` 完全一致**：多声明、少声明都会在加载
时抛 `ValueError`，错误信息列出未声明和未使用的变量名。

这条校验是刻意的 —— 变量名拼错时不会静默渲染成空字符串。

## 用 `$name` 而不是 `{{ name }}`

`user_template` 用 `string.Template` 语法：

```yaml
user_template: |
  请审查以下 $language 代码：

  $code
```

不用 `{{ }}`：那是脚手架模板引擎的语法，两者不是一回事。用 `{{ }}` 会
被当成普通文本原样输出。

`string.Template` 的规则：

- `$name` 替换变量
- `$$` 输出字面量 `$`
- 非法占位符在加载时抛 `ValueError`

## 渲染

```python
from your_package.prompt import PromptRegistry

prompts = PromptRegistry("config/prompts")
prompt = prompts.render("code-review", language="Python", code=source)
```

返回 `RenderedPrompt`，包含：

| 字段 | 用途 |
|---|---|
| `text` | 渲染后的用户消息 |
| `instructions` | 取自 YAML，作为 system prompt |
| `id` / `version` | 进日志，便于追溯 |
| `definition_sha256` | 定义文件摘要，改动即变化 |
| `variable_names` | 本次使用的变量名 |
| `sensitive_variables` | 被标记敏感的变量名 |

## 校验时机

| 时机 | 检查 |
|---|---|
| `load()` | YAML 结构、字段约束、变量契约一致性 |
| `render()` | 提供的是否都是已声明变量、必需变量是否齐全 |

传了未声明的变量抛 `ValueError`，不会忽略。

## 下一步

[变量、敏感标记与版本](02-variables-and-versioning.md) —— 什么时候升版本、
`sensitive` 怎么影响日志。
