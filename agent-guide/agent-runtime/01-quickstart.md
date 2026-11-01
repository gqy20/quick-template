# 快速开始

用 Claude Agent SDK 做一次结构化查询：给定 Prompt，拿到通过 Pydantic
校验的结果对象。

## 安装

Agent SDK 是可选依赖：

```bash
uv sync --extra agent
```

未安装时调用会抛出 `RuntimeError`，提示补装该 extra。

## 最小示例

```python
import asyncio

from your_package.agent_models import SentimentOutput
from your_package.agent import structured_query

TEXT = "这家店的服务体验超出预期。"


async def main() -> None:
    result = await structured_query(
        f"分析下面文本的情感：{TEXT}",
        SentimentOutput,
    )
    print(result.model_dump_json(indent=2))


asyncio.run(main())
```

`structured_query` 是三合一入口：加载 `config/agent.yaml`、从 Pydantic 模型
生成 JSON Schema、执行查询并校验结果。

- 返回值是 `SentimentOutput` 实例，不是 dict。
- 失败按类型抛出，见下节。
- 需要 `ANTHROPIC_API_KEY`：写进项目根目录的 `.env`，程序启动时由
  `load_environment()` 加载。

## 配置来源

`load_environment()` 在读取配置前调用一次：

```python
from your_package import load_environment

load_environment()
```

它做两件事：

1. 加载 `.env` 并**覆盖**宿主同名变量 —— 宿主 shell 里可能有指向其他网关的
   `ANTHROPIC_BASE_URL`，只在 `.env` 中显式声明才能压过它。未声明的变量
   仍沿用宿主值。
2. 当 `ANTHROPIC_API_KEY` 存在时移除 `ANTHROPIC_AUTH_TOKEN`。两者并存时
   SDK 会同时发出两种认证头，只校验 `Authorization` 的网关会拒掉合法 Key。

`uv run python -m your_package.main` 和 `run_api()` 已经调用过它；作为库
直接调用 `structured_query` 时，先自己调一次。

## 错误处理

所有失败都继承 `AgentError`（本身是 `RuntimeError`），按处理方式区分：

| 异常 | 触发 | 建议处理 |
|---|---|---|
| `AgentConnectionError` | CLI 未安装或连不上 | 补装 `claude-agent-sdk` 或检查 CLI |
| `AgentProcessError` | 子进程失败、协议解析错误 | 读 `exit_code` / `stderr` 后重试 |
| `AgentBudgetExceededError` | 达到 `max_turns` 或 `max_budget_usd` | 调整上限或拆分任务 |
| `AgentRateLimitError` | API 限流被拒 | 按 `resets_at` 等待后重试 |
| `AgentOutputError` | 没拿到符合 Schema 的结果 | 改 Prompt 或放宽输出模型 |

```python
from your_package.agent import AgentBudgetExceededError, AgentError, structured_query

try:
    result = await structured_query(prompt, SentimentOutput)
except AgentBudgetExceededError as error:
    print(f"超出上限: turns={error.num_turns}")
except AgentError as error:
    print(f"执行失败: {type(error).__name__}: {error}")
```

SDK 自己的异常（`CLINotFoundError`、`ProcessError`、`CLIJSONDecodeError` 等）
会被映射成上面的类型，原始异常保留在 `__cause__`。

## 三种调用方式

| 方式 | 用法 | 适用 |
|---|---|---|
| 默认 | `structured_query(prompt, Model)` | 自动读 `config/agent.yaml` |
| 指定配置文件 | `structured_query(prompt, Model, config_path="other.yaml")` | 多套环境配置 |
| 传入配置对象 | `structured_query(prompt, Model, config=AgentConfig(...))` | 代码内动态构造 |

`config` 与 `config_path` 互斥，同时传入抛 `ValueError`。

## 自定义 Prompt

字符串 Prompt 直接用；需要版本管理和变量契约时用 Prompt Registry：

```python
from your_package.prompt import PromptRegistry

prompts = PromptRegistry("config/prompts")
prompt = prompts.render("sentiment", text=TEXT)
result = await structured_query(prompt, SentimentOutput)
```

传入 `RenderedPrompt` 时，其 `instructions` 会作为 Claude Code preset 的
system prompt 追加，Prompt 的 id、版本和摘要会写入运行日志。
详见 [Prompt 专题](../prompts/01-create-prompt.md)。

## 需要更多控制时

`structured_query` 适合快速调用。需要控制事件日志、复用配置或逐步观察
消息时，直接用 `AgentRunner`：

```python
from your_package.agent import AgentConfig, AgentRunner, output_format_schema

config = AgentConfig.from_yaml("config/agent.yaml")
runner = AgentRunner(
    schema=output_format_schema(SentimentOutput),
    config=config,
)
result = await runner.run("分析下面文本的情感：" + TEXT, SentimentOutput)
```

`AgentRunner` 额外提供：

- `runner.events` —— `AgentEventLogger` 实例，可注入自定义日志器
- `runner.run()` 逐条消费 SDK 消息并渲染到终端

## 下一步

- [运行配置](02-configuration.md) —— `config/agent.yaml` 逐项说明
- [工具与权限](03-tools-and-permissions.md) —— 开放哪些工具、如何限制
- [MCP 与 Skills](04-mcp-and-skills.md) —— 接外部服务和项目 Skill
- [Session 与恢复](05-session-and-resume.md) —— 持久状态与 resume
