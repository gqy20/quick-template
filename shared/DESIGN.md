---
name: "{{ project_name_escaped }}"
status: baseline
design:
  density: 5
  variance: 6
  motion: 4
colors:
  canvas: "#F7F7F5"
  surface: "#FFFFFF"
  surface-muted: "#F0F0ED"
  ink: "#18181B"
  ink-muted: "#66666D"
  border: "#DEDED9"
  accent: "#B04A5A"
  accent-hover: "#923B49"
  accent-soft: "#F8ECEE"
  focus: "#0B63CE"
  evidence: "#0F766E"
  evidence-soft: "#E8F5F2"
  success: "#15803D"
  warning: "#A16207"
  danger: "#B42318"
typography:
  sans: "Geist, Noto Sans SC Variable, PingFang SC, Microsoft YaHei, system-ui, sans-serif"
  mono: "Geist Mono, JetBrains Mono, SFMono-Regular, Consolas, monospace"
spacing:
  unit: "4px"
  scale: ["4px", "8px", "12px", "16px", "24px", "32px", "48px", "64px"]
radius:
  control: "6px"
  panel: "10px"
  overlay: "14px"
motion:
  fast: "120ms"
  normal: "180ms"
  slow: "260ms"
  easing: "cubic-bezier(0.16, 1, 0.3, 1)"
---

# Design System: {{ project_name }}

代码里的 Token 文件是可执行实现，本文件是语义与用途事实源；修改颜色、字体、
间距、圆角或动效时，两者必须在同一变更中保持一致。

## 1. 设计北极星

- 每页围绕一个主要任务，给最重要的操作最高视觉强调。
- 按上下文、当前状态或结论、依据、可执行动作、历史详情排列内容。
- 区分已确认事实、推断、建议和待审核状态。动效用于解释状态变化。

## 2. 语义 Token

Token 按用途命名，不按某个页面或当前色相命名。新增视觉值前先确认现有 Token
无法表达该语义；禁止在组件中散写重复的颜色、间距、圆角和阴影。

### 颜色

- **canvas**：应用主画布。
- **surface**：主要内容表面、输入和浮层主体。
- **surface-muted**：次级分区、禁用背景和骨架底色。
- **ink**：标题、正文和需要长期阅读的信息；不使用纯黑。
- **ink-muted**：元数据和辅助说明，仍需满足对比度要求。
- **border**：结构线，不承担主要强调。
- **focus**：键盘焦点环，不用于装饰或普通强调。
- **accent**：唯一品牌强调色，只用于主要动作、当前选择和少量关键状态。
- **evidence**：可追溯来源、证据入口和已定位关系；不是第二品牌色。
- **success / warning / danger**：只表达明确系统状态，不用于装饰。

同一语义在所有页面使用同一颜色。状态不能只靠颜色区分，必须同时提供文字、
图标、形状或位置线索。

### Token 分层

```text
primitive value → semantic token → component role → state
```

组件只消费 semantic token：

```css
/* 对：语义层 */ .card { background: var(--surface); border: 1px solid var(--border); }
/* 错：绕过语义层，直接引用色阶 */ .card { background: #FFFFFF; border: 1px solid #DEDED9; }
```

### 间距与几何

- 所有尺寸落在 4px 基础网格。
- 紧密关系使用 4–8px，控件内部使用 8–16px。
- 面板内部使用 16–24px，区块之间使用 24–48px。
- 控件圆角 6px，面板 10px，浮层 14px。
- 胶囊圆角只用于标签、筛选和明确的 pill 控件。
- 不使用 24px 以上大圆角包装普通业务内容。

### 阴影

默认扁平，通过表面、边框、间距和遮罩表达层级。

- 常驻面板不使用宽软阴影。
- 菜单、Popover、Modal、Drawer 可以使用一层克制结构阴影。
- 不同时叠加完整描边和大范围柔光。
- 焦点环是无障碍状态，不是装饰阴影。

## 3. 字体与内容层级

界面与正文用 Geist + Noto Sans SC，代码、ID、数值用 Geist Mono 或
JetBrains Mono。不用装饰性衬线，不为“高级感”混用字体家族。

