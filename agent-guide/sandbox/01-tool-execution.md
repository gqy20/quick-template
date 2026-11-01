# 让工具在沙箱里执行

智能体默认在本机执行工具：模型输出一条 shell 命令，代码就在当前环境跑。
一旦模型被诱导执行危险命令，影响直接落在宿主机上。把工具调用移进沙箱，
可以把「模型能做什么」交给沙箱策略决定，而不是交给模型自觉。

先用一句话定方向：**能靠权限和沙箱解决的，不要靠 Prompt 约束模型。**

## 优先用 SDK 自带沙箱

Claude Agent SDK 的 `sandbox` 选项提供 OS 级隔离：macOS 用 Seatbelt，
Linux / WSL2 用 bubblewrap。它约束 **shell 命令及其子进程**，边界由内核
强制，命令运行期间一直生效。

```yaml
# config/agent.yaml
sandbox:
  enabled: true
  failIfUnavailable: true      # 依赖缺失时直接失败，不要静默降级
  allowUnsandboxedCommands: false
  network:
    allowedDomains: []         # 留空即禁止出网
```

```python
# 或代码里传入
config = AgentConfig(sandbox={"enabled": True, "failIfUnavailable": True})
```

必须知道的三条边界：

| 边界 | 含义 |
|---|---|
| 只管 shell 命令 | Read / Edit / Write / WebFetch / WebSearch 等内置工具**在沙箱外**，靠 `tools`、`allowed_tools`、`permission_mode` 管 |
| 默认读权限很宽 | 连 `~/.ssh`、`~/.aws/credentials` 都能读，需要按需收紧 |
| 失败会降级 | 缺依赖时默认**不沙箱直接跑**，所以 `failIfUnavailable: true` 不能省 |

Linux 还需要 `bubblewrap` 与 `socat`。原生 Windows 不支持，用 WSL2。

**结论：只要开放了 shell 工具，就开沙箱并设 `failIfUnavailable`；内置工具
继续用允许列表收窄。** 两者互补，不是二选一。

## 需要更强隔离时：外部沙箱

内置沙箱不够时（例如要把文件系统也隔离、或跨语言运行时），才考虑把工具
执行放到独立沙箱进程里。下面的结构适用于这种场景，代价是组件变多。

### 结构：模型在宿主，工具在沙箱

```
宿主                         沙箱
┌──────────────────┐         ┌──────────────────┐
│ 模型调用          │         │ 文件系统          │
│ Agent 循环        │──工具──▶│ 进程执行          │
│ 密钥              │  调用   │ 策略检查          │
└──────────────────┘         └──────────────────┘
```

关键点：**只有工具调用穿过边界**。模型请求、凭据、编排逻辑都留在宿主。

这条边界带来三个直接收益：

| 风险 | 默认结构 | 沙箱结构 |
|---|---|---|
| 模型读取密钥 | 同进程可读 | 密钥不在沙箱，读不到 |
| 模型蔓延到其他项目 | 整个磁盘可写 | 只有挂载进去的目录可见 |
| 模型访问外网 | 继承宿主网络 | 沙箱策略决定是否放行 |

### 策略：按需要给的最小集合

外部沙箱的权限由策略声明，通常分两类：

```yaml
# 文件系统：只读系统路径，可写工作目录与临时目录
filesystem:
  read_only: [/usr, /bin, /lib, /etc]
  read_write: [/sandbox, /tmp]

# 网络：留空表示完全禁止出网
network: []
```

**如果模型在宿主调用、工具在沙箱执行，沙箱通常不需要出网。** 模型本身的
网络由宿主负责，沙箱只需要跑命令、读写文件。这个组合最省心：网络策略
留空即可，不用担心模型在沙箱里探测外部服务。

反过来，如果工具需要访问 PyPI、内部 API，就单独声明目标主机和端口，
不要整段放开。

判断标准很简单：**沙箱里每多一条网络规则，就多一个模型可以触发外部副作
用的入口。**

