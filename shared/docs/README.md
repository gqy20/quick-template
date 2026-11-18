# 专题文档索引

## 文档分工

| 文档 | 内容 | 维护时机 |
| --- | --- | --- |
| `README.md` | 项目概览、安装与使用 | 能力或用法变化 |
| `AGENTS.md` | Agent 执行契约 | 协作规则变化 |
{{#if has_frontend}}| `DESIGN.md` | 前端视觉与交互契约 | 视觉方向或 Token 变化 |
{{#endif}}| `CHANGELOG.md` | 版本与行为变化 | 每次发布 |
| `PRODUCT.md` | 产品范围与边界 | 产品定位变化 |
| `ROADMAP.md` | 只列未完成事项，按需建立 | 计划调整 |
| 专题文档 | 展开的规范、边界、操作步骤与验收证据 | 对应领域变化 |
| `reports/` | 实测、验证与调研快照 | 每次研究或验收 |

## 目录编号

有内容时再创建专题目录。前缀表示阅读顺序，前三个编号固定：

| 目录 | 内容 |
| --- | --- |
| `01-product/` | 用户、范围、术语 |
| `02-architecture/` | 模块边界、数据流、架构决策 |
| `03-operations/` | 启停、排障、发布、配置和验收记录 |

新专题取下一个编号，废弃的编号留空。专题内文件也按阅读顺序编号，
例如 `01-product/01-scope.md`，显示标题写「产品范围」。

## 命名

- 文件名用 kebab-case：`product-scope.md`、`runbook.md`。
- 通用名保留大写：`README.md`、`CHANGELOG.md`、`ROADMAP.md`{{#if has_frontend}}、`DESIGN.md`{{#endif}}。
- 报告用 `YYYY-MM-DD-主题.md`，日期即记录时间，不加流水编号。
- 不用无信息量的名字：`notes.md`、`misc.md`、`new.md`。

{{#if has_frontend}}## 验收证据

视觉与交互验收的截图、录屏和发现记录，作为对应专题下的独立文档存放，
例如 `03-operations/01-visual-verification.md`。证据不追加到稳定规范
（`DESIGN.md`、`AGENTS.md`），也不占用固定槽位。记录内容与严重度定义见
`DESIGN.md` 的 Design QA 一节。
{{#endif}}
## 证据与归档

- `reports/` 存放实测、验证与调研快照，只反映写作当天的状态，不随实现更新。
- 被替代的方案移入 `90-archive/`，并在归档索引说明替代原因。
- 历史报告保留当时结论，不能改写成现在的质量证明。
- 调整路径时同步更新仓库内引用，并检查链接与锚点。
