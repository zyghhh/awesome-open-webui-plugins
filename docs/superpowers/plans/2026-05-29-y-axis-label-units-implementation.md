# Y-Axis Label Units Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add unit-safe y-axis labels to `inline-visualizer-template` line and bar charts, including dashboard trend charts and PNG exports.

**Architecture:** Normalize a final `y_axis_label` string in Python and serialize it in the existing chart/dashboard payload. Render it with Chart.js native `scales.y.title` so the label is drawn inside the canvas and included in the existing canvas PNG export. Units are only displayed when explicitly supplied by `y_axis_label` or safely combined from `y_axis_unit` for exactly one y-column.

**Tech Stack:** Python async Open WebUI tool, embedded JavaScript, Chart.js, `unittest`.

---

## File Structure

- Modify `inline-visualizer-template/tool.py`
  - Add a Python helper `_resolve_y_axis_label`.
  - Add `y_axis_label` and `y_axis_unit` parameters to `render_chart` and `render_dashboard`.
  - Serialize `data["y_axis_label"]` for chart and dashboard payloads.
  - Add JS helpers `axisTitleFromData` and `yScaleOptions`.
  - Use the helper in chart and dashboard line/bar Chart.js configs.
- Modify `inline-visualizer-template/test_dashboard_table.py`
  - Add tests for explicit labels, unit-safe single-series labels, ignored unsafe multi-series units, dashboard labels, and Chart.js title config.
- Modify `inline-visualizer-template/README.md`
  - Document the new chart/dashboard parameters and unit correctness rules.
- Modify `inline-visualizer-template/SKILL.md`
  - Teach the calling model to use `y_axis_label` for exact units and `y_axis_unit` only for one y-column.
- Modify root `README.md` and `README.zh.md`
  - Update short feature descriptions to mention y-axis labels and units.

---

### Task 1: Add Failing Tests for Unit-Safe Payloads and Chart.js Titles

**Files:**
- Modify: `inline-visualizer-template/test_dashboard_table.py`

- [ ] **Step 1: Add tests to `DashboardTableTest`**

Insert these methods after `test_render_chart_accepts_rows_alias_after_data_detail` in `inline-visualizer-template/test_dashboard_table.py`:

```python
    def test_render_chart_uses_explicit_y_axis_label(self):
        html = self.render_chart_html(
            series=[
                {"month": "Jan", "revenue": 120},
                {"month": "Feb", "revenue": 148},
            ],
            chart_type="line",
            y_axis_label="Revenue (USD)",
            title="Monthly Revenue",
        )

        self.assertIn('"y_axis_label":"Revenue (USD)"', html)
        self.assertIn("function yScaleOptions(yAxisLabel, textColor, gridColor)", html)
        self.assertIn("title: {", html)
        self.assertIn("text: yAxisLabel", html)
        self.assertIn("y: yScaleOptions(yAxisLabel, textColor, gridColor)", html)

    def test_render_chart_combines_single_y_column_with_explicit_unit(self):
        html = self.render_chart_html(
            series=[
                {"time": "00:00", "requests": 120},
                {"time": "01:00", "requests": 148},
            ],
            chart_type="bar",
            y_axis_unit="rpm",
            title="Request Rate",
        )

        self.assertIn('"y_columns":["requests"]', html)
        self.assertIn('"y_axis_label":"requests (rpm)"', html)

    def test_render_chart_does_not_apply_unit_to_multiple_y_columns(self):
        html = self.render_chart_html(
            series=[
                {"month": "Jan", "revenue": 120, "users": 500},
                {"month": "Feb", "revenue": 148, "users": 600},
            ],
            chart_type="line",
            y_columns=["revenue", "users"],
            y_axis_unit="USD",
            title="Revenue and Users",
        )

        self.assertIn('"y_columns":["revenue","users"]', html)
        self.assertIn('"y_axis_label":"revenue, users"', html)
        self.assertNotIn('"y_axis_label":"revenue, users (USD)"', html)
        self.assertNotIn('"y_axis_label":"revenue (USD), users (USD)"', html)

    def test_render_dashboard_applies_same_y_axis_label_rules(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Peak", "value": "5,677 rpm"}],
            series=[
                {"time": "00:00", "requests": 120},
                {"time": "01:00", "requests": 148},
            ],
            chart_type="line",
            y_axis_label="Requests (rpm)",
            title="Traffic Dashboard",
        )

        self.assertIn('"y_axis_label":"Requests (rpm)"', html)
        self.assertIn("var dashYAxisLabel = axisTitleFromData(data, dashYCols);", html)
        self.assertIn("y: yScaleOptions(dashYAxisLabel, textColor, gridColor)", html)
```

