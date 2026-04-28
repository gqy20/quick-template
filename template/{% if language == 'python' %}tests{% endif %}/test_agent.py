"""Agent SDK 示例代码的测试。

注意：这些测试需要实际运行 Claude Agent SDK，
在 CI 环境中可能需要跳过或使用 mock。
"""

import pytest

from {{ package_name }}.logger import console


class TestAgentModule:
    """测试 agent 模块导入。"""

    def test_agent_module_import(self):
        """测试 agent 模块可以成功导入。"""
        from {{ package_name }} import agent
        assert agent is not None

    def test_agent_has_demo_functions(self):
        """测试 agent 模块包含演示函数。"""
        from {{ package_name }} import agent

        assert hasattr(agent, "demo_query_mode")
        assert hasattr(agent, "demo_client_mode")
        assert hasattr(agent, "demo_structured_output")
        assert hasattr(agent, "main")

    def test_agent_async_functions_are_coroutines(self):
        """测试演示函数是异步函数。"""
        import inspect
        from {{ package_name }} import agent

        assert inspect.iscoroutinefunction(agent.demo_query_mode)
        assert inspect.iscoroutinefunction(agent.demo_client_mode)
        assert inspect.iscoroutinefunction(agent.demo_structured_output)


class TestStructuredSchemas:
    """测试结构化输出的 Schema 定义。"""

    def test_sentiment_schema_structure(self):
        """验证情感分析的 Schema 结构正确。"""
        from {{ package_name }}.agent import demo_structured_output

        import inspect

        source = inspect.getsource(demo_structured_output)
        assert "sentiment_schema" in source
        assert "json_schema" in source
        assert '"sentiment"' in source
        assert '"confidence"' in source

    def test_code_review_schema_structure(self):
        """验证代码审查的 Schema 结构正确。"""
        from {{ package_name }}.agent import demo_structured_output

        import inspect

        source = inspect.getsource(demo_structured_output)
        assert "code_review_schema" in source
        assert "issues" in source
        assert "severity" in source


class TestAgentOptions:
    """测试 ClaudeAgentOptions 配置。"""

    def test_options_can_be_imported(self):
        """测试可以成功导入 ClaudeAgentOptions。"""
        try:
            from claude_agent_sdk import ClaudeAgentOptions

            options = ClaudeAgentOptions(
                system_prompt="test",
                permission_mode="acceptEdits",
            )
            assert options.system_prompt == "test"
            assert options.permission_mode == "acceptEdits"
        except ImportError:
            pytest.skip("claude-agent-sdk not installed")

    def test_query_function_can_be_imported(self):
        """测试可以成功导入 query 函数。"""
        try:
            from claude_agent_sdk import query

            assert callable(query)
        except ImportError:
            pytest.skip("claude-agent-sdk not installed")

    def test_client_can_be_imported(self):
        """测试可以成功导入 ClaudeSDKClient。"""
        try:
            from claude_agent_sdk import ClaudeSDKClient

            assert callable(ClaudeSDKClient)
        except ImportError:
            pytest.skip("claude-agent-sdk not installed")
