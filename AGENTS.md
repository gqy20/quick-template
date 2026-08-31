# quick-template Agent 执行契约

本文件约束在 quick-template 仓库中工作的编码 Agent。它服务于模板维护，
不替代生成项目中的 `AGENTS.md`、产品文档、运行时 Agent Prompt 或 Skill。

## 项目目的

quick-template 的交付物不是三套 Hello World，而是一个可安装、可验证、
可被人和 Agent 立即接管的工程基线。语言模板负责技术栈，`shared/`
负责跨项目治理契约；新增能力必须保持二者边界清楚。

非目标：

- 不追求覆盖所有语言、框架或项目类型。
- 不把可选 Agent、前端、数据库或部署能力塞入所有项目。
- 不为尚未出现的需求预建抽象、兼容层或插件系统。
- 不恢复 Copier 或第二套模板事实源。

## 指令优先级

发生冲突时按以下顺序判断：

1. 用户当前请求和明确授权。
2. 权限、安全、Secret、数据完整性与不可逆副作用。
3. 生成项目的正确性和公共契约。
4. 测试、兼容性与单一事实源。
5. 最小改动和交付效率。
6. 性能、审美和未来扩展性。

用户授权只覆盖当前请求。分析许可不等于修改许可，修改许可不等于
commit、push、Tag、Release 或其他外部写入许可。

## 项目事实

- `src/scaffold/` 是生成器实现。
- `languages/` 与 `shared/` 是唯一模板源。
- `template/` 已废弃，不得恢复第二套渲染树。
- 模板语法为变量替换及 `{{#if}}`、`{{#elif}}`、`{{#else}}`、
  `{{#endif}}` 条件块。
- wheel 必须包含全部模板资源；源码可运行但 wheel 不可用属于发布阻断。
- Python、Go、TypeScript 的 API / 非 API 六种组合都是受支持契约。

代码、测试、当前 Schema 和已合并配置描述已实现事实。Roadmap、TODO、
草案和 Proposed 设计不得当作已经实现的能力。

## 事实源与文档路由

- 安装、能力与用户边界：`README.md`
- 版本与行为变化：`CHANGELOG.md`
- Agent 维护契约：本文件
- 生成项目 Agent 契约：`shared/AGENTS.md`
- 前端设计基线：`shared/DESIGN.md`
- Python Agent 模板：`languages/python/src/{{package_name}}/agent.py`
- Agent 日志模板：`languages/python/src/{{package_name}}/agent_log.py`
- Agent 运行配置：`languages/python/config/agent.yaml`
- Prompt 资产：`languages/python/config/prompts/`
- LangGraph Runtime：`languages/python/src/{{package_name}}/langgraph_agent.py`
- LangGraph 工具与 MCP 适配：
  `languages/python/src/{{package_name}}/langgraph_tools.py`
- LangGraph 配置：`languages/python/config/runtimes/langgraph.yaml`
- MCP / Skills 配置：`languages/python/.mcp.json`、`.claude/skills/`
- 文档站实现：`docs/`
- 模板引擎契约：`src/scaffold/` 与 `tests/`
- 线上真实门禁：`.github/workflows/test.yml`

修改模板前只读取任务相关语言目录和共享文件。修改公共行为前先读相应测试；
修改 CI 时保证本地验证命令与线上命令一致。

## 按请求类型确定授权

- “分析、检查、解释、评审、先说明”：只读，不修改文件。
- “规划、设计、给方案”：输出方案或草案，不提前实现。
- “诊断”：确认原因和证据；除非请求包含修复，否则不改代码。
- “修改文档”：只修改相关文档及必要的文档测试。
- “修复”：修复已确认问题，不顺手重构相邻模块。
- “实现、构建”：实现明确需求及其必要支撑。
- “重构”：可调整指定边界内结构，不扩展为新产品能力。
- “提交、推送、发布”：只执行用户明确点名的层级。
- 用户要求“不运行”时，不启动测试、脚本、服务、浏览器或外部探测。

## 执行方式

开始前确定 Deliverable、Scope、Non-goals、Verification 和 Stop 条件。
优先一次性完成必要发现，再集中修改并按风险逐级验证。

- 从用户指定入口、直接依赖和相关测试开始。
- 证据足够后停止扩展阅读。
- 能安全推断的小细节直接推进；会改变产品含义或外部状态时再询问。
- 发现范围外问题只在交付中记录，不自动实现、建 Issue 或扩写 Roadmap。
- 达到停止条件后交付，不因“还可以更优雅”继续修改。

## 变更与扩展门禁