- [ ] **Step 2: Run the focused tests and verify failure**

Run:

```bash
python -m unittest inline-visualizer-template/test_dashboard_table.py -v
```

Expected: FAIL with `TypeError: Tools.render_chart() got an unexpected keyword argument 'y_axis_label'` or `y_axis_unit`, and missing JS helper assertions.

---

### Task 2: Add Python Label Normalization and Public Parameters

**Files:**
- Modify: `inline-visualizer-template/tool.py`

- [ ] **Step 1: Add `_resolve_y_axis_label` near the other Python helpers**

Find the helper section above `_render_response`. Add:

```python
def _resolve_y_axis_label(
    y_columns: List[str],
    *,
    y_axis_label: str = "",
    y_axis_unit: str = "",
    chart_type: str = "line",
) -> str:
    """Return a display-safe y-axis label without guessing units."""
    if chart_type in {"pie", "table"}:
        return ""

    explicit_label = str(y_axis_label or "").strip()
    if explicit_label:
        return explicit_label

    clean_columns = [str(col).strip() for col in y_columns if str(col).strip()]
    if not clean_columns:
        return ""

    base_label = clean_columns[0] if len(clean_columns) == 1 else ", ".join(clean_columns)
    explicit_unit = str(y_axis_unit or "").strip()
    if explicit_unit and len(clean_columns) == 1:
        return f"{base_label} ({explicit_unit})"

    return base_label
```

- [ ] **Step 2: Update `render_chart` signature and docstring**

Change:

```python
    async def render_chart(
        self,
        series: Any = None,
        chart_type: ChartType = "line",
        y_columns: Any = None,
        rows: Any = None,
        title: str = "Chart",
    ) -> tuple:
```

to:

```python
    async def render_chart(
        self,
        series: Any = None,
        chart_type: ChartType = "line",
        y_columns: Any = None,
        rows: Any = None,
        title: str = "Chart",
        y_axis_label: str = "",
        y_axis_unit: str = "",
    ) -> tuple:
```

Add these docstring lines after the `:param y_columns:` block:

```python
        :param y_axis_label: Optional complete y-axis label, including unit when
            needed, e.g. "Revenue (USD)". Highest priority and never modified.
        :param y_axis_unit: Optional unit for exactly one y-column, e.g. "rpm".
            Ignored for multi-series charts to avoid incorrect unit display.
```

- [ ] **Step 3: Serialize `y_axis_label` in `render_chart`**

After the `data` dict is created:

```python
        data: Dict[str, Any] = {
            "series": clean,
            "y_columns": resolved_y,
            "x_column": x_col,
        }
```

add:

```python
        data["y_axis_label"] = _resolve_y_axis_label(
            resolved_y,
            y_axis_label=y_axis_label,
            y_axis_unit=y_axis_unit,
            chart_type=chart_type,
        )
```

Leave the existing `chart_type == "table"` branch replacing `data` unchanged so tables do not get a y-axis label.

- [ ] **Step 4: Update `render_dashboard` signature and docstring**

Change:

```python
    async def render_dashboard(
        self,
        metrics: Any,
        series: Any = None,
        chart_title: str = "",
        chart_type: DashChartType = "line",
        y_columns: Any = None,
        title: str = "Dashboard",
    ) -> tuple:
```

to:

```python
    async def render_dashboard(
        self,
        metrics: Any,
        series: Any = None,
        chart_title: str = "",
        chart_type: DashChartType = "line",
        y_columns: Any = None,
        title: str = "Dashboard",
        y_axis_label: str = "",
        y_axis_unit: str = "",
    ) -> tuple:
```

Add these docstring lines after the `:param y_columns:` block:

```python
        :param y_axis_label: Optional complete y-axis label for the trend chart,
            including unit when needed, e.g. "Requests (rpm)".
        :param y_axis_unit: Optional trend chart unit for exactly one y-column.
            Ignored for multi-series trend charts to avoid incorrect units.
```

- [ ] **Step 5: Serialize `y_axis_label` in `render_dashboard` only when trend data exists**

Inside the `if series is not None:` block, after:

```python
                data["series"] = clean_series
                data["x_column"] = dash_x_col
                data["y_columns"] = dash_y_cols
```

add:

```python
                data["y_axis_label"] = _resolve_y_axis_label(
                    dash_y_cols,
                    y_axis_label=y_axis_label,
                    y_axis_unit=y_axis_unit,
                    chart_type=chart_type,
                )
```

- [ ] **Step 6: Run focused tests and verify remaining JS failures**

Run:

