# Inline Visualizer Template

面向 Open WebUI 的快速模板可视化插件，使用 Chart.js 渲染。

这个插件用于补充 `inline-visualizer-v3`，不是替代它。模型调用三个自描述函数，传入扁平参数即可生成可视化，避免模型输出大量前端代码。

## 设计理念

v3 的 `render_visual_template` 只有一个函数，通过 `template` 枚举 + 嵌套 `data` 字典来区分可视化类型。模型看到 `data: Optional[Dict[str, Any]]` 无法理解具体结构，容易传错格式。

v4 拆分为三个独立函数，每个函数的参数即 schema：

| 维度 | v3 (旧) | v4 (新) |
|------|---------|---------|
| 函数数量 | 1 个通用函数 | 3 个独立函数 |
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
| `explanation` | `str` | 否 | 纯文本解释 |
| `title` | `str` | 否 | 标题，默认 "Data Detail" |

### render_chart

折线图、柱状图、饼图（Chart.js doughnut）、二维表格。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `series` | `list[dict]` | 是 | `[{label, value}]` 数组，label 为字符串，value 为数字 |
| `chart_type` | `"line" \| "bar" \| "pie" \| "table"` | 否 | 图表类型，默认 "line" |
| `title` | `str` | 否 | 标题，默认 "Chart" |

### render_dashboard

指标卡 + 可选趋势图。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `metrics` | `list[dict]` | 是 | `[{label, value, delta?}]` 数组 |
| `series` | `list[dict]` | 否 | 可选趋势图数据 `[{label, value}]` |
| `chart_title` | `str` | 否 | 趋势图标题 |
| `chart_type` | `"line" \| "bar" \| "pie"` | 否 | 趋势图类型，默认 "line" |
| `title` | `str` | 否 | 标题，默认 "Dashboard" |

## 数据合法性

参数格式不合法时，**Python 端直接返回纯文本错误消息**，模型能直接看到并纠正参数，不会生成 HTML 错误卡片。

## 推荐调用顺序

推荐（非强制）先调用 `render_data_detail` 展示数据来源，再调用目标图表：

1. 先调用 `render_data_detail`，展示 SQL、解释和数据表。
2. 再调用 `render_chart` 或 `render_dashboard`。

## 内置功能

- Chart.js 动画图表（line/bar/doughnut）
- 图表类型切换（line/bar/pie/table）
- 导出 PNG
- 统计信息：模板、图表类型、JSON 长度、HTML 长度、构建耗时、渲染耗时
- 自动深色模式适配（`prefers-color-scheme: dark`）

## 与 inline-visualizer-v3 的关系

| 维度 | v3 | template v4 |
|------|-----|----------|
| 渲染引擎 | 模型生成 HTML + Chart.js | 工具内置 Chart.js |
| 模型负担 | 需生成完整 HTML/CSS/JS | 只需扁平 JSON 参数 |
| 灵活性 | 完全自由 | 3 种函数，13 种参数 |
| 容错 | 依赖模型输出质量 | Python 端验证 + 纯文本错误 |
| 适用场景 | 复杂定制可视化 | 高频数据图表、KPI 仪表盘 |