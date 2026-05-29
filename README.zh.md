# Open WebUI 插件 — 内联可视化工具集

为 [Open WebUI](https://github.com/open-webui/open-webui) 精心策划的插件集合 — 扩展 AI 聊天体验的工具、技能、过滤器、管道和操作。

> **致谢：** 本项目基于并受 [Classic298/open-webui-plugins](https://github.com/Classic298/open-webui-plugins) 启发。`inline-visualizer` (v1) 基础架构由 Classic298 创建。`inline-visualizer-v3` 和 `inline-visualizer-template` 插件由 **Derek** 独立研发。

---

## 插件总览

| 插件 | 类型 | 作者 | 描述 |
|------|------|------|------|
| [Inline Visualizer v2](inline-visualizer-v2/) | 工具 + 技能 | Classic298 | 流式实时渲染可视化引擎 — 逐token见证 HTML/SVG 绘制过程 |
| [Inline Visualizer v3](inline-visualizer-v3/) | 工具 + 技能 | **Derek** | 新一代流式可视化，增强设计系统、双语技能支持、扩展桥接架构 |
| [Inline Visualizer Template](inline-visualizer-template/) | 工具 + 技能 | **Derek** | 快速模板可视化 — 4 个自描述函数，扁平参数，零代码生成 |
| [Inline Visualizer v1](inline-visualizer/) | 工具 + 技能 | Classic298 | 传统静态渲染引擎 — 一次性 HTMLResponse 模式 |
| [Email Composer](email-composer/) | 工具 | Classic298 | AI 驱动的邮件撰写，带富交互 UI 卡片 |
| [MCP App Bridge](mcp-app-bridge/) | 工具 | Classic298 | 将 MCP 应用 (SEP-1865) 渲染为富 UI 嵌入 |

---

## 重点插件详解

### v2 — Inline Visualizer（流式版）

突破性的流式可视化引擎。模型调用 `render_visualization(title=...)`，然后在 `@@@VIZ-START` / `@@@VIZ-END` 标记之间输出 HTML/SVG。同源 iframe 观察器实时追踪聊天 DOM 并增量协调新节点 — 你会看到卡片、SVG 和图表随着模型打字而逐渐呈现，而非消息完成后一次性弹出。

**核心能力：**

- **流式实时渲染** — 首个元素在起始标记到达后约 50ms 内开始呈现。通过自定义安全截断 HTML 解析器和增量 DOM 协调器实现逐 token 渲染。已有节点从不重新挂载，动画从不重新触发，零闪烁。
- **完整设计系统** — 9 色渐变体系（purple, teal, coral, pink, gray, blue, green, amber, red），自动适配亮色/暗色主题。SVG 工具类（`.t`, `.ts`, `.th`, `.box`, `.node`, `.arr`, `.leader`, `.c-{ramp}`）。预样式化裸 HTML 元素 — 直接写 `<button>`, `<input>`, `<textarea>`, `<select>`, `<table>`, `<details>`, `<dl>`（grid/inline 布局），无需 class 或 style 即可获得主题匹配的精美样式。
- **`data-accent` 色调面板** — 在任何元素上设置 `data-accent="teal"` 即可改变聚焦环、复选框、单选按钮和 `var(--accent)` 消费者的颜色。9 种命名值与图表色系一一对应。
- **6 个交互桥接** — `sendPrompt(text)` 对话式下钻、`openLink(url)`、`copyText(text)` 自动弹出提示、`toast(msg, kind)` 支持 success/info/warn/error 四级通知、`saveState(k,v)` / `loadState(k,fallback)` 基于消息的 localStorage 持久化，刷新不丢失。
- **CDN 库生态** — 原生支持 Chart.js, D3.js, Vega-Lite, ECharts, Plotly, vis-network 和 Tone.js/Wavesurfer，每个库附带经过验证的 CDN 地址和使用指南。严格 CSP 模式下自动加入白名单。
- **46 语言国际化** — 5 个 UI 字符串 × 46 种语言 = 230 条翻译。自动检测服务器注入的 `<html data-iv-lang>`、父级 `localStorage.locale` 和 `navigator.language`。
- **可配置 CSP** — 严格（禁止外部请求/图片）、平衡（允许图片）、无限制（完全开放）。通过工具阀门切换。
- **流完成反馈** — 本地化的"可视化就绪"提示 + 可选 C 大调和弦提示音（Web Audio 正弦波振荡器）。可全局或单次可视化关闭。
- **生产级加固** — 脚本边界安全守卫、工具结果示例泄漏防护、独立守护层启动弹性、逐 tick 缓存优化、Promise 链动态脚本注入。

**效果：** 用户体验到如绘画般流畅的视觉生成。复杂的仪表盘、交互式图示、数据探索实时具象化 — 不是静态结果，而是动态的创作过程。

---

### v3 — Inline Visualizer v3（新一代流式）

由 **Derek** 独立研发，v3 在流式架构基础上进化出精致的设计系统、扩展的桥接能力和首创的双语（中文/英文）技能支持。为生产级可视化工作流而生。

**v3 相比 v2 的提升：**

- **重构的设计系统** — 更精致的色彩调色板、增强的 SVG 原语、更丰富的预样式组件。裸 HTML 样式覆盖更广泛的表单元素和布局模式。
- **双语技能支持** — 内置 `SKILL.md`（英文）+ `SKILL.zh.md`（中文）。模型可以加载任一语言的技能手册，大幅提升中文用户的可视化质量。
- **扩展桥接架构** — 保留 v2 所有桥接能力，并增加更多通信原语，实现可视化与父级聊天之间更丰富的交互。
- **优化的渲染引擎** — 改进的 DOM 协调器，更好地处理边界情况，更快的绘制周期，更低的内存占用。
- **增强的 CDN 库集成** — 与可视化库生态更紧密的集成，确保脚本可靠加载，图表首次绘制即正确渲染。
- **全面的错误恢复** — 多层降级系统确保可视化优雅降级而非静默失败。
- **生产测试覆盖** — 包含运行时守护测试（`test_streaming_runtime_guards.py`）和干运行验证（`dry_run_v3.py`），支持部署验证。

**效果：** v3 提供了生态系统中最精致的流式可视化体验。中文用户获得母语级别的技能指导。开发者获得经过实战检验、文档完善的基础设施，可在此基础上构建自定义可视化工作流。

---

### Template — Inline Visualizer Template（快速模板可视化）

由 **Derek** 独立研发，该插件采用完全不同的设计思路：不再让模型从零生成 HTML/CSS/JS，而是提供 **4 个自描述函数**，每个函数具有扁平的参数签名。模型传入结构化的 JSON 数据，工具内部使用 Chart.js 完成所有渲染。

**设计理念：** v3 的 `render_visual_template` 使用单一函数配合 `template` 枚举 + 嵌套 `data` 字典。模型看到 `data: Optional[Dict[str, Any]]` 无法理解具体的结构要求。Template v4（本插件）拆分为 4 个独立函数，**每个函数的参数即其 schema** — 模型从函数签名中直接理解参数契约。

| 维度 | v3（通用函数） | Template（4 个独立函数） |
|------|--------------|------------------------|
| 函数数量 | 1 个通用函数 | 4 个独立函数 |
| 参数设计 | 嵌套 `data` 字典 | 扁平类型参数 |
| Schema 定义 | SKILL.md 文档 | 函数签名 + 参数名 |
| 验证位置 | 浏览器 JS | Python 端 |
| 错误反馈 | HTML 错误卡片 | 纯文本错误消息 |
| 模型指令 | 依赖外部 SKILL.md | 内置 `tool_instructions` |

**四个函数：**

1. **`render_data_detail`** — SQL + 解释 + 数据表预览。`columns` 和 `rows` 必填。SQL 和解释自动折叠，数据表始终可见，超过 10 行自动分页。

2. **`render_chart`** — 折线图、柱状图、饼图（Chart.js doughnut）、表格。`series` 为行对象数组，包含一个 x 轴键和一个或多个数值 y 列（`[{label, value}]` 仍作为简单兼容格式）。支持多列数据配合 `y_columns`。自动检测数值列。折线/柱状图支持单位安全的 y 轴名称。图表类型切换、PNG 导出。

3. **`render_dashboard`** — KPI 指标卡 + 可选趋势图。`metrics` 为 `[{label, value, delta?}]`。Delta 自动着色（`+` 绿色，`-` 红色）。可选 `series` 在指标卡下方渲染趋势图。

4. **`render_analysis_dashboard`** — 综合监控/诊断看板，包含 KPI、趋势、拆分、排行、说明和告警模块。

**核心优势：**

- **模型负担极低** — 模型只需传入扁平 JSON 参数，无需生成数百行 HTML/CSS/JS。大幅减少 token 错误，生成更快，成功率更高。
- **Python 端验证** — 参数格式不合法时返回纯文本错误消息，模型能直接看到并纠正，不会产生破损的 HTML 卡片。
- **内置交互功能** — 图表类型切换（line/bar/pie/table）、PNG 导出、自动深色模式、渲染统计信息（JSON 长度、HTML 长度、构建耗时、渲染耗时）。
- **补充 v3，而非替代** — 高频数据图表、KPI 仪表盘、SQL 数据预览使用 Template。复杂自定义可视化、交互图示、地图、创意布局使用 v3。

**推荐调用流程：** 先 `render_data_detail`（展示数据来源和 SQL）→ 单图请求再调用 `render_chart`，轻量 KPI 概览再调用 `render_dashboard`，明确要求综合分析、监控或诊断看板时再调用 `render_analysis_dashboard`。

**效果：** Template 将"给我画个数据图表"从需要数百 token 的 HTML 生成任务转变为约 50 token 的 JSON 参数传递。结构化数据可视化的成功率接近 100%。模型专注于数据分析，而非前端编码。

---

## 插件类型

| 类型 | 功能 | 安装位置 |
|------|------|---------|
| **工具 (Tools)** | 赋予模型新的可调用能力（网络搜索、API、渲染） | 工作区 → 工具 |
| **技能 (Skills)** | 教授模型如何执行特定任务或工作流的结构化指令 | 工作区 → 技能 |
| **过滤器 (Filters)** | 在消息到达模型前或展示给用户前进行转换 | 管理面板 → 函数 |
| **管道 (Pipes)** | 自定义模型端点 — 代理、合并或创建全新模型行为 | 管理面板 → 函数 |
| **操作 (Actions)** | 显示在消息下方的快捷操作按钮 | 管理面板 → 函数 |

---

## 如何安装

1. 打开插件文件夹，阅读其 **README** 了解具体安装说明
2. 每个 README 列出了组件（工具、技能、过滤器等）及其安装位置
3. 部分插件是单个文件，其他是多组件 — README 会提供指引

---

## 快速开始 — 可视化插件

```bash
# v2 (流式版) — 实时逐 token 渲染
cp inline-visualizer-v2/tool.py → 工作区 → 工具
cp inline-visualizer-v2/SKILL.md → 工作区 → 技能（名称："visualize"）

# v3 (新一代) — 增强流式 + 双语支持
cp inline-visualizer-v3/tool.py → 工作区 → 工具
cp inline-visualizer-v3/SKILL.md → 工作区 → 技能（名称："visualize"）

# Template — 快速模板图表和仪表盘
cp inline-visualizer-template/tool.py → 工作区 → 工具
cp inline-visualizer-template/SKILL.md → 工作区 → 技能（名称："visual_template"）
```

**必须设置：** 在 Open WebUI 设置 → 界面中启用 **允许 iframe 同源**（v2 和 v3 流式模式必需）。

---

## 版本选择指南

| 使用场景 | 推荐插件 |
|---------|---------|
| 高频数据图表（折线图、柱状图、饼图、表格） | Template |
| KPI 仪表盘（指标卡片） | Template |
| SQL 数据预览 + 解释 | Template |
| 复杂 SVG 图示（架构图、流程图） | v3 |
| 交互式地图、元素周期表、问答 | v3 |
| 自定义创意可视化 | v3 |
| 实时流式视觉体验 | v2 或 v3 |
| 中文聊天环境 | v3（双语技能） |

---

每个插件文件夹独立包含所有必要文件和文档。

---

## 参与贡献

发现 bug 或有想法？提交 issue 或 pull request。

---

## 致谢

- [Classic298/open-webui-plugins](https://github.com/Classic298/open-webui-plugins) — 原始 inline-visualizer v1、v2、email-composer 和 MCP app bridge
- **Derek** — 独立研发 inline-visualizer-v3 和 inline-visualizer-template