- 优先复用当前架构、标准库、框架原生能力和现有依赖。
- 局部修改足够时不得跨模块重构。
- 不为未来假设增加 Provider、接口、兼容层或配置项。
- 不同时实现多个备选方案。
- 新增生产依赖必须证明现有能力无法正确完成当前需求。
- 修改模板引擎或文件复制前先补回归测试。
- 新增模板变量时必须同步模型、CLI/配置、文档、测试和生成矩阵。

只有以下情况可以扩大范围：

1. 不扩大就无法满足当前验收标准；
2. 不扩大将导致生成结果不可运行、测试失败或数据损坏；
3. 当前改动产生明确的权限、安全、幂等或不可逆风险；
4. 用户明确批准。

## 架构不变量

- 生成结果只由 `languages/` 和 `shared/` 组合产生。
- 语言目录不得复制共享治理文件；共享目录不得硬编码语言实现。
- 条件关闭的文件必须完全消失，不得留下无效 import、空 workflow 或占位注释。
- 文本模板与二进制资源使用不同复制路径。
- 派生变量必须稳定、可验证，并保留用户显式配置。
- 输出到非空目录默认失败；覆盖必须显式使用 `--force`。
- 核心 CLI 依赖保持最小；示例和集成依赖进入可选 extra。
- `AGENTS.md` 是跨 Agent 规范事实源；`CLAUDE.md` 只做路由或平台特有补充。
- `DESIGN.md` 保存稳定设计契约；截图、差异和迭代历史写入独立 Design QA。
- 多 Runtime 共享 Prompt、Pydantic 输出和高层日志，但保留各自原生状态与工具语义。
- `.mcp.json` 只声明连接；LangGraph MCP 工具必须由 Runtime 配置显式授权，
  协议与会话交给官方 Adapter。

## 工作区与 Git 安全

- 开始修改前检查 `git status --short --branch`。
- 用户已有修改属于用户；不得覆盖、回滚、格式化或提交无关改动。
- 禁止使用会丢失工作区内容的 Git 命令。
- 删除、移动、批量生成或改写前先解析精确目标。
- 未经明确要求，不 commit、push、创建 PR、Tag、Release 或修改远端状态。
- 提交时只包含本任务改动；提交前检查 cached diff、文件范围和 `diff --check`。
- Secret、Token、真实配置、日志、数据库、构建产物和临时文件不得进入提交。

## 验证阶梯

按改动范围选择最小充分验证：

1. 文档：检查链接、模板标记、生成结果和 diff。
2. Python 生成器：Ruff、Mypy、相关 pytest。
3. 模板引擎或共享文件：根测试 + 六种生成组合。
4. 语言模板：对应语言 API / 非 API 的 lint、类型、测试与构建。
5. 打包：构建 wheel，在全新环境安装并生成项目。
6. CI：对根 workflow 和生成 workflow 运行 actionlint。
7. 推送后：监控 GitHub Actions 到终态。

基础命令：

```bash
uv run ruff check src tests test_template.py
uv run ruff format --check src tests test_template.py
uv run mypy src/scaffold
uv run pytest
```

真实公网、真实模型、外部服务和发布验证必须单独授权。不得用固定睡眠代替
服务就绪检测，不得复用来源不明的已有进程完成隔离测试。

## 文档与设计规则

- README 只描述当前可用能力，不把计划写成事实。
- 公共行为或兼容边界变化同步 CHANGELOG。
- 架构理由、设计规范和 QA 证据各自维护，不互相冒充。
- 修改前端页面或组件前必须读取 `DESIGN.md`。
- 稳定视觉规则更新 `DESIGN.md`；截图、对照、发现和修复记录写入
  `design-qa.md` 或 `docs/design-qa/`。
- `CLAUDE.md` 不复制本文件；只指向本文件并记录 Claude 专属差异。

## Code Review Rules

审查时优先报告正确性、权限、安全、数据完整性和契约问题，不把 CI 可自动
发现的格式问题作为主要审查结论。

- 标记新增第二模板源、生成文件残留模板标记或 wheel 缺少资源。
- 标记关闭功能后仍保留依赖、文件、import 或 workflow 的情况。
- 标记显式用户配置被派生默认值覆盖。
- 标记文档把 Proposed、示例或未验证能力写成当前事实。
- 标记未经授权的外部写入、发布、Secret 处理或破坏性文件操作。
- 前端改动必须指出违反 `DESIGN.md` 的具体规则，并给出安全替代路径。

## 完成标准

任务只有在以下条件满足时才算完成：

- 实现与用户请求、当前代码和事实源一致；
- 没有无证据扩展范围、依赖或权限；
- 相关模板组合可生成且没有残留控制标记；
- 最小相关验证通过，或明确说明未运行及原因；
- wheel、CI、文档或设计契约在受影响时已同步；
- 用户已有修改未被破坏；
- 最终回复说明实际改动、验证、未验证项和重要剩余风险。