### 坑一：并行工具调用会让「写后读」失败

模型可以在一轮里同时给出多个工具调用，LangGraph 会**并发执行**它们。

```python
# 模型一次返回两个调用
write_file(path="hello.py", content="print('hi')")
run_shell("python hello.py")  # ← 可能先执行
```

如果写操作是一次完整的往返（例如经由沙箱 exec 传输文件内容），而读操作
只是短命令，读会先赢：

```
python hello.py
python: can't open file 'hello.py': [Errno 2] No such file or directory
```

**写其实成功了**，只是发生在读之后。这类错误很难排查，因为错误信息指向
「文件不存在」，而文件最终确实存在。

修复方式是把工具的底层执行串行化：

```python
from functools import wraps
from threading import Lock


def serialize(backend):
    """把后端的底层执行串行化，恢复写后读的顺序。"""
    lock = Lock()
    original = backend.exec

    @wraps(original)
    def locked(*args, **kwargs):
        with lock:
            return original(*args, **kwargs)

    backend.exec = locked
    return backend
```

要点：**锁要加在所有操作都会经过的那一层**。如果只在写路径加锁，读路径
仍然可以插进来，问题不变。反过来，如果可以证明模型不会在同批次里发写和
读，这层锁可以不要 —— 但通常证明不了。

代价是所有工具调用串行，失去并行收益。对「一次生成里工具调用只有几次」
的场景可以接受；如果工具调用量大且相互独立，按会话或按路径分段加锁。

## 坑二：环境变量会悄悄改写模型流量

宿主机上常有其他工具注入的模型配置。例如 Claude Code 会在 shell 里留下
`ANTHROPIC_BASE_URL` 和 `ANTHROPIC_AUTH_TOKEN`，指向它自己的网关。

结果：你用 A 网关的 key，请求被发到 B 网关，返回 `401` 或"令牌已过期"。
看起来像 key 失效，实际是地址被改写。

同时还有第二个陷阱：Anthropic SDK 在 `ANTHROPIC_API_KEY` 和
`ANTHROPIC_AUTH_TOKEN` 都存在时，会**同时发出两种认证头**。只校验
`Authorization` 的网关会拿 `AUTH_TOKEN` 判失败，即使 `API_KEY` 是有效的。

处理方式是在程序启动时显式加载配置并清理冲突：

```python
import os

from dotenv import load_dotenv


def load_environment() -> None:
    # 项目 .env 优先于宿主环境：显式声明 ANTHROPIC_BASE_URL 才能覆盖注入值
    load_dotenv(override=True)

    # 两种认证头同时存在时，网关可能拒掉合法的 API Key
    if os.environ.get("ANTHROPIC_API_KEY"):
        os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
```

两条都要写：`override=True` 解决「地址被改」，清掉 `AUTH_TOKEN` 解决
「认证头冲突」。

注意 `override=True` 只覆盖 `.env` 里存在的变量。`.env` 没写
`ANTHROPIC_BASE_URL` 时，宿主值仍会生效 —— 想去掉它，就在 `.env` 里写
空值或显式写正确地址。

## 什么时候值得引入沙箱

沙箱不是免费的：多一个组件、多一套策略、调试链路变长，CI 通常也跑不了
完整路径。按风险决定：

| 场景 | 建议 |
|---|---|
| 只做结构化抽取、不执行代码 | 不需要沙箱 |
| 执行模型生成的 shell 命令 | 需要 |
| 处理不可信输入（外部网页、用户文件） | 需要 |
| 只在受控数据上做只读分析 | 视情况，通常靠工具白名单即可 |

退一步的做法是**不给执行类工具**：只提供读文件、查数据库这类受限工具，
把风险面压到最小。模板默认 `tools: []` 就是这个思路 —— 能读能推理，
不能执行。

只有在确实需要「让模型写代码并运行」时，沙箱的复杂度才值得。