| 层级 | 尺寸 | 用途 |
|---|---|---|
| Display | 36–44px | 页面级结论，每页最多一个 |
| H1 / H2 / H3 | 28–34 / 22–26 / 18–20px | 标题、分区、面板 |
| Body | 16–18px，65–72ch | 连续阅读 |
| UI / Caption | 14–16 / 12–13px | 可操作信息不小于 14px |

数字启用 `font-variant-numeric: tabular-nums`。标题直接表达对象或任务，不在
上方堆英文眉题、编号或同义副标题。文案用具体名词和动词，避免“赋能、无缝、
释放潜能”这类套话；空状态和错误只说明发生了什么、影响和下一步。

## 4. 布局与信息架构

- 使用 CSS Grid 表达二维结构，避免依赖 `calc()` 的百分比拼接。
- 主内容设置明确 max-width；工作台可使用 1280–1440px 基准。
- 不默认使用三个等宽卡片横排；根据任务重要度形成主次或列表。
- 卡片只在边界、点击目标或层级确实需要时使用。
- 禁止卡片套卡片；优先使用标题、留白、分隔线和背景层。
- 文本、表格标题和业务内容默认左对齐；数值列右对齐。
- 页面只保留一个语义 H1；相同信息只保留一个主要视觉表达。
- 主要动作靠近其影响对象，不把所有操作集中到页面角落。
- 高密度页面通过渐进展开、抽屉和详情分层，不隐藏关键状态。

### 页面类型

- **工作台：** 当前状态、关键变化、待处理事项和证据入口。
- **列表 / 表格：** 比较和批量操作优先，不把每行转换成大卡片。
- **详情：** 对象标题、状态、关键事实、证据、历史和操作。
- **表单：** 标签在输入上方，帮助文字可选，错误紧邻字段下方。
- **营销页面：** 可以更舒展和不对称，但仍遵守单一主 CTA 与语义 Token。

## 5. 组件与交互

### 按钮

- 主按钮每个可视区域最多一个，标签使用“动词 + 对象”。
- 次按钮使用描边或 ghost，不与主操作竞争。
- 加载态保持原有宽度，并说明正在执行的动作。

```css
.button {
  min-height: 44px;
  min-width: 44px;
  padding: 0 16px;
  border-radius: var(--radius-control);
  background: var(--accent);
  color: var(--surface);
  transition: background var(--motion-fast) var(--ease),
              transform var(--motion-fast) var(--ease);
}
.button:hover { background: var(--accent-hover); }
.button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.button:active { transform: translateY(1px); }   /* 不用发光、弹跳或夸张上浮 */
.button:disabled { opacity: 0.6; cursor: not-allowed; }
```

用键盘检查位于容器边缘的按钮，确保焦点环完整可见。

### 输入与表单

- 使用可见 label，不依赖 placeholder 作为唯一标签。
- 焦点环与按钮共用 `var(--focus)`，不改变布局尺寸。
- 错误包含字段、原因和修复方式；不只显示红色边框。
- 提交失败保留用户输入。
- 破坏性或不可逆提交明确说明后果并提供确认。

### 导航与图标

- 导航层级稳定，当前状态不仅靠颜色表达。
- 纯图标按钮必须有 `aria-label` 和 Tooltip。
- 同一动作全局只使用一种图标和名称。
- 通用动作可以符号化；领域含义和关键业务状态保留文字。
- 不用 emoji、字符箭头或 `...` 模拟正式图标。

### 表格、图表与数据

- 文本左对齐，数字右对齐，操作列稳定。
- 图表必须有文字结论、单位、时间范围和可访问替代。
- 颜色之外再使用标签、形状、线型或图标区分系列。
- 缺失值显示“暂无 / 未采集 / 不适用”，不得伪造成 0。
- AI 推断与已确认事实使用不同状态语法。

### Loading、Empty、Error

- Loading 使用匹配最终尺寸的骨架；不在大面积内容中放孤立转圈。
- Empty 说明为空原因并给出合理下一步。
- Error 说明失败位置、影响范围、已有数据是否可用和重试动作。
- 成功、警告和进度消息通过可被辅助技术识别的状态区域呈现。

## 6. 响应式与无障碍

目标至少满足 WCAG 2.2 AA：

