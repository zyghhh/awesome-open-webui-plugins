# Inline Visualizer Template v3

面向 Open WebUI 的快速模板可视化插件，使用 Chart.js 渲染。

## 版本兼容性

- **适用版本：Open WebUI 0.10.2+**
- v3 使用消息级 `embeds` 事件，绕过 Open WebUI 0.10.2 将连续工具调用分组后不显示工具内嵌 iframe 的前端问题。
- 如需 Open WebUI 0.9.5 的旧版 `HTMLResponse` 工具内嵌行为，请使用 `inline-visualizer-template-v2`。

这个插件用于补充 `inline-visualizer-v3`，不是替代它。模型调用四个自描述函数，传入扁平参数即可生成可视化，避免模型输出大量前端代码。

## 设计理念

旧版单函数原型的 `render_visual_template` 通过 `template` 枚举 + 嵌套 `data` 字典来区分可视化类型。模型看到 `data: Optional[Dict[str, Any]]` 无法理解具体结构，容易传错格式。

当前 Template 插件拆分为四个独立函数，每个函数的参数即 schema：

| 维度 | 旧版单函数原型 | 当前 Template 插件 |
|------|---------|---------|
| 函数数量 | 1 个通用函数 | 4 个独立函数 |
| 参数设计 | 嵌套 `data` dict | 扁平类型参数 |
| Schema 定义 | SKILL.md 文档 | 函数签名 + 参数名 |
| 验证位置 | 浏览器 JS | Python 端 |
| 错误反馈 | HTML 错误卡片 | 纯文本错误消息 |
| 模型指令 | 依赖外部 SKILL.md | `tool_instructions` 内置 |

## 文件

| 文件 | 用途 |
| --- | --- |
| `tool.py` | Open WebUI 工具。复制到 Workspace -> Tools。 |
| `SKILL.md` | Skill 指令。添加为名为 `visual_template` 的 skill。 |

## 函数

### render_data_detail

SQL + 解释 + 数据表预览。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `columns` | `list[str]` | 是 | 列名字符串数组 |
| `rows` | `list[dict]` | 是 | 行数据对象数组 |
| `sql` | `str` | 否 | SQL 查询字符串 |
| `sql_lines` | `list[str]` | 否 | SQL 行数组；复杂或多行 SQL 推荐使用，比整段字符串更稳定 |
| `explanation` | `str` | 否 | 纯文本解释 |
| `title` | `str` | 否 | 标题，默认 "Data Detail" |

### render_chart

折线图、柱状图、饼图（Chart.js doughnut）、二维表格。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `series` | `list[dict]` | 是 | 行数据对象数组：一个 x 轴键（如 `label`、`date`、`name`）加一个或多个数值 y 列；`[{label, value}]` 仍可作为兼容/简单示例 |
| `chart_type` | `"line" \| "bar" \| "pie" \| "table"` | 否 | 图表类型，默认 "line" |
| `y_columns` | `list[str]` | 否 | 指定绘图数值列；不传时优先使用 `value`，否则自动检测数值列。`pie` 只使用第一个数值列 |
| `y_axis_label` | `str` | 否 | 完整 y 轴名称和单位，如 `"Revenue (USD)"`；优先级最高，导出 PNG 会包含 |
| `y_axis_unit` | `str` | 否 | y 轴单位，如 `"rpm"`；单 y 列显示为 `列名 (单位)`，多 y 列仅在所有指标共享同一单位时使用 |
| `title` | `str` | 否 | 标题，默认 "Chart" |

### render_dashboard

指标卡 + 可选趋势图，支持单列和多列趋势数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `metrics` | `list[dict]` | 是 | `[{label, value, delta?}]` 数组 |
| `series` | `list[dict]` | 否 | 可选趋势图数据；兼容 `[{label, value}]`，也支持如 `[{month, revenue, users}]` 的多列数据 |
| `chart_title` | `str` | 否 | 趋势图标题 |
| `chart_type` | `"line" \| "bar" \| "pie" \| "table"` | 否 | 趋势图类型，默认 "line" |
| `y_columns` | `list[str]` | 否 | 指定绘图数值列；不传时优先使用 `value`，否则自动检测数值列。`pie` 只使用第一个数值列 |
| `y_axis_label` | `str` | 否 | 趋势图完整 y 轴名称和单位，如 `"Requests (rpm)"`；导出 PNG 会包含 |
| `y_axis_unit` | `str` | 否 | 趋势图 y 轴单位；单 y 列显示为 `列名 (单位)`，多 y 列仅在所有指标共享同一单位时使用 |
| `title` | `str` | 否 | 标题，默认 "Dashboard" |

