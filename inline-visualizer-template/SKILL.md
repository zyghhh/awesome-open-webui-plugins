---
name: visual_template
description: 使用内置模板快速渲染 Open WebUI 内联可视化。四个自描述函数：render_data_detail（数据详情）、render_chart（图表）、render_dashboard（轻量仪表盘）、render_analysis_dashboard（综合分析看板）。模型传入扁平参数，Chart.js 渲染由工具内置完成。
---

# 模板可视化

使用四个独立函数生成常见可视化，每个函数的参数即 schema，模型无需查文档即可正确调用。不要手写 HTML、CSS、SVG 或 JavaScript。

## 调用规则

### 合并优先 — 避免同质化多图

**数据详情表必须先展示。** 每个包含可视化的回答都必须先调用 `render_data_detail` 展示源数据表；然后才允许再调用至多一个 `render_chart` / `render_dashboard` / `render_analysis_dashboard`。不要直接调用图表或看板。不要因为必须先展示数据详情表，就自动选择综合分析看板。

同一个回答中除 `render_data_detail` 外，**最多再调用一次可视化函数**。相关数据合并展示，不要拆成多个孤立的单图。

| 数据特征 | 合并策略 |
|---------|---------|
| 多个指标（如收入 + 用户数 + 转化率） | 一个 `render_dashboard`，各指标放入 `metrics` |
| 明确要求综合分析/监控诊断/多模块看板 | 一个 `render_analysis_dashboard`，用主图 + 排名 + 辅助图 + KPI 卡片 |
| 同维度多项对比（如各省收入 + 各省用户数） | 一个 `render_chart` + `chart_type="table"` 展示完整数据表 |
| 单指标、单维度 | 一个 `render_chart` |

**禁止**：连续多次调用 `render_chart` 展示相关数据。例如"各省收入"和"各省用户数"应合并为一个 table 或 dashboard，不要拆成两个 bar chart。

### 调用流程

1. 所有可视化回答第一步 → `render_data_detail`
2. 普通单图、趋势、柱状、饼图或表格请求必须优先使用 `render_chart`（仅调用一次）
3. 用户要求 KPI/概览/多个指标 → 再调用 `render_dashboard`（仅调用一次）
4. 只有当用户明确要求综合分析、监控看板、诊断、多角度展示，或需要主图 + 排名/辅助图/摘要卡片等 3 个以上语义模块时，才调用 `render_analysis_dashboard`（仅调用一次）
5. 不允许跳过 `render_data_detail` 直接调用图表或看板
6. 调用后只用自然语言简要说明结果
7. 不要输出 `@@@VIZ-START`、HTML、CSS、SVG、JavaScript、代码块

## 适用场景

优先使用本 skill：

- `render_data_detail`：SQL、解释、数据表预览
- `render_chart`：折线图、柱状图、饼图、二维表格
- `render_dashboard`：轻量多指标卡片 + 可选趋势图
- `render_analysis_dashboard`：固定版式 + 可配置语义模块的综合分析看板，优先适配时序监控，也支持业务分析

语义边界：

- `render_data_detail` 是完整数据来源和 SQL 的唯一职责入口。`render_analysis_dashboard` 不再包含详细数据模块，避免和数据详情表重复。
- `render_chart` 解决单个图表问题。
- `render_dashboard` 解决轻量 KPI + 一个趋势图。
- `render_analysis_dashboard` 解决多模块综合分析，不替代数据明细表，也不用于普通单图请求。

只有模板无法表达用户需求时，才切换到 inline-visualizer-v3。

## 函数签名与示例

所有参数均为扁平传参，不需要嵌套 `data` 包装。

### render_data_detail

SQL + 解释 + 数据表预览。`columns` 和 `rows` 必填，`sql` 和 `explanation` 可选。

- `columns`：列名数组。**使用有意义的名称**，这些名称将显示为表头。
- `sql`：原始 SQL 查询字符串，可选。不要传 JSON 对象。
- `explanation`：纯文本解释，**最多 2 句话，不超过 80 字**。不要用 markdown、HTML 或换行。

