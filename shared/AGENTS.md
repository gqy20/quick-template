# {{ project_name }} Agent 执行契约

本文件约束在本仓库中工作的编码 Agent。它不是运行时 Agent Prompt，
不能替代产品、架构、设计或发布文档。

## 目的与范围

默认目标是用最小、正确、可验证的改动完成用户明确要求，并保护代码、
数据、用户已有修改和外部系统。模型应在明确范围内自主推进，在产品含义、
权限或不可逆副作用不明确时停止并请求方向。

## 指令优先级

发生冲突时按以下顺序判断：

1. 用户当前请求和明确授权。
2. 权限、安全、Secret、数据完整性与不可逆副作用。
3. 当前需求正确性和公共契约。
4. 测试与当前架构不变量。
5. 最小改动和交付效率。
6. 性能、审美和未来扩展性。

子目录中的 `AGENTS.md` 可以增加或收紧局部规则，但不得放宽根目录的
安全、权限和数据完整性边界。

## 项目事实

- 项目：{{ project_name }}
- 描述：{{ description }}
- 语言：{{ language }}
{{#if add_api}}- API：启用
{{#else}}- API：未启用
{{#endif}}
{{#if language == 'python'}}- 运行时：Python {{ python_version }}+
- 依赖管理：uv
- 源码：`src/{{ package_name }}/`
- 测试：pytest；lint / format：Ruff；类型检查：Mypy
- Agent 配置：`config/agent.yaml`；Prompt：`config/prompts/*.yaml`
- LangGraph 配置：`config/runtimes/langgraph.yaml`
- MCP：`.mcp.json`；Skills：`.claude/skills/`
- Agent 审计日志：`logs/agent/events.jsonl`，默认不得记录正文或工具值
- Claude CLI 完整 transcript 默认使用临时目录，不写入用户全局 `~/.claude`
{{#elif language == 'golang'}}- 运行时：Go {{ go_version }}+
- 依赖管理：Go Modules
- 入口：`cmd/{{ project_slug }}/`
- 测试：go test；lint / format：golangci-lint / gofmt
{{#elif language == 'typescript'}}- 运行时：Node.js {{ node_version }}+ / TypeScript
- 依赖管理：npm
- 源码：`src/`
- 测试：Vitest；lint / format：Biome；类型检查：tsc
{{#endif}}

代码、测试、当前配置和已接受的架构决策描述已实现事实。Roadmap、TODO、
草案和 Proposed 设计只能作为计划，不能当作当前能力。

## 事实源与文档路由

- 用户当前可用能力、安装与运行：`README.md`
- Agent 执行规则：本文件
- 前端视觉与交互契约：`DESIGN.md`
- 版本变化：`docs/CHANGELOG.md`
- 工程命令：`Makefile`
- 线上门禁：`.github/workflows/`
{{#if language == 'python'}}- Python 依赖与工具配置：`pyproject.toml`
- Claude Agent SDK 配置：`config/agent.yaml`、`config/prompts/`、
  `.mcp.json`、`.claude/skills/`
{{#elif language == 'golang'}}- Go 模块与依赖：`go.mod`
{{#elif language == 'typescript'}}- Node 依赖与脚本：`package.json`
{{#endif}}

只读取当前任务需要的文档和代码。若文档与代码冲突，先核对测试、Schema
和运行结果；不得静默选择更符合预期的一方。

## 按请求类型确定授权

- “分析、检查、解释、评审、先说明”：只读，不修改文件。
- “规划、设计、给方案”：输出方案，不提前实现。
- “诊断”：查明原因和证据；除非明确要求，否则不修复。
- “修改文档”：只修改相关文档及必要的文档测试。
- “修复”：修复已确认问题，不顺手重构相邻模块。
- “实现、构建”：实现明确需求及必要支撑改动。
- “重构”：可调整指定范围结构，不扩展产品能力。
- “提交、推送、发布”：只执行用户明确点名的层级。
- 用户要求“不运行”时，不启动测试、服务、脚本、浏览器或外部探测。

分析许可不等于修改许可，修改许可不等于 commit，commit 不等于 push，
push 不等于 Tag、Release、部署或对外发送消息。

## 工作方式

开始前在内部明确 Deliverable、Scope、Non-goals、Verification 和 Stop 条件。

- 从用户指定入口、直接依赖和相关测试开始。
- 一次性完成必要发现，再集中修改，避免反复扫描全仓库。
- 能安全推断的小细节直接推进；会改变产品含义时再询问。
- 发现范围外问题只在交付中记录，不主动实现、建 Issue 或修改 Roadmap。
- 达到完成标准后停止，不因“还可以更优雅”继续扩展。

## 变更与依赖门禁

- 优先使用当前架构、标准库、框架原生能力和已有组件。
- 原生能力不足时写薄适配；只有项目独有领域规则才新增领域模块。
- 局部修复足够时避免跨模块重构。
- 不为假设的未来需求增加抽象、接口、兼容层或配置。
- 不同时实现多个备选方案。
- 新增生产依赖前必须确认现有能力无法正确满足当前需求。
- 公共 API、Schema、配置或持久化格式变化必须说明兼容影响。

只有以下情况允许扩大范围：

1. 不扩大无法满足用户明确需求；
2. 不扩大将导致代码不可运行、测试失败或数据损坏；
3. 当前改动产生权限、安全、幂等或不可逆风险；
4. 用户明确批准。

## 架构与数据不变量

- 入口层负责协议适配，业务规则进入明确的领域或服务边界。
- 结构化数据使用 Schema 和类型校验，不用自由文本猜测控制状态。
- 展示层不得成为业务事实源。
- 错误、空值与缺失数据必须显式表达，不得静默伪造成成功或零值。
- 写操作需要明确副作用；可能重试的外部写入应有稳定幂等键。
- Secret 只来自环境或 Secret 管理，不得写入源码、日志或截图。
{{#if add_api}}- API 请求与响应使用稳定模型；新增、删除或重命名字段时同步测试和文档。
- 健康检查只报告服务真实状态，不触发业务写入。
- 外部请求必须有超时、错误传播和可审计日志；不得无限重试。
{{#endif}}
{{#if language == 'python'}}- 保持 src layout；公共导出显式维护，不依赖隐式路径注入。
- 同步与异步边界必须清楚，不在异步路径中执行无界阻塞操作。
- 普通应用启动和默认测试保持离线；真实 Agent 只能通过显式入口运行。
- Agent 日志只记录运行元数据、能力加载、工具名、字段名和用量；正文需另行授权。
- Prompt 行为变化必须升级 YAML 版本；日志记录 Prompt ID、版本和摘要。
- Session 需要 resume 时才启用 project 状态；不得把 runtime state 写进 `.claude/`。
- Claude 与 LangGraph 共享 Prompt、输出模型和日志；不得伪造 MCP/Skills 等价语义。
- LangGraph State 只保存可 checkpoint 数据；model、logger 和 Schema 放入 context。
{{#elif language == 'golang'}}- `internal/` 保存私有实现，`pkg/` 只放置真正稳定、可复用的公开能力。
- 错误必须保留上下文并由调用方处理，不以日志代替错误返回。
{{#elif language == 'typescript'}}- 保持 ESM 与严格类型；不得用 `any` 或无说明断言绕过契约。
- 浏览器与服务端边界显式，禁止把 Secret 打进客户端 bundle。
{{#endif}}

## 前端与设计契约

仓库出现用户界面、页面、组件、样式或可视化时，`DESIGN.md` 自动成为
前端改动的必读规范。

- 设计先服从产品任务、信息层级和可访问性，再追求装饰。
- 颜色、字体、间距、圆角、阴影和动效必须来自语义 Token。
- 不在组件中散写与 Token 重复的静态视觉值。
- 修改视觉方向、Token 或跨页面组件规则时同步 `DESIGN.md`。
- 截图、差异、发现与迭代历史写入 `design-qa.md` 或
  `docs/design-qa/`，不得污染稳定规范。
- UI 改动必须验证目标视口、键盘焦点、文本缩放、空/错/加载态和
  `prefers-reduced-motion`。

## 工作区与 Git 安全

- 修改前检查 `git status --short --branch`。
- 用户已有修改均属于用户；不得覆盖、回滚、格式化或提交无关改动。
- 不使用会丢失工作区内容的 Git 命令。
- 删除、移动、批量改写前先解析精确目标和可恢复性。
- 未经明确要求，不 commit、push、创建 PR、Tag、Release、部署或修改远端。
- 提交时只暂存当前任务文件；提交前检查 cached diff 和 `diff --check`。
- `.env`、Token、真实响应、数据库、日志、缓存和构建产物不得提交。

## 验证阶梯

用户未禁止运行时，按改动风险选择最小充分验证：

1. 文档：链接、格式、引用和 diff。
2. 局部逻辑：相关 lint / 类型检查和定向测试。
3. 公共契约或跨模块修改：`make all`。
4. 构建、依赖或发布改动：安装、构建和包级 smoke。
5. 前端改动：目标视口截图与交互 / 可访问性检查。
6. 外部系统：仅在明确授权后运行真实集成测试。

通用入口：

```bash
make check
make typecheck
make test
make all
```

{{#if language == 'python'}}Python 定向验证：

```bash
uv run ruff check <changed-paths>
uv run pytest <relevant-tests>
uv run mypy src/{{ package_name }}
```
{{#elif language == 'golang'}}Go 定向验证：

```bash
gofmt -d <changed-files>
go test <relevant-packages>
go vet ./...
```
{{#elif language == 'typescript'}}TypeScript 定向验证：

```bash
npx biome check <changed-paths>
npx tsc --noEmit
npx vitest run <relevant-tests>
```
{{#endif}}

文档修改不启动应用服务。真实模型、公网 API、设备、生产数据库和部署验证
必须单独授权。不得用固定睡眠代替服务就绪检测。

## 外部系统与发布

- 真实外部写入前确认目标、身份、环境和影响范围。
- 发布必须区分版本修改、Tag、Release、部署和产物上传；它们不是同一授权。
- 工作区不干净时不得创建发布 Tag。
- 已发布 Tag 不移动、不覆盖、不复用。
- 候选、已验证、已批准和已发布是不同状态，不得用复制或改名伪造。
- 发布任务只有在用户要求的远端状态和产物均可验证后才算完成。

## 文档规则

- README 只描述当前已实现并可使用的能力。
- 计划、Proposed、已知缺口和当前事实必须明确区分。
- 公共行为、接口或兼容边界变化同步文档和 CHANGELOG。
- 架构理由写入专门设计文档或 ADR，不把长篇理由堆入代码注释。
- 注释解释非显然约束、风险和取舍，不复述代码字面行为。
- `CLAUDE.md` 只做平台路由，不复制本文件。

## Code Review Rules

审查优先级：正确性与数据完整性 > 权限与安全 > 公共契约 >
回归风险 > 可维护性 > 性能与视觉精修。

- 标记未经请求的范围扩大、依赖、权限或外部副作用。
- 标记把 Roadmap、Mock、AI 候选或未验证状态写成当前事实。
- 标记缺少 Schema 校验、超时、错误传播、幂等或负向测试的边界变更。
- 标记用户改动被覆盖、无关文件被格式化或 Secret / 产物进入提交。
- 标记违反 `DESIGN.md` 的视觉值、交互、响应式或无障碍实现，并给出
  对应 Token、原生组件或安全路径。
- 格式问题优先交给 CI；审查意见应说明行为风险和可行修复路径。

## 完成标准

任务只有在以下条件满足时才算完成：

- 实现与用户请求、当前代码和事实源一致；
- 没有无证据扩大范围、依赖、权限或外部状态；
- 输入、输出、错误和副作用边界与改动规模匹配；
- 最小相关验证通过，或明确说明未运行及原因；
- 相关 README、CHANGELOG、DESIGN 或架构文档已同步；
- 用户已有修改未被破坏；
- 最终回复说明实际改动、验证、未验证项、产物位置和重要剩余风险。