单位规则：工具不会从数据值里猜单位。需要准确单位时优先传 `y_axis_label`，例如 `"Revenue (USD)"`。单个 y 列会用 `y_axis_unit` 自动组合为 `列名 (单位)`；多个 y 列只有在所有指标共享同一单位时才传 `y_axis_unit`，图例开关后左侧标题会随当前可见指标更新。多 y 列单位不同则不要传共享单位，必要时用准确的 `y_axis_label`。

### render_analysis_dashboard

综合分析看板，适合时序监控、业务诊断和多角度分析。固定页面骨架，模块语义由参数配置。它不替代 `render_data_detail`：如果用户需要 SQL、原始数据、完整明细或数据来源，必须先调用 `render_data_detail`。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `hero_chart` | `dict` | 是 | 主图 `{title, chart_type, series, y_columns?}` |
| `rankings` | `dict` | 否 | 排行/峰值/贡献度 `{title, items:[{label, value, unit?}]}` |
| `small_charts` | `list[dict]` | 否 | 最多 2 个辅助小图，结构同 `hero_chart` |
| `summary_cards` | `list[dict]` | 否 | 底部 KPI 卡片 `[{label, value, delta?}]` |
| `subtitle` | `str` | 否 | 副标题 |
| `title` | `str` | 否 | 标题，默认 "Analysis Dashboard" |

## 数据合法性

参数格式不合法时，**Python 端直接返回纯文本错误消息**，模型能直接看到并纠正参数，不会生成 HTML 错误卡片。

## 调用顺序

所有包含可视化的回答都必须先调用 `render_data_detail` 展示数据来源，再调用目标图表或看板。数据详情表优先只是调用顺序要求，不代表所有查询都要使用综合分析看板：

1. 先调用 `render_data_detail`，展示 SQL、解释和完整数据表。
2. 普通单图、趋势、柱状、饼图或表格请求，再调用 `render_chart`。
3. KPI/概览/多个指标请求，再调用 `render_dashboard`。
4. 只有明确要求综合分析、监控看板、诊断、多角度展示，或需要 3 个以上语义模块时，才调用 `render_analysis_dashboard`。

调用 `render_chart` 时必须传 `series`。如果刚展示过 `render_data_detail.rows`，把同一批行数据作为 `series` 传入；工具也兼容 `rows` 作为别名，但推荐使用 `series`。

职责边界：

- `render_data_detail`：完整数据来源、SQL、可核对明细。
- `render_chart`：单个图表问题。
- `render_dashboard`：轻量 KPI + 一个趋势图。
- `render_analysis_dashboard`：明确要求的综合分析页，多模块展示；不包含详细数据模块，避免和 `render_data_detail` 重复。

## 内置功能

- Chart.js 动画图表（line/bar/doughnut）
- 图表类型切换（line/bar/pie/table）
- 综合分析看板（主图、排行、辅助图、摘要卡片）
- 导出 PNG
- 统计信息：模板、图表类型、JSON 长度、HTML 长度、构建耗时、渲染耗时
- 自动深色模式适配（`prefers-color-scheme: dark`）

## 与 inline-visualizer-v3 的关系

| 维度 | inline-visualizer-v3 | Template 插件 |
|------|-----|----------|
| 渲染引擎 | 模型生成 HTML + Chart.js | 工具内置 Chart.js |
| 模型负担 | 需生成完整 HTML/CSS/JS | 只需扁平 JSON 参数 |
| 灵活性 | 完全自由 | 4 种函数，20+ 种参数 |
| 容错 | 依赖模型输出质量 | Python 端验证 + 纯文本错误 |
| 适用场景 | 复杂定制可视化 | 高频数据图表、KPI 仪表盘 |