```json
{
  "columns": ["month", "revenue", "growth"],
  "rows": [
    {"month": "Jan", "revenue": 120, "growth": "+8%"},
    {"month": "Feb", "revenue": 148, "growth": "+12%"},
    {"month": "Mar", "revenue": 132, "growth": "+5%"}
  ],
  "sql": "SELECT month, revenue FROM sales ORDER BY month",
  "explanation": "按月汇总收入，展示Q1收入趋势。",
  "title": "Sales Data"
}
```

SQL 和 explanation 在页面中**默认折叠**，点击展开。数据表始终可见，超过 10 行自动分页。

### render_chart

折线图、柱状图、饼图、二维表格。`series` 必填，支持**单列**和**多列**数据。先调用 `render_data_detail` 后，如需继续画单图，把同一批行数据转换为 `render_chart.series`，不要省略 `series`。

**关键规则：series 中每个对象的 key 名称即列名。使用有意义的名称（如 `timestamp`、`revenue`），不要用通用的 `label`/`value`。这样切换到 table 视图时列名才能与 data_detail 保持一致。**x 轴列是第一个非数值 key，其余数值列为 y 轴。

**单列数据**（一个指标）：

```json
{
  "series": [
    {"month": "Jan", "revenue": 120},
    {"month": "Feb", "revenue": 148},
    {"month": "Mar", "revenue": 132}
  ],
  "chart_type": "line",
  "title": "Monthly Revenue"
}
```

**多列数据**（多个指标在同一张图上对比，line 多线、bar 分组柱状）：

```json
{
  "series": [
    {"month": "Jan", "revenue": 120, "users": 500},
    {"month": "Feb", "revenue": 148, "users": 600},
    {"month": "Mar", "revenue": 132, "users": 550}
  ],
  "y_columns": ["revenue", "users"],
  "chart_type": "line",
  "title": "Revenue & Users"
}
```

- `y_columns`：指定哪些列绘图，可选（不传则自动检测数值列）
- 多列时 line 渲染多条线、bar 渲染分组柱状，自动显示图例
- pie 只使用第一个 y_column
- `y_axis_label`：可选，完整 y 轴名称和单位，如 `"Revenue (USD)"`。需要导出图片可独立理解时优先传这个。
- `y_axis_unit`：可选，只能在单个 y_column 且单位明确时使用，如 `"rpm"`；多 y_column 不要用它自动套单位，避免单位错误。
- 单位不能从数据值猜测；如果不确定单位，不要填单位，只填准确的列名/指标名。

`chart_type` 选项：
- `line`（默认）：时间序列折线图
- `bar`：柱状图，每根柱子独立颜色
- `pie`：环形图（doughnut）
- `table`：HTML 表格，自动从 series 生成

### render_dashboard

KPI 指标卡 + 可选趋势图。`metrics` 必填，`series`、`chart_title`、`chart_type`、`y_columns`、`title` 可选。支持单列和多列趋势数据。

```json
{
  "metrics": [
    {"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"},
    {"label": "Active Users", "value": "48.2K", "delta": "+6.1%"},
    {"label": "Avg Latency", "value": "184ms", "delta": "-8.0%"}
  ],
  "series": [
    {"month": "Jan", "revenue": 120, "users": 500},
    {"month": "Feb", "revenue": 148, "users": 600},
    {"month": "Mar", "revenue": 132, "users": 550}
  ],
  "y_columns": ["revenue", "users"],
  "chart_title": "Monthly Trend",
  "chart_type": "line",
  "title": "Q1 Overview"
}
```

- `metrics[].delta`：可选，`+` 开头显示绿色，`-` 开头显示红色
- `series`：可选，传入后在指标卡下方渲染趋势图。支持有意义的 key 名称（如 `month`、`revenue`），多列时 line 渲染多条线、bar 渲染分组柱状，自动显示图例
- `y_columns`：可选，指定哪些数值列绘图（不传则自动检测数值列）。pie 只使用第一个 y_column
- `y_axis_label` / `y_axis_unit`：趋势图 y 轴名称和单位，规则同 `render_chart`。多指标不同单位时不要强行共用单位。

### render_analysis_dashboard

