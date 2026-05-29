# Y-Axis Label and Units Design

## Goal

Add readable y-axis names and units to `inline-visualizer-template` charts so exported PNGs remain understandable without chat context.

## Scope

This applies to `render_chart` and the trend chart inside `render_dashboard` for `line` and `bar` chart types. `pie` and `table` have no y-axis and will not render a y-axis title.

## Current Behavior

The plugin resolves y-axis data columns from `y_columns` or numeric auto-detection, then renders Chart.js line/bar charts with tick labels only. Dashboard trend charts use a separate Chart.js configuration but the same data normalization pattern. PNG export currently exports the canvas, so any label drawn outside the canvas would be omitted.

## Selected Approach

Use Chart.js native `scales.y.title` for the visible y-axis label. This keeps the label inside the canvas, so existing PNG export includes it automatically.

Combine explicit unit-safe labeling with a backward-compatible fallback:

1. `y_axis_label` is the complete label and has highest priority.
2. `y_axis_unit` is optional and only combined with a single y-column label.
3. If neither is provided, infer the label from `y_columns`.

## Unit Correctness Rules

Units must not be guessed from data values. The implementation may display a unit only when the caller explicitly supplies `y_axis_unit` or when the caller supplies a complete `y_axis_label` containing the unit.

Single-series behavior:

- `y_axis_label="Revenue (USD)"` displays `Revenue (USD)`.
- `y_axis_unit="USD"` with `y_columns=["revenue"]` displays `revenue (USD)`.
- No explicit unit displays `revenue`.

Multi-series behavior:

- `y_axis_label` displays exactly as provided, allowing the caller to provide a correct shared unit such as `Requests (rpm)`.
- `y_axis_unit` without `y_axis_label` is not applied to multiple y-columns, because different columns may have different units.
- No explicit label displays the column names joined by comma, such as `revenue, users`.

## API Changes

Add optional parameters to both public functions:

- `y_axis_label: str = ""`
- `y_axis_unit: str = ""`

Both parameters are optional and preserve existing calls. The rendered payload will include:

- `y_axis_label`: normalized final label string, or an empty string for pie/table.

## Rendering Behavior

For line and bar charts, configure Chart.js:

```javascript
scales: {
  y: {
    title: {
      display: !!yAxisLabel,
      text: yAxisLabel,
      color: textColor,
      font: { size: 11, weight: '600' },
      padding: { bottom: 6 }
    }
  }
}
```

The helper should be shared by chart and dashboard rendering so both surfaces remain consistent.

## Documentation

Update the README and skill docs to explain:

- Prefer `y_axis_label` when the chart needs a precise exported label.
- Use `y_axis_unit` only when the chart has a single y-column with a clear unit.
- Multi-series charts with different units should use `y_axis_label` only if the label is accurate for all series.

## Tests

Add focused unit tests around generated HTML and payload serialization:

- `render_chart` includes an explicit `y_axis_label`.
- `render_chart` combines single y-column plus `y_axis_unit`.
- `render_chart` does not apply `y_axis_unit` to multiple y-columns.
- `render_dashboard` applies the same label rules to its trend chart.
- Chart.js y-axis title configuration exists for line/bar charts.

