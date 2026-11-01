# 结构化输出

两条 Runtime 都要求模型返回**符合 Pydantic 模型**的结果。不符合就抛错，
不降级成自由文本。

## 定义输出模型

```python
from pydantic import BaseModel, Field


class CodeIssue(BaseModel):
    severity: str = Field(description="严重程度: critical/major/minor/info")
    line: int | None = Field(default=None, description="行号")
    description: str = Field(description="问题描述")
    suggestion: str | None = Field(default=None, description="修复建议")


class CodeReviewOutput(BaseModel):
    score: int = Field(description="代码评分 0-10", ge=0, le=10)
    issues: list[CodeIssue] = Field(default_factory=list)
    overall: str = Field(description="总体评价")
```

`Field(description=...)` 不是装饰 —— 它会进入 JSON Schema 告诉模型每个
字段该填什么。**没有 description 的字段模型容易乱填。**

## Schema 从模型生成

```python
from your_package.agent import output_format_schema

schema = output_format_schema(CodeReviewOutput)
```

它会：

- 把 Pydantic 模型转成 JSON Schema
- 内联本地 `$ref`，让 Schema 自包含（SDK 不接受外部引用）

不需要手写 Schema。

## 校验发生在哪

| Runtime | 校验方式 |
|---|---|
| Claude Agent SDK | SDK 按 Schema 约束模型，返回后 `model_validate` |
| LangGraph | 节点 `validate` 按 Schema 校验，失败进 `repair` |

失败行为不同：

- SDK 路径：`AgentOutputError("Agent 未返回符合 Schema 的结构化结果")`
- LangGraph 路径：带校验错误重试，最多 `max_attempts` 次，仍失败则
  `status: failed`

## 写模型的几条规则

**用 `Field` 约束取值。** `ge`/`le`、`Literal`、正则都在 Schema 里生效：

```python
status: Literal["valid", "failed"]  # 只能是这两个
score: int = Field(ge=0, le=10)  # 范围约束
```

**可空字段显式标注。** `str | None` 配 `default=None`，别用空字符串冒充
"没有值"。

**列表默认空列表。** `Field(default_factory=list)`，避免 `None` 判断。

**description 写清判据。** "置信度 0-1"比"置信度"有用；"严重程度:
critical/major/minor/info"比"严重程度"有用。

## 共享输出模型

多个 Runtime 用同一份输出模型：

```python
from your_package.agent_models import CodeReviewOutput, SentimentOutput
```

放在 `agent_models.py` 而不是某个 Runtime 模块里，避免 Claude 侧和
LangGraph 侧各定义一份。模型是契约，契约只有一份。

## 测试用假模型

LangGraph 侧可以传假的 `StructuredModel` 做离线测试：

```python
class FakeStructuredModel:
    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages, **kwargs):
        return CodeReviewOutput(score=8, issues=[], overall="通过")
```

Claude Agent SDK 侧的 `structured_query` 直接打网络，不适合单测 ——
测输出模型时只测 Pydantic 校验本身：

```python
def test_score_range():
    with pytest.raises(ValidationError):
        CodeReviewOutput(score=11, overall="x")
```

## 常见错误

- **没写 `description`。** 模型不知道字段含义，乱填。
- **用 `dict` 接收结果。** 失去校验，错误延迟到使用处才暴露。
- **渲染层再校验一遍。** Schema 已经校验过，重复校验只会产生第二事实源。
- **两条 Runtime 各定义一份输出模型。** 契约分叉。
