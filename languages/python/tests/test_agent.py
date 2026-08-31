"""Agent SDK 模块测试。"""

import json

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
        from {{ package_name }}.agent import AgentConfig, AgentRunner, output_format_schema

        class DummyOutput(BaseModel):
            value: str

        schema = output_format_schema(DummyOutput)
        config = AgentConfig(system_prompt="test prompt", max_turns=5)
        runner = AgentRunner(
            schema=schema,
            config=config,
        )

        assert runner.schema == schema
        assert runner.config.system_prompt == "test prompt"
        assert runner.config.max_turns == 5

    def test_runner_default_system_prompt(self):
        """测试默认系统提示词。"""
        from {{ package_name }}.agent import AgentRunner, output_format_schema

        class DummyOutput(BaseModel):
            value: str

        schema = output_format_schema(DummyOutput)
        runner = AgentRunner(schema=schema)

        assert isinstance(runner.config.system_prompt, dict)
        assert runner.config.system_prompt["preset"] == "claude_code"


class TestAgentConfig:
    """AgentConfig: SDK 原生选项映射与配置加载。"""

    def test_safe_defaults(self):
        from {{ package_name }}.agent import AgentConfig

        config = AgentConfig()

        assert config.tools == []
        assert config.skills == []
        assert config.setting_sources == ["project"]
        assert config.permission_mode == "dontAsk"
        assert config.strict_mcp_config is True

    def test_loads_yaml_and_maps_native_options(self, tmp_path):
        from {{ package_name }}.agent import AgentConfig

        path = tmp_path / "agent.yaml"
        path.write_text(
            "model: claude-sonnet-4-6\n"
            "tools: [Read, Grep]\n"
            "allowed_tools: [Read]\n"
            "skills: [review]\n"
            "mcp_config: .mcp.json\n"
            "strict_mcp_config: true\n"
            "setting_sources: [project]\n"
        )

        config = AgentConfig.from_yaml(path)
        options = config.to_option_kwargs({"type": "json_schema", "schema": {}})

        assert options["model"] == "claude-sonnet-4-6"
        assert options["tools"] == ["Read", "Grep"]
        assert options["allowed_tools"] == ["Read"]
        assert options["skills"] == ["review"]
        assert options["mcp_servers"] == str(tmp_path / ".mcp.json")
        assert config.cwd == tmp_path
        assert options["strict_mcp_config"] is True
        assert options["setting_sources"] == ["project"]


class TestPromptRegistry:
    """Prompt YAML: 版本、变量契约和安全渲染。"""

    def test_loads_and_renders_versioned_prompt(self, tmp_path):
        from {{ package_name }}.prompt import PromptRegistry

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        (prompt_dir / "review.yaml").write_text(
            "id: review\n"
            "version: 1.2.0\n"
            "description: Review code\n"
            "instructions: Review carefully.\n"
            "user_template: |\n"
            "  Review $language code:\n"
            "  $code\n"
            "variables:\n"
            "  language: {required: true, sensitive: false}\n"
            "  code: {required: true, sensitive: true}\n"
        )

        prompt = PromptRegistry(prompt_dir).render(
            "review",
            language="Python",
            code="print('ok')",
        )

        assert prompt.id == "review"
        assert prompt.version == "1.2.0"
        assert prompt.instructions == "Review carefully."
        assert "Python" in prompt.text
        assert "print('ok')" in prompt.text
        assert prompt.sensitive_variables == frozenset({"code"})
        assert len(prompt.definition_sha256) == 64

        from {{ package_name }}.agent import claude_system_prompt

        claude_prompt = claude_system_prompt(prompt.instructions)
        assert claude_prompt["append"] == prompt.instructions

    def test_rejects_missing_or_unknown_variables(self, tmp_path):
        from {{ package_name }}.prompt import PromptRegistry

        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()
        (prompt_dir / "simple.yaml").write_text(
            "id: simple\n"
            "version: 1.0.0\n"
            "description: Simple prompt\n"
            "instructions: Be concise.\n"
            "user_template: 'Hello $name'\n"
            "variables:\n"
            "  name: {required: true}\n"
        )
        registry = PromptRegistry(prompt_dir)

        with pytest.raises(ValueError, match="Missing"):
            registry.render("simple")
        with pytest.raises(ValueError, match="Unknown"):
            registry.render("simple", name="Ada", extra="no")


