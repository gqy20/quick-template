# 专题文档索引

本目录存放随实现维护的专题文档。当前只有版本变化记录；项目出现第二类
专题时按下述规则建立。

本规范面向从模板生成的项目，不约束 quick-template 仓库自身：它是工具
仓库，站点产物在 `docs/`，维护者参考在 `agent-guide/`。

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

规则文档写规则与边界，操作文档写步骤，报告写当时的证据。各文档的完整
路径见 `AGENTS.md` 的事实源路由。

## 目录编号

专题目录使用两位数字前缀表示稳定阅读顺序：

```
docs/
├── README.md
├── CHANGELOG.md
├── PRODUCT.md
├── 01-product/           固定槽位，按需建立
├── 02-architecture/
├── 03-operations/
└── 90-archive/           归档，保留被替代的方案
```

前三个槽位固定含义，跨项目一致：

| 编号 | 主题 | 内容 |
| --- | --- | --- |
| `01` | `product` | 交付范围、用户、术语与边界 |
| `02` | `architecture` | 系统结构、模块边界、数据流 |
| `03` | `operations` | 启停、排障、发布与配置、验收证据 |

规则：

- 编号表示阅读顺序，不表示优先级或重要性。
- 插入新专题取下一个编号，废弃的编号留空，不重排已有编号。
- 编号不进显示标题。`01-product/01-scope.md` 的标题是「产品范围」。
- 专题内文件同样编号：`NN-<职责>.md`，例如 `01-scope.md`、`02-workflows.md`。
- `90-archive` 留给归档，使其永远排在最后。
- 只有内容长出来后才建目录。预先建空的编号目录会让读者误以为那里缺文档。

## 命名

- 文件名用 kebab-case：`product-scope.md`、`runbook.md`。
- 通用名保留大写：`README.md`、`CHANGELOG.md`、`ROADMAP.md`{{#if has_frontend}}、`DESIGN.md`{{#endif}}。
- 报告用 `YYYY-MM-DD-主题.md`，日期即记录时间，不加流水编号。
- 不用无信息量的名字：`notes.md`、`misc.md`、`new.md`。

## 其他专题

除固定槽位外，按需增加专题并取下一个编号：

| 主题 | 内容 |
| --- | --- | --- |
| `development` | 代码规范、测试策略、本地流程 |
{{#if has_frontend}}| `design` | 前端实现基线与组件约定 |
{{#endif}}| `reference` | API、配置项与清单 |

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