综合分析看板。固定版式 + 可配置语义模块，适合明确要求的时序监控、业务诊断、多角度分析。`hero_chart` 必填，其余模块可选。它不替代 `render_data_detail`：如果用户需要 SQL、原始数据、完整明细或数据来源，必须先调用 `render_data_detail`。不要把普通趋势图、柱状图、饼图、表格请求升级为综合分析看板。

```json
{
  "title": "Service Traffic Analysis",
  "subtitle": "24-hour monitor overview",
  "hero_chart": {
    "title": "Traffic Trend",
    "chart_type": "line",
    "series": [
      {"time": "00:00", "requests": 120, "errors": 3},
      {"time": "01:00", "requests": 148, "errors": 5}
    ],
    "y_columns": ["requests", "errors"]
  },
  "rankings": {
    "title": "Peak Services",
    "items": [
      {"label": "api-a", "value": 5677, "unit": "rpm"},
      {"label": "api-b", "value": 4805, "unit": "rpm"}
    ]
  },
  "small_charts": [
    {
      "title": "Error Rate",
      "chart_type": "line",
      "series": [
        {"time": "00:00", "rate": 1.2},
        {"time": "01:00", "rate": 1.5}
      ]
    }
  ],
  "summary_cards": [
    {"label": "Peak", "value": "5,677 rpm", "delta": "+8%"},
    {"label": "Avg", "value": "3,120 rpm"}
  ]
}
```

- `hero_chart`：主图，通常用于时序趋势、主指标对比或核心业务走势
- `rankings`：Top N、峰值排行、贡献度排行，可选
- `small_charts`：最多 2 个辅助小图，可选
- `summary_cards`：底部摘要指标卡，可选

### 多指标合并示例

查询结果包含多个指标（如各省的收入、用户数、增长率）时，**合并到一个 dashboard**，不要拆成多个单图：

```json
// render_dashboard — 一次调用展示全部指标，趋势图多列对比
{
  "metrics": [
    {"label": "Total Revenue", "value": "$12.8M", "delta": "+12.4%"},
    {"label": "Active Users", "value": "48.2K", "delta": "+6.1%"},
    {"label": "Conversion Rate", "value": "3.8%", "delta": "+0.3%"}
  ],
  "chart_title": "Monthly Trend",
  "series": [
    {"month": "Jan", "revenue": 120, "users": 500},
    {"month": "Feb", "revenue": 148, "users": 600},
    {"month": "Mar", "revenue": 132, "users": 550}
  ],
  "y_columns": ["revenue", "users"],
  "chart_type": "line",
  "title": "Q1 Business Overview"
}
```

需要精确对比多个维度的每个值时，用一个 `chart_type="table"` 代替多个 chart。

## 选择规则

默认 `chart_type` 为 `"line"`。拿不准时就不要传 `chart_type`，工具默认 line。

- 时间序列、趋势、排名、任何有顺序含义的数据 → `chart_type="line"`（默认）
- 仅当数据是无序分类（互不相关的并列项，如各省对比、产品对比）→ `chart_type="bar"`
- 占比、构成、份额 → `chart_type="pie"`
- 精确查看每个单元格的值 → `chart_type="table"`
- 多个指标 + 趋势 → `render_dashboard`
- 只有明确的综合分析、监控看板、诊断、多角度展示 → `render_analysis_dashboard`
- 展示数据来源和 SQL → `render_data_detail`（所有可视化回答必须先调用）

## 渲染效果

所有函数生成包含以下功能的 HTML：
- Chart.js 动画图表（line/bar/doughnut）
- 图表类型切换（render_chart 和 render_dashboard）
- 综合分析看板（render_analysis_dashboard）
- 导出 PNG
- 统计信息：模板、图表类型、JSON 长度、HTML 长度、构建耗时、渲染耗时
- 自动深色模式适配

## 数据合法性

Python 端验证参数格式。如果数据不合法，返回纯文本错误消息（模型可直接看到并纠正），不生成 HTML。

## 输出纪律

保持 JSON 简洁、结构化。不要把展示代码塞进 JSON 字段，不添加 inline style，不传 raw SVG path。如果需要完全自定义几何图形或复杂应用式交互，切换到 inline-visualizer-v3。