```bash
python -m unittest inline-visualizer-template/test_dashboard_table.py -v
```

Expected: the payload assertions for `"y_axis_label"` pass; tests still fail for missing JS helpers/config.

---

### Task 3: Render Chart.js Native Y-Axis Titles

**Files:**
- Modify: `inline-visualizer-template/tool.py`

- [ ] **Step 1: Add shared JS helpers after `buildChartDatasets`**

Find `function buildChartDatasets(...)` and add this immediately after it:

```javascript
  function axisTitleFromData(data, yCols) {
    if (data && typeof data.y_axis_label === 'string') return data.y_axis_label.trim();
    if (!Array.isArray(yCols) || yCols.length === 0) return '';
    return yCols.map(function(col) { return String(col); }).join(', ');
  }

  function yScaleOptions(yAxisLabel, textColor, gridColor) {
    return {
      grid: { color: gridColor },
      ticks: { color: textColor, font: {size:11} },
      border: { display: false },
      title: {
        display: !!yAxisLabel,
        text: yAxisLabel,
        color: textColor,
        font: { size: 11, weight: '600' },
        padding: { bottom: 6 }
      }
    };
  }
```

- [ ] **Step 2: Use the helper in `renderChart`**

In `renderChart(chartType, data)`, after:

```javascript
    var datasets = buildChartDatasets(series, yCols, isMulti, chartType, 4, 6, bgColor);
```

add:

```javascript
    var yAxisLabel = axisTitleFromData(data, yCols);
```

In the bar Chart.js config, replace the current y scale:

```javascript
            y: { grid: { color: gridColor }, ticks: { color: textColor, font: {size:11} }, border: { display: false } }
```

with:

```javascript
            y: yScaleOptions(yAxisLabel, textColor, gridColor)
```

In the line Chart.js config, replace the same y scale with:

```javascript
            y: yScaleOptions(yAxisLabel, textColor, gridColor)
```

- [ ] **Step 3: Use the helper in `renderDashboard`**

In `renderDashboard(data, chartType)`, after:

```javascript
      var datasets = buildChartDatasets(series, dashYCols, dashMulti, chartType, 3, 5, bgColor);
```

add:

```javascript
      var dashYAxisLabel = axisTitleFromData(data, dashYCols);
```

In the dashboard bar config, replace:

```javascript
            scales: { x: { grid: {display:false}, ticks: {color:textColor,font:{size:11}}, border: {color:gridColor} }, y: { grid: {color:gridColor}, ticks: {color:textColor,font:{size:11}}, border: {display:false} } }
```

with:

```javascript
            scales: { x: { grid: {display:false}, ticks: {color:textColor,font:{size:11}}, border: {color:gridColor} }, y: yScaleOptions(dashYAxisLabel, textColor, gridColor) }
```

In the dashboard line config, replace:

```javascript
            scales: { x: { grid: {display:false}, ticks: {color:textColor,font:{size:11},maxRotation:45}, border: {color:gridColor} }, y: { grid: {color:gridColor}, ticks: {color:textColor,font:{size:11}}, border: {display:false} } }
```

with:

```javascript
            scales: { x: { grid: {display:false}, ticks: {color:textColor,font:{size:11},maxRotation:45}, border: {color:gridColor} }, y: yScaleOptions(dashYAxisLabel, textColor, gridColor) }
```

- [ ] **Step 4: Run focused tests and verify pass**

Run:

```bash
python -m unittest inline-visualizer-template/test_dashboard_table.py -v
```

Expected: PASS.

---

### Task 4: Update Plugin Documentation and Skill Instructions

**Files:**
- Modify: `inline-visualizer-template/README.md`
- Modify: `inline-visualizer-template/SKILL.md`
- Modify: `README.md`
- Modify: `README.zh.md`

- [ ] **Step 1: Update `inline-visualizer-template/README.md` parameter tables**

In the `render_chart` table, add rows after `chart_type`:

```markdown
| `y_columns` | `list[str]` | 否 | 指定绘图数值列；不传时优先使用 `value`，否则自动检测数值列。`pie` 只使用第一个数值列 |
| `y_axis_label` | `str` | 否 | 完整 y 轴名称和单位，如 `"Revenue (USD)"`；优先级最高，导出 PNG 会包含 |
| `y_axis_unit` | `str` | 否 | 单 y 列图表的单位，如 `"rpm"`；多 y 列时不会自动套用，避免单位错误 |
```

In the `render_dashboard` table, add rows after `y_columns`:

```markdown
| `y_axis_label` | `str` | 否 | 趋势图完整 y 轴名称和单位，如 `"Requests (rpm)"`；导出 PNG 会包含 |
| `y_axis_unit` | `str` | 否 | 单 y 列趋势图的单位；多 y 列时不会自动套用 |
```

Add this paragraph after the `render_dashboard` table:

```markdown
单位规则：工具不会从数据值里猜单位。需要准确单位时优先传 `y_axis_label`，例如 `"Revenue (USD)"`。只有单个 y 列时才使用 `y_axis_unit` 自动组合为 `列名 (单位)`；多 y 列图表如果单位不同，必须用不含错误单位的 `y_axis_label` 或只显示列名。
```

- [ ] **Step 2: Update `inline-visualizer-template/SKILL.md` chart guidance**

In the `render_chart` bullet list after `- pie 只使用第一个 y_column`, add:

```markdown
- `y_axis_label`：可选，完整 y 轴名称和单位，如 `"Revenue (USD)"`。需要导出图片可独立理解时优先传这个。
- `y_axis_unit`：可选，只能在单个 y_column 且单位明确时使用，如 `"rpm"`；多 y_column 不要用它自动套单位，避免单位错误。
- 单位不能从数据值猜测；如果不确定单位，不要填单位，只填准确的列名/指标名。
```

In the `render_dashboard` bullet list after `- y_columns：可选...`, add:

```markdown
- `y_axis_label` / `y_axis_unit`：趋势图 y 轴名称和单位，规则同 `render_chart`。多指标不同单位时不要强行共用单位。
```

- [ ] **Step 3: Update root README feature summaries**

In `README.md`, replace the Template `render_chart` sentence:

```markdown
2. **`render_chart`** — Line, bar, pie (doughnut via Chart.js), or table. `series` as `[{label, value}]` array. Multi-column support with `y_columns`. Auto-detects numeric columns. Chart type switcher, PNG export.
```

with:

```markdown
2. **`render_chart`** — Line, bar, pie (doughnut via Chart.js), or table. `series` as `[{label, value}]` array. Multi-column support with `y_columns`. Auto-detects numeric columns. Unit-safe y-axis labels for line/bar charts. Chart type switcher, PNG export.
```

In `README.zh.md`, replace the corresponding sentence with:

```markdown
2. **`render_chart`** — 折线图、柱状图、饼图（Chart.js doughnut）、表格。`series` 为 `[{label, value}]` 数组。支持多列数据配合 `y_columns`。自动检测数值列。折线/柱状图支持单位安全的 y 轴名称。图表类型切换、PNG 导出。
```

- [ ] **Step 4: Run documentation-sensitive tests**

Run:

```bash
python -m unittest inline-visualizer-template/test_analysis_dashboard.py -v
```

Expected: PASS.

---

### Task 5: Full Verification and Commit

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run all inline visualizer template tests**

Run:

```bash
python -m unittest inline-visualizer-template/test_dashboard_table.py inline-visualizer-template/test_analysis_dashboard.py -v
```

Expected: PASS.

- [ ] **Step 2: Inspect generated HTML for exact unit behavior**

Run:

```bash
python -m unittest inline-visualizer-template/test_dashboard_table.py::DashboardTableTest.test_render_chart_does_not_apply_unit_to_multiple_y_columns -v
```

If `unittest` does not accept the `::` selector in this environment, run:

```bash
python -m unittest inline-visualizer-template.test_dashboard_table.DashboardTableTest.test_render_chart_does_not_apply_unit_to_multiple_y_columns -v
```

Expected: PASS and confirms multi-series unit is not applied.

- [ ] **Step 3: Check git diff**

Run:

```bash
git diff -- inline-visualizer-template/tool.py inline-visualizer-template/test_dashboard_table.py inline-visualizer-template/README.md inline-visualizer-template/SKILL.md README.md README.zh.md
```

Expected: diff only contains y-axis label/unit changes and documentation updates.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add inline-visualizer-template/tool.py inline-visualizer-template/test_dashboard_table.py inline-visualizer-template/README.md inline-visualizer-template/SKILL.md README.md README.zh.md
git commit -m "feat: add unit-safe y-axis labels"
```

Expected: commit succeeds.

---

## Self-Review

- Spec coverage: The plan covers public API parameters, unit correctness, Chart.js native canvas rendering, dashboard parity, docs, and tests.
- Placeholder scan: No `TBD`, `TODO`, or vague "add tests" steps remain; each code change has concrete snippets and commands.
- Type consistency: The final serialized key is consistently `y_axis_label`; Python parameters are `y_axis_label` and `y_axis_unit`; JS helper names are `axisTitleFromData` and `yScaleOptions`.

