"""Agent SDK 模块测试。"""

import pytest
from pydantic import BaseModel, Field


class TestOutputFormatSchema:
    """output_format_schema: Pydantic → SDK output_format。"""

    def test_simple_model_schema(self):
        """测试简单模型的 schema 生成。"""
        from {{ package_name }}.agent import output_format_schema

        class SimpleOutput(BaseModel):
            name: str
            value: int

        schema = output_format_schema(SimpleOutput)

        assert schema["type"] == "json_schema"
        assert schema["name"] == "SimpleOutput"
        assert schema["strict"] is True
        assert "schema" in schema

    def test_nested_model_schema(self):
        """测试嵌套模型的 schema 生成。"""
        from {{ package_name }}.agent import output_format_schema

        class Item(BaseModel):
            id: int
            title: str

        class ListOutput(BaseModel):
            items: list[Item]
            total: int

        schema = output_format_schema(ListOutput)

        assert schema["name"] == "ListOutput"
        assert "items" in schema["schema"]["properties"]
        assert "total" in schema["schema"]["properties"]

    def test_schema_with_field_description(self):
        """测试带 Field 描述的 schema。"""
        from {{ package_name }}.agent import output_format_schema

        class DescribedOutput(BaseModel):
            score: int = Field(description="评分 0-100")
            remark: str = Field(description="备注信息")

        schema = output_format_schema(DescribedOutput)

        props = schema["schema"]["properties"]
        assert "description" in props["score"]
        assert "description" in props["remark"]


class TestParseWithModel:
    """parse_with_model: 结构化输出解析。"""

    def test_parse_simple_output(self):
        """测试简单输出解析。"""
        from {{ package_name }}.agent import parse_with_model

        class SimpleOutput(BaseModel):
            result: str
            count: int

        # 模拟 ResultMessage with structured_output
        class MockResult:
            structured_output = {"result": "success", "count": 42}

        parsed = parse_with_model(MockResult(), SimpleOutput)
        assert parsed is not None
        assert parsed.result == "success"
        assert parsed.count == 42

    def test_parse_nested_output(self):
        """测试嵌套输出解析。"""
        from {{ package_name }}.agent import parse_with_model

        class Item(BaseModel):
            id: int
            name: str

        class ListOutput(BaseModel):
            items: list[Item]
            total: int

        class MockResult:
            structured_output = {
                "items": [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
                "total": 2,
            }

        parsed = parse_with_model(MockResult(), ListOutput)
        assert parsed is not None
        assert parsed.total == 2
        assert len(parsed.items) == 2
        assert parsed.items[0].name == "item1"

    def test_parse_invalid_output_returns_none(self):
        """测试无效输出返回 None。"""
        from {{ package_name }}.agent import parse_with_model

        class StrictOutput(BaseModel):
            required_field: str

        class MockResult:
            structured_output = {"wrong_field": "value"}

        parsed = parse_with_model(MockResult(), StrictOutput)
        # 验证失败返回 None
        assert parsed is None


class TestAgentRunner:
    """AgentRunner: 简化 query 执行。"""

    def test_runner_initialization(self):
        """测试 Runner 初始化。"""
        from {{ package_name }}.agent import AgentRunner, output_format_schema

        class DummyOutput(BaseModel):
            value: str

        schema = output_format_schema(DummyOutput)
        runner = AgentRunner(
            schema=schema,
            system_prompt="test prompt",
            max_turns=5,
        )

        assert runner.schema == schema
        assert runner.system_prompt == "test prompt"
        assert runner.max_turns == 5

    def test_runner_default_system_prompt(self):
        """测试默认系统提示词。"""
        from {{ package_name }}.agent import AgentRunner, output_format_schema

        class DummyOutput(BaseModel):
            value: str

        schema = output_format_schema(DummyOutput)
        runner = AgentRunner(schema=schema)

        assert "有帮助" in runner.system_prompt


class TestPredefinedSchemas:
    """预定义 Schema 工厂。"""

    def test_sentiment_schema_structure(self):
        """测试情感分析 Schema 结构。"""
        from {{ package_name }}.agent import sentiment_schema

        schema = sentiment_schema()

        assert schema["type"] == "json_schema"
        props = schema["schema"]["properties"]
        assert "sentiment" in props
        assert "confidence" in props
        assert "keywords" in props

    def test_code_review_schema_structure(self):
        """测试代码审查 Schema 结构。"""
        from {{ package_name }}.agent import code_review_schema

        schema = code_review_schema()

        assert schema["type"] == "json_schema"
        props = schema["schema"]["properties"]
        assert "score" in props
        assert "issues" in props
        assert "overall" in props
