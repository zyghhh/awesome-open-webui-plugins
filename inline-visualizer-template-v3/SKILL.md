---
name: inline-visualizer-template-v3
description: 使用内置模板快速渲染 Open WebUI 内联可视化。四个自描述函数：render_data_detail（数据详情）、render_chart（图表）、render_dashboard（轻量仪表盘）、render_analysis_dashboard（综合分析看板）。模型传入扁平参数，Chart.js 渲染由工具内置完成。
---

# 模板可视化 v3

使用四个独立函数生成常见可视化。不要手写 HTML、CSS、SVG 或 JavaScript。

## 核心规则

### 调用顺序（不可违反）

1. **所有可视化回答第一步 → `render_data_detail`**
2. **再调用恰好一个** `render_chart` / `render_dashboard` / `render_analysis_dashboard`
3. 禁止跳过 `render_data_detail` 直接调用图表或看板
4. 禁止在 `render_data_detail` 之后调用多个可视化函数
5. **禁止同时调用两种 dashboard**（`render_dashboard` + `render_analysis_dashboard`），它们互斥
6. **多轮对话中，每一次重新进行数据查询并可视化，都必须执行 `render_data_detail` → 恰好一个图表/看板函数**

### 每轮调用预算

“本轮”指从最新一条用户消息开始，到当前助手回答结束。每条新用户消息开始时，重新初始化以下预算：

- `detail_budget = 1`
- `final_visualization_budget = 1`

`render_data_detail` 成功返回后消耗 `detail_budget`。

`render_chart`、`render_dashboard`、`render_analysis_dashboard` 共享 `final_visualization_budget`；其中任意一个成功返回后，该预算立即耗尽，本轮不得再次调用、补充调用或切换到另一个最终可视化函数。

数据库查询、任务更新和其他非 `render_*` 工具不计入预算，也不会重置预算。只有下一条用户消息才能开始新的预算周期。

### 函数选择

| 用户意图 | 使用函数 | 何时不能用 |
|---------|---------|-----------|
| 单指标趋势/柱状/饼图/表格 | `render_chart` | — |
| KPI 概览 + 可选趋势图 | `render_dashboard` | 不要用于单图请求 |
| 明确要求综合分析、监控看板、诊断、多角度展示 | `render_analysis_dashboard` | 不要用于普通单图/趋势请求 |

**不要因为必须先展示数据详情表，就自动选择综合分析看板。** 普通单图、趋势、柱状、饼图或表格请求必须优先使用 `render_chart`。

### 合并优先

查询结果包含多个指标时，**合并到一个 dashboard**，不要拆成多个单图：

- 多个指标（如收入 + 用户数 + 转化率）→ `render_dashboard`，各指标放入 `metrics`
- 同维度多项对比 → `render_chart` + `chart_type="table"`
- 需要主图 + 排名 + 辅助图 + KPI 卡片 → `render_analysis_dashboard`

**禁止**连续多次调用 `render_chart` 展示相关数据。

### chart_type 选择

- 时间序列、趋势、排名、有顺序含义的数据 → `"line"`（默认）
- 无序分类（各省对比、产品对比）→ `"bar"`
- 占比、构成、份额 → `"pie"`
- 精确查看每个单元格的值 → `"table"`

拿不准时不要传 `chart_type`，工具默认 line。

## 各函数的使用约束

### render_data_detail

SQL + 解释 + 数据表预览。`columns` 和 `rows` 必填。

- `columns`：使用有意义的名称，这些名称将显示为表头
- `sql` / `sql_lines`：必须填写真实执行的数据查询 SQL，也就是实际产生 `rows` 的查询原文
- 禁止填写示例 SQL、占位 SQL、伪 SQL、模型编造 SQL；如果拿不到真实执行 SQL，就省略 SQL
- `sql`：单行 SQL 字符串，不要传 JSON 对象
- `sql_lines`：多行 SQL 必须传这个，避免字符串转义不稳定。示例：`["SELECT a, b", "FROM t", "WHERE c=1"]`
- `explanation`：最多 2 句话，不超过 80 字，不要用 markdown 或 HTML

SQL few-shot:
- GOOD multi-line SQL: `"sql_lines": ["SELECT month, revenue", "FROM sales", "ORDER BY month"]`
- GOOD single-line SQL: `"sql": "SELECT month, revenue FROM sales ORDER BY month"`
- AVOID JSON-wrapped SQL: `"sql": '{"sql":"SELECT month, revenue\\nFROM sales"}'`

SQL 和 explanation 在页面中默认折叠。数据表超过 10 行自动分页。

### render_chart

折线图、柱状图、饼图、二维表格。`series` 必填。

- **使用有意义的 key 名称**（如 `timestamp`、`revenue`），不要用通用的 `label`/`value`。x 轴是第一个非数值 key
- 先调用 `render_data_detail` 后，把同一批行数据转换为 `render_chart.series`，不要省略 `series`
- `y_axis_label`：完整 y 轴名称和单位，如 `"Revenue (USD)"`
- `y_axis_unit`：单个 y_column 显示为 `列名 (单位)`；多个 y_column 只有共享同一单位时才用
- 不能从数据值猜测单位；不确定时不要填单位

### render_dashboard

KPI 指标卡 + 可选趋势图。`metrics` 必填，`series`/`chart_type`/`chart_title` 可选。

- `metrics[].delta`：`+` 开头显示绿色，`-` 开头显示红色
- 趋势图 `y_axis_label` / `y_axis_unit` 规则同 `render_chart`
- 多指标不同单位时不要强行共用单位

### render_analysis_dashboard

综合分析看板。`hero_chart` 必填，其余模块可选。

- 不替代 `render_data_detail`：如果用户需要 SQL 或完整明细，必须先调用 `render_data_detail`
- `hero_chart`：主图（同 `render_chart` 的 series 块）
- `rankings`：Top N、峰值排行（`items[].label/value/unit?`）
- `small_charts`：最多 2 个辅助小图
- `summary_cards`：底部摘要指标卡（`label/value/delta?`）

## 输出纪律

1. 只有在查询已完成且数据已正确展示后，才用自然语言简要说明结果
2. 不要输出 `@@@VIZ-START`、HTML、CSS、SVG、JavaScript、代码块
3. 保持 JSON 简洁，不要把展示代码塞进 JSON 字段
4. 只有模板无法表达用户需求时，才切换到 inline-visualizer-v3
