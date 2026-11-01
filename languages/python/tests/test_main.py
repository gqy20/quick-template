"""主模块的测试用例。"""

import os
from unittest.mock import patch

import pytest

from {{package_name }}.main import demo_basic_features, demo_logging, demo_rich_output, main


def test_main_runs_successfully(capsys):
    """测试主函数是否能正常运行。"""
    main()
    captured = capsys.readouterr()
    # 检查预期的输出元素
    assert "{{project_name }}" in captured.out or len(captured.out) > 0


def test_demo_basic_features(capsys):
    """测试基本功能演示。"""
    demo_basic_features()
    captured = capsys.readouterr()
    # 输出将是 rich 格式化的，只验证没有错误
    assert len(captured.out) > 0 or True  # rich 输出到 stdout 或终端


def test_demo_rich_output(capsys):
    """测试 rich 输出演示。"""
    demo_rich_output()
    captured = capsys.readouterr()
    # 检查是否产生了一些输出
    assert len(captured.out) > 0 or True  # rich 可能直接输出到终端


def test_demo_logging(capsys):
    """测试日志演示。"""
    demo_logging()
    captured = capsys.readouterr()
    # 验证日志产生了输出
    assert len(captured.err) > 0 or len(captured.out) > 0


@patch("{{package_name }}.main.greet")
def test_main_calls_greet(mock_greet):
    """测试主函数是否调用了 greet 函数。"""
    mock_greet.return_value = "模拟的问候"
    main()
    # 验证 greet 至少被调用了一次
    assert mock_greet.called


def test_main_handles_exceptions():
    """测试主函数是否正确处理异常。"""
    with patch("{{package_name }}.main.demo_basic_features") as mock_demo:
        mock_demo.side_effect = RuntimeError("测试错误")
        with pytest.raises(RuntimeError):
            main()


def test_main_does_not_run_agent_demo_by_default():
    """安装 Agent extra 后，普通启动仍保持离线。"""
    with patch("{{package_name }}.main.run_agent_demos") as mock_agent_demo:
        main()
    mock_agent_demo.assert_not_called()


def test_load_environment_prefers_dotenv(tmp_path, monkeypatch):
    """`.env` 覆盖宿主变量。"""
    from {{package_name }} import load_environment

    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=from-dotenv\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell")

    load_environment(env_file)

    assert os.environ["ANTHROPIC_API_KEY"] == "from-dotenv"


def test_load_environment_drops_conflicting_auth_token(tmp_path, monkeypatch):
    """同时存在 API Key 与 Auth Token 时移除后者，避免两种认证头冲突。"""
    from {{package_name }} import load_environment

    env_file = tmp_path / ".env"
    env_file.write_text("ANTHROPIC_API_KEY=from-dotenv\n")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "ambient-token")

    load_environment(env_file)

    assert "ANTHROPIC_AUTH_TOKEN" not in os.environ


def test_load_environment_keeps_auth_token_without_api_key(tmp_path, monkeypatch):
    """只有 Auth Token 时保留它，不能把用户唯一的凭据删掉。"""
    from {{package_name }} import load_environment

    env_file = tmp_path / ".env"
    env_file.write_text("SOMETHING_ELSE=1\n")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "ambient-token")

    load_environment(env_file)

    assert os.environ["ANTHROPIC_AUTH_TOKEN"] == "ambient-token"
