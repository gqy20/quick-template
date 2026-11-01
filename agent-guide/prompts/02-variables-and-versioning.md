# 变量、敏感标记与版本

Prompt 的版本和变量契约会进日志。它们决定了"这次用的是哪份 Prompt、
喂了什么"，也是排查结果差异的起点。

## 什么时候升版本

`version` 是语义化版本，只描述 **Prompt 行为变化**：

| 变化 | 版本 |
|---|---|
| 改 `instructions` 的意图、约束、输出要求 | 升 |
| 改 `user_template` 的结构或措辞 | 升 |
| 改变量的必填性或语义 | 升 |
| 改 `description`、`tags` | 不升 |
| 改 `sensitive` 标记 | 不升 |

判据：**同一份输入，改动后可能得到不同模型行为的，升版本。** 纯元数据
（描述、标签、敏感标记）不影响模型行为。

日志记录 `prompt_version` 和 `definition_sha256`。前者是你声明的版本，
后者是文件实际内容的摘要 —— 改了文件却忘升版本时，摘要会变而版本不变，
能查出来。

## 敏感变量

`sensitive: true` 的变量会被记录在 `sensitive_variables` 里，但**值本身
不写日志**：

```yaml
variables:
  code:
    required: true
    sensitive: true
```

日志里记录的是：

```json
{
  "variable_names": ["code", "language"],
  "sensitive_variables": ["code"]
}
```

知道"传了 code"，不知道 code 是什么。

什么算敏感：用户数据、源码内容、凭据、个人信息、内部路径。什么不算：
语言名、模式开关、枚举值。

注意 `sensitive` 只影响**日志记录**，不影响模型上下文 —— 变量值仍会
进入 Prompt 发给模型。它防止的是"日志泄露"，不是"模型泄露"。

## 默认值

非必需变量可以设默认值：

```yaml
variables:
  tone:
    required: false
    default: 专业
```

`required: true` 和 `default` 互斥 —— 加载时抛 `ValueError`。一个变量
要么必须提供，要么有兜底，两种语义不能混。

## 变量名一致性校验

模板里的 `$name` 和 `variables` 声明必须完全一致：

```yaml
user_template: |
  请审查 $language 代码：$code

variables:
  language: {required: true}
  code: {required: true}
```

少声明 `code` → 加载报错 `undeclared=['code']`
声明了 `tone` 但模板没用 → 加载报错 `unused=['tone']`

这样拼写错误立刻暴露，不会渲染出 `$cod` 这种漏网的占位符。

## Prompt 目录

```
config/prompts/
├── code-review.yaml
├── default.yaml
├── sentiment.yaml
└── summary.yaml
```

- 一个文件一个 Prompt，文件名即 id
- `default_prompt` 配置指定默认用哪个（默认 `default`）
- `prompt_dir` 配置指定目录（默认 `config/prompts`）

`PromptRegistry` 校验 id 格式并阻止路径穿越：`id` 含 `/` 或 `..` 直接
抛 `ValueError`，只能访问注册根目录下的文件。

## 检查清单

新增或修改 Prompt 时：

- [ ] `id` 与文件名一致，符合 `^[a-z][a-z0-9-]*$`
- [ ] 行为变化已升 `version`
- [ ] `$` 变量与 `variables` 声明完全对应
- [ ] 用户数据、源码等标记 `sensitive: true`
- [ ] `required: true` 的变量没有 `default`
- [ ] 本地跑一次渲染，确认没有未替换的占位符