- 正文对比度至少 4.5:1；大字至少 3:1；非文本控件与焦点至少 3:1。
- 所有功能可通过键盘完成，焦点可见且不被粘性区域遮挡。
- 触摸目标至少 44×44px；相邻目标保持足够间隔。
- 页面在 320px CSS 宽度下不因布局产生双向滚动。
- 文本放大到 200% 时不裁切、重叠或丢失功能。
- 不以颜色、位置、形状或声音作为唯一说明。
- 图像提供与用途相符的替代文字；装饰图像使用空 alt。
- 状态、错误和异步结果可被辅助技术感知。

### 断点策略

- 小于 768px：多列布局按任务顺序折叠为单列。
- 768–1199px：保留主任务，次要详情进入抽屉或下一层。
- 1200px 及以上：允许双栏、多栏工作台和固定辅助区。
- 标题与区块间距使用 `clamp()` 平滑缩放。
- 移动端禁止意外横向滚动；数据表可使用明确的局部滚动容器。

响应式不是机械堆叠。折叠顺序必须体现“上下文 → 主任务 → 证据 → 次要历史”。

## 7. 动效与性能

- 动效只表达进入、退出、展开、定位、状态变化和因果关系。
- 默认使用 120–260ms 与 `cubic-bezier(0.16, 1, 0.3, 1)`。
- 列表进入可以轻量 stagger，但不得延迟用户读取或操作。
- 仅动画化 `transform` 与 `opacity`；避免动画化布局属性。
- 不使用无限循环脉冲、漂浮或 shimmer，除非它真实表达活动状态。
- 支持 `prefers-reduced-motion`；减少模式移除非必要位移、缩放和视差。
- 动效不能成为理解状态变化的唯一方式。
- 大图、字体和可视化按需加载，避免为装饰引入高成本运行时。

## 8. 实现契约

- 优先复用现有设计系统和可访问原语，不重写等价 Button、Dialog、Tooltip、
  Form、Table 和 Tabs。
- Token 进入 CSS Variables、主题配置或设计 token 文件；组件不维护平行色表。
- 静态样式进入样式系统；inline style 只用于真实动态值或 Token 引用。
- 删除组件时同步删除样式、故事、测试和无效 Token。
- 新增组件前搜索现有实现，避免同义组件和选择器。
- 组件必须覆盖 default、hover、focus-visible、active、disabled、loading、
  empty 和 error 中适用的状态。
- 页面级视觉改变必须提供真实内容，不用 Lorem Ipsum、John Doe、Acme、
  伪造 99.99% 或无来源的整齐数据冒充产品事实。

## 9. 禁止模式

- 禁止 AI 紫蓝霓虹、发光外阴影和大面积渐变文字。
- 禁止纯黑背景配高饱和荧光色作为默认“科技感”。
- 禁止三个等宽卡片、卡片套卡片和无意义 Bento 堆叠。
- 禁止居中大标题 + 两个 CTA + “Scroll to explore” 的模板化首屏。
- 禁止无信息价值的眉题、英文标签、重复标题和巨大数字。
- 禁止过度圆角、玻璃拟态、装饰网格、噪点和持续漂浮动画。
- 禁止自定义鼠标指针、隐藏系统焦点和只在 hover 可发现的关键操作。
- 禁止用 emoji、字符或临时 SVG 代替现有图标系统。
- 禁止图片与文字重叠到影响阅读；每个元素占据清晰空间。
- 禁止为了“简洁”缩小正文、隐藏状态、删除标签或牺牲可访问性。
- 禁止把 Mock、AI 候选或占位内容视觉上呈现为已确认事实。

## 10. Design QA

`DESIGN.md` 只存稳定规则；每轮证据另存为 `docs/` 下的独立文档，位置与命名见
`docs/README.md`，不追加到本文件。

必查视口：390×844、768×1024、1280×800、1440×900、1920×1080。

必查状态：默认、hover、focus、active、disabled；loading、empty、error、长
内容；Modal/Drawer、表单校验、异步成功与失败；reduced motion 与 200% 缩放。

每轮记录变更范围、目标视口、证据路径、P0–P3 发现与处理状态、已跑检查、未验
证项。严重度：P0 主任务或数据风险；P1 内容不可读或不可达；P2 明显层级或交互
缺陷；P3 精修差异。

没有截图、尺寸和状态证据时，不得宣称“像素一致”或“设计验收通过”；修复后
重新捕获，不用旧截图证明新实现。