class TestRuntimeState:
    """Claude CLI transcript 的隔离模式。"""

    def test_ephemeral_state_is_removed_after_run(self, tmp_path):
        from pathlib import Path

        from {{ package_name }}.agent_state import RuntimeStateConfig, runtime_state_env

        config = RuntimeStateConfig(mode="ephemeral")
        with runtime_state_env(config, tmp_path) as env:
            state_dir = Path(env["CLAUDE_CONFIG_DIR"])
            assert state_dir.is_dir()
            assert tmp_path not in state_dir.parents
        assert not state_dir.exists()

    def test_project_state_is_persistent_and_default_is_untouched(self, tmp_path):
        from pathlib import Path

        from {{ package_name }}.agent_state import RuntimeStateConfig, runtime_state_env

        project = RuntimeStateConfig(mode="project", project_path=".agent-state/claude")
        with runtime_state_env(project, tmp_path) as env:
            state_dir = Path(env["CLAUDE_CONFIG_DIR"])
            assert state_dir == tmp_path / ".agent-state" / "claude"
        assert state_dir.is_dir()

        with runtime_state_env(RuntimeStateConfig(mode="default"), tmp_path) as env:
            assert "CLAUDE_CONFIG_DIR" not in env


class TestAgentEventLogger:
    """AgentEventLogger: 安全的结构化执行日志。"""

    def test_writes_jsonl_without_prompt_content(self, tmp_path):
        from {{ package_name }}.agent_log import AgentEventLogger

        path = tmp_path / "agent.jsonl"
        events = AgentEventLogger(path=path)
        events.run_started(
            prompt="secret prompt",
            output_model="Review",
            metadata={
                "prompt_id": "review",
                "prompt_version": "1.0.0",
                "definition_sha256": "a" * 64,
                "variable_names": ["code"],
                "sensitive_variables": ["code"],
            },
        )

        record = json.loads(path.read_text().splitlines()[0])
        assert record["event"] == "run_started"
        assert record["prompt_chars"] == len("secret prompt")
        assert record["prompt_id"] == "review"
        assert record["prompt_version"] == "1.0.0"
        assert record["definition_sha256"] == "a" * 64
        assert record["variable_names"] == ["code"]
        assert record["sensitive_variables"] == ["code"]
        assert "prompt_sha256" in record
        assert "secret prompt" not in path.read_text()

    def test_tool_event_logs_keys_not_values(self, tmp_path):
        from {{ package_name }}.agent_log import AgentEventLogger

        class ToolUseBlock:
            id = "tool-1"
            name = "mcp__db__query"
            input = {"query": "SELECT secret", "token": "sk-private"}

        path = tmp_path / "agent.jsonl"
        events = AgentEventLogger(path=path)
        events.observe_block(ToolUseBlock())

        text = path.read_text()
        record = json.loads(text.splitlines()[0])
        assert record["input_keys"] == ["query", "token"]
        assert "SELECT secret" not in text
        assert "sk-private" not in text

    def test_tool_result_records_duration_without_content(self, tmp_path):
        from {{ package_name }}.agent_log import AgentEventLogger

        class ToolUseBlock:
            id = "tool-1"
            name = "Read"
            input = {"file_path": "/private/file"}

        class ToolResultBlock:
            tool_use_id = "tool-1"
            content = "private file content"
            is_error = False

        path = tmp_path / "agent.jsonl"
        events = AgentEventLogger(path=path)
        events.observe_block(ToolUseBlock())
        events.observe_block(ToolResultBlock())

        record = json.loads(path.read_text().splitlines()[1])
        assert record["event"] == "tool_result"
        assert isinstance(record["duration_ms"], int)
        assert "private file content" not in path.read_text()

    def test_stderr_callback_redacts_tokens(self, tmp_path):
        from {{ package_name }}.agent_log import AgentEventLogger

        path = tmp_path / "agent.jsonl"
        events = AgentEventLogger(path=path)
        events.capture_stderr("[ERROR] token=sk-ant-secret failed")

        text = path.read_text()
        assert "sdk_stderr" in text
        assert "sk-ant-secret" not in text
        assert "[REDACTED]" in text


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
