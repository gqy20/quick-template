# 事件日志

Agent 运行日志是结构化 JSONL，一行一个事件。它的用途是**排障和审计**，
不是记录业务数据。

## 输出位置

| Runtime | 默认路径 |
|---|---|
| Claude Agent SDK | `logs/agent/events.jsonl` |
| LangGraph | `logs/agent/langgraph.jsonl` |

按大小轮转：`max_bytes`（默认 10 MiB）和 `backup_count`（默认 5）控制。

## 记录什么

| 内容 | 记录 | 说明 |
|---|---|---|
| 事件名、时间、级别 | 是 | 结构化字段 |
| 模型标识、Prompt id 与版本 | 是 | 追溯依据 |
| 工具名、调用 id | 是 | 关联同一次调用 |
| 工具参数的**键名** | 是 | 知道传了哪些字段 |
| 工具参数的**值** | 否 | 可能含用户数据 |
| 工具结果的**内容** | 否 | 同上 |
| 耗时、状态、异常类型 | 是 | 排障核心信息 |
| token / 费用用量 | 是 | 聚合值，非逐 token |
| 完整 transcript | 否（默认） | 由 `debug_file` 单独控制 |

## 主要事件

Claude Agent SDK 路径：

| 事件 | 时机 |
|---|---|
| `run_started` | 一次查询开始，带 Prompt 元数据和变量名 |
| `run_configured` | 配置生效（工具、权限、MCP 来源、状态模式） |
| `run_failed` | 查询失败，带 `error_type` 和脱敏后的错误摘要 |
| `tool_call_started` / `tool_call_completed` | 工具调用边界 |
| `rate_limit` | 触发限流 |
| `system_event` | SDK 系统事件，只保留安全字段 |

LangGraph 路径：

| 事件 | 时机 |
|---|---|
| `graph_started` / `graph_resumed` | 图开始或从检查点恢复 |
| `graph_interrupted` | 图暂停，带中断数量 |
| `tool_call_started` / `tool_call_completed` / `tool_call_failed` | 工具审计 |
| `tool_call_interrupted` | 工具内触发 `interrupt()` |

事件名稳定，动态数据放字段里 —— 便于按事件名过滤。

## 脱敏

`redact_text` 处理常见泄露：

| 模式 | 处理 |
|---|---|
| `Authorization: Bearer xxx` | `[REDACTED]` |
| `api_key=` / `token:` / `password=` / `secret=` | `[REDACTED]` |
| `sk-...` 形态的密钥 | `[REDACTED]` |

错误摘要截断到 1000 字符，SDK 消息截断到 2000 字符。

**这是兜底，不是保证。** 自定义字段里的敏感数据不会被自动识别 —— 写
`emit()` 前自己确认字段内容。

## 关联字段

排障时按这些字段串起来：

| 字段 | 关联 |
|---|---|
| `run_id` | 一次查询 |
| `thread_id` | LangGraph 的一次会话（可跨多次 run） |
| `tool_call_id` | 一次工具调用 |
| `prompt_id` + `prompt_version` | 用的是哪份 Prompt |
| `definition_sha256` | Prompt 文件的实际内容摘要 |

`definition_sha256` 与 `prompt_version` 不一致时，说明改了文件没升版本。

## 自己写事件

```python
runner.events.emit(
    "custom_step",
    step="validate",
    duration_ms=120,
    status="ok",
)
```

字段会被序列化进 JSONL。**不要传正文、路径、用户输入** —— 需要时传
标识符，内容去别处查。

## debug_file 是另一回事

```yaml
logging:
  debug_file: null
```

设为路径时，SDK 会写出**完整上下文**，包括 Prompt 全文和模型原始响应。
它会进 `.gitignore`，且**不得在生产开启**。

两者区别：

| | JSONL 事件日志 | `debug_file` |
|---|---|---|
| 内容 | 元数据和聚合值 | 完整 transcript |
| 脱敏 | 自动 + 人工 | 无 |
| 生产 | 开 | 关 |

## 检查清单

- [ ] 日志路径在 `.gitignore` 里
- [ ] 生产环境 `debug_file: null`
- [ ] 自定义 `emit()` 字段不含正文、路径、凭据
- [ ] 轮转参数与磁盘容量匹配
- [ ] Prompt 元数据随运行记录，能追溯版本
