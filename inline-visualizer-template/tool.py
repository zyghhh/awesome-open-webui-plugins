"""
title: Inline Visualizer Template
author: Derek
version: 0.4.0
license: MIT
description: Fast template-based visualizations for Open WebUI. Three self-describing functions — render_data_detail, render_chart, render_dashboard — each with flat, typed parameters. Chart.js rendering, dark-mode-safe, PNG export.
required_open_webui_version: 0.9.5

tool_instructions: |
  Arguments MUST be valid JSON objects.

  Rules:
  - Do NOT wrap arguments in XML.
  - Do NOT HTML-escape quotes (no &quot;).
  - Arrays and objects must be native JSON, not strings.
  - Numbers must be numbers, not strings.
  - ALL parameters are direct values — no nested "data" wrapper.

  --- render_data_detail: SQL + explanation + data table preview ---
  {
    "columns": ["month", "revenue", "growth"],
    "rows": [
      {"month": "Jan", "revenue": 120, "growth": "+8%"},
      {"month": "Feb", "revenue": 148, "growth": "+12%"}
    ],
    "sql": "SELECT month, revenue FROM sales ORDER BY month",
    "explanation": "Monthly revenue trend for Q1 2025.",
    "title": "Sales Data"
  }
  columns: list of column name strings (required).
  rows: list of row objects (required). Keys must match columns.
  sql: raw SQL string (optional). Do NOT pass a JSON object — must be a plain string.
  explanation: plain text (optional). Max 2 sentences, ≤80 chars. No markdown, no HTML, no line breaks.
  SQL and explanation are collapsed by default — click to expand.
  title: shown in the toolbar (optional, defaults to "Data Detail").

  --- render_chart: line / bar / pie / table ---

  IMPORTANT: Use meaningful key names in series objects — they become table column headers
  when the user switches to table view. The x-axis key is the first non-numeric column;
  all numeric columns are plotted on the y-axis. Do NOT use generic "label"/"value" keys.

  Single series (1 metric):
  {
    "series": [
      {"month": "Jan", "revenue": 120},
      {"month": "Feb", "revenue": 148},
      {"month": "Mar", "revenue": 132}
    ],
    "chart_type": "line",
    "title": "Monthly Revenue"
  }

  Multi-series (multiple metrics on one chart):
  {
    "series": [
      {"month": "Jan", "revenue": 120, "users": 500},
      {"month": "Feb", "revenue": 148, "users": 600},
      {"month": "Mar", "revenue": 132, "users": 550}
    ],
    "y_columns": ["revenue", "users"],
    "chart_type": "line",
    "title": "Revenue & Users Trend"
  }
  Multi-series renders grouped bars (bar) or multiple lines with legend (line).
  Pie only uses the first y_column.

  series: list of objects (required). Each must have one x-axis key (string) plus one or more numeric value columns.
  y_columns: which columns to plot on y-axis (optional). Auto-detected if omitted.
  chart_type: "line" | "bar" | "pie" | "table" (optional, defaults to "line").
  title: shown in the toolbar (optional, defaults to "Chart").

  --- render_dashboard: KPI metric cards + optional trend chart ---
  {
    "metrics": [
      {"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"},
      {"label": "Active Users", "value": "48.2K", "delta": "+6.1%"},
      {"label": "Avg Latency", "value": "184ms", "delta": "-8.0%"}
    ],
    "series": [
      {"label": "Jan", "value": 120},
      {"label": "Feb", "value": 148}
    ],
    "chart_title": "Monthly Trend",
    "chart_type": "line",
    "title": "Q1 Overview"
  }
  metrics: list of {label, value, delta?} objects (required).
    label: metric name (string).
    value: display value (string or number, e.g. "$3.87M" or 48200).
    delta: change indicator (string, optional, e.g. "+12.4%" or "-8.0%").
  series: optional trend chart data (list of {label, value}).
  chart_title: label for the trend chart (optional).
  chart_type: "line" | "bar" | "pie" | "table" for the trend chart (optional, defaults to "line").
  title: shown in the toolbar (optional, defaults to "Dashboard").

  After calling any of these functions, only describe what the visualization shows in natural language. Do NOT output HTML, CSS, SVG, or JavaScript.
"""

import html
import json
import time
from typing import Any, Dict, List, Literal, Optional

from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

_BUILD = "0.4.0"

ChartType = Literal["line", "bar", "pie", "table"]
DashChartType = Literal["line", "bar", "pie", "table"]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _json_for_script(value: Any) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _coerce_list(value: Any) -> Any:
    """Coerce input to list — handles JSON strings, HTML entities, outer quotes."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        s = html.unescape(value.strip())
        if (s.startswith('"') and s.endswith('"')) or (
            s.startswith("'") and s.endswith("'")
        ):
            s = s[1:-1].strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
    return value


def _coerce_dict(value: Any) -> Any:
    """Coerce input to dict — handles JSON strings, HTML entities, outer quotes."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        s = html.unescape(value.strip())
        if (s.startswith('"') and s.endswith('"')) or (
            s.startswith("'") and s.endswith("'")
        ):
            s = s[1:-1].strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass
    return value


def _coerce_str_list(value: Any) -> List[str]:
    v = _coerce_list(value)
    if isinstance(v, list):
        return [str(x) for x in v]
    return []


# ---------------------------------------------------------------------------
# CSS — v3-compatible theme variables (light default, dark via prefers-color-scheme)
# ---------------------------------------------------------------------------

_THEME_CSS = """
:root {
  --color-text-primary: #1F2937;
  --color-text-secondary: #6B7280;
  --color-text-tertiary: #9CA3AF;
  --color-text-success: #059669;
  --color-text-danger: #DC2626;
  --color-text-info: #2563EB;
  --color-bg-primary: #FFFFFF;
  --color-bg-secondary: #F9FAFB;
  --color-bg-tertiary: #F3F4F6;
  --color-border-tertiary: rgba(0,0,0,0.15);
  --color-border-secondary: rgba(0,0,0,0.3);
  --font-sans: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', Menlo, Consolas, monospace;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --accent: #0F6E56;
  --accent-foreground: #ffffff;
  --text: var(--color-text-primary);
  --muted: var(--color-text-secondary);
  --bg: var(--color-bg-primary);
  --surface: var(--color-bg-secondary);
  --surface-2: var(--color-bg-tertiary);
  --border: var(--color-border-tertiary);
  --border-strong: var(--color-border-secondary);
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-text-primary: #E5E7EB;
    --color-text-secondary: #9CA3AF;
    --color-text-tertiary: #6B7280;
    --color-text-success: #34D399;
    --color-text-danger: #F87171;
    --color-text-info: #60A5FA;
    --color-bg-primary: #1A1A1A;
    --color-bg-secondary: #262626;
    --color-bg-tertiary: #111111;
    --color-border-tertiary: rgba(255,255,255,0.15);
    --color-border-secondary: rgba(255,255,255,0.3);
    --accent: #5DCAA5;
    --accent-foreground: #1A1A1A;
  }
}
"""

# ---------------------------------------------------------------------------
# HTML page chrome (shared layout: topbar + stage + stats)
# ---------------------------------------------------------------------------

_LAYOUT_CSS = """
* { box-sizing: border-box; margin: 0; }
html, body {
  font-family: var(--font-sans);
  background: transparent;
  color: var(--color-text-primary);
  overflow: visible;
  min-height: 200px;
}
body { padding: 4px; }
.wrap { padding: 0; }
.shell {
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-lg);
  background: var(--color-bg-primary);
  overflow: hidden;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 6px 10px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
  background: var(--color-bg-secondary);
}
.title {
  min-width: 0;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--color-text-primary);
}
.controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
button, select {
  height: 26px;
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-md);
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font: 500 12px var(--font-sans);
  padding: 0 9px;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
button:hover, select:hover { border-color: var(--color-border-secondary); }
button:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 1px; }
select { max-width: 118px; }
#stage { padding: 0; }
#stage canvas { display: block; }
.stats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 4px 10px;
  border-top: 0.5px solid var(--color-border-tertiary);
  color: var(--color-text-secondary);
  font: 11px var(--font-mono);
  background: var(--color-bg-secondary);
}
.stat strong { color: var(--color-text-primary); font-weight: 500; }
.toast {
  position: fixed;
  top: 10px;
  right: 10px;
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-md);
  padding: 7px 12px;
  font-size: 12px;
  font-family: var(--font-sans);
  opacity: 0;
  transform: translateY(-4px);
  transition: 0.18s ease;
  pointer-events: none;
  z-index: 10;
}
.toast.show { opacity: 1; transform: translateY(0); }

/* --- Error state --- */
.error-card {
  padding: 20px 16px;
  text-align: center;
}
.error-card .error-icon {
  width: 40px;
  height: 40px;
  margin: 0 auto 12px;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: var(--color-text-danger);
}
.error-card .error-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}
.error-card .error-msg {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 12px;
  line-height: 1.5;
}
.error-card .error-expected {
  display: inline-block;
  text-align: left;
  background: var(--color-bg-tertiary);
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
  white-space: pre;
  line-height: 1.6;
}

/* --- data_detail --- */
.data-detail { padding: 10px 14px; }
.data-detail h3 {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 10px 0 4px;
}
.data-detail h3:first-child { margin-top: 0; }
.data-detail pre {
  background: var(--color-bg-tertiary);
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-md);
  padding: 8px 10px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  max-height: 200px;
  overflow-y: auto;
}
.data-detail .explanation {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}
.fold { margin-bottom: 6px; }
.fold summary {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  cursor: pointer;
  padding: 2px 0;
  user-select: none;
  list-style: none;
}
.fold summary::-webkit-details-marker { display: none; }
.fold summary::before { content: '\\25B6'; display: inline-block; margin-right: 5px; font-size: 9px; transition: transform 0.15s; }
.fold[open] summary::before { content: '\\25BC'; }
.fold summary:hover { color: var(--accent); }
.fold pre, .fold .explanation { margin-top: 4px; }
.data-detail table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-detail th {
  text-align: left;
  font-weight: 600;
  color: var(--color-text-primary);
  padding: 5px 10px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
  background: var(--color-bg-secondary);
  font-size: 12px;
}
.data-detail td {
  padding: 4px 10px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
  color: var(--color-text-primary);
  font-size: 12px;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* --- Dashboard --- */
.dashboard { padding: 10px 14px; }
.metrics-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.metric-card {
  background: var(--color-bg-secondary);
  border: 0.5px solid var(--color-border-tertiary);
  border-radius: var(--radius-lg);
  padding: 10px 14px;
}
.metric-card .metric-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-bottom: 2px;
}
.metric-card .metric-value {
  font-size: 22px;
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 2px;
}
.metric-card .metric-delta {
  font-size: 12px;
}
.metric-delta.positive { color: var(--color-text-success); }
.metric-delta.negative { color: var(--color-text-danger); }
.chart-area {
  position: relative;
  height: 260px;
}

/* --- Table template --- */
.data-table-wrap { padding: 10px 14px; }
.data-table-wrap table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.data-table-wrap th {
  text-align: left;
  font-weight: 600;
  color: var(--color-text-primary);
  padding: 5px 10px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
  background: var(--color-bg-secondary);
  font-size: 12px;
}
.data-table-wrap td {
  padding: 4px 10px;
  border-bottom: 0.5px solid var(--color-border-tertiary);
  color: var(--color-text-primary);
  font-size: 12px;
}
.data-table-wrap tr:hover td { background: var(--color-bg-tertiary); }

/* --- Pagination --- */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
  font-size: 12px;
  color: var(--color-text-secondary);
}
.pagination-info { white-space: nowrap; }
.pagination-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}
.pagination-controls .page-btn {
  height: 24px;
  min-width: 24px;
  padding: 0 6px;
  font-size: 11px;
}
.pagination-controls .page-btn:disabled {
  opacity: 0.4;
  cursor: default;
  pointer-events: none;
}
.pagination-controls .page-size-select {
  height: 24px;
  font-size: 11px;
  max-width: 82px;
}
.pagination-controls .page-info {
  font-size: 11px;
  white-space: nowrap;
  padding: 0 3px;
  color: var(--color-text-tertiary);
}

/* --- responsive --- */
@media (max-width: 520px) {
  .topbar { align-items: flex-start; flex-direction: column; }
  .controls { justify-content: flex-start; }
  button, select { height: 28px; }
  .metrics-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
"""


# ---------------------------------------------------------------------------
# HTML + JS page builder
# ---------------------------------------------------------------------------


def _build_html(
    *,
    title: str,
    template: str,
    data: Dict[str, Any],
    chart_type: str,
    show_stats: bool,
) -> str:
    safe_title = html.escape(title or "Visualization")
    payload = {
        "title": title or "Visualization",
        "template": template,
        "data": data,
        "options": {
            "chartType": chart_type,
            "showStats": show_stats,
        },
        "build": _BUILD,
    }
    payload_json = _json_for_script(payload)

    return f"""<!DOCTYPE html>
<html data-ivt-build="{_BUILD}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'unsafe-inline'; img-src data: blob:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{safe_title}</title>
<style>
{_THEME_CSS}
{_LAYOUT_CSS}
</style>
</head>
<body>
<div class="wrap">
  <div class="shell">
    <div class="topbar">
      <div class="title" id="title">{safe_title}</div>
      <div class="controls">
        <select id="chartSwitch" title="Switch chart type">
          <option value="line">Line</option>
          <option value="bar">Bar</option>
          <option value="pie">Pie</option>
          <option value="table">Table</option>
        </select>
        <button id="pngBtn" title="Export PNG">PNG</button>
        <button id="csvBtn" title="Export CSV" style="display:none">CSV</button>
      </div>
    </div>
    <div id="stage"></div>
    <div class="stats" id="stats"></div>
  </div>
</div>
<div class="toast" id="toast"></div>
<script id="payload" type="application/json">{payload_json}</script>
<script id="serverStats" type="application/json">__SERVER_STATS__</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>
(function() {{
  'use strict';

  var payload = JSON.parse(document.getElementById('payload').textContent);
  var serverStats = JSON.parse(document.getElementById('serverStats').textContent);
  var stage = document.getElementById('stage');
  var stats = document.getElementById('stats');
  var chartSwitch = document.getElementById('chartSwitch');

  var COLORS = ['#1D9E75','#7F77DD','#D85A30','#378ADD','#BA7517','#639922','#D4537E','#888780'];
  var currentChart = null;
  var pageStore = {{}};

  // -------------------------------------------------------------------
  // Pagination helpers
  // -------------------------------------------------------------------

  function paginationHTML(key, page, pageSize, totalRows) {{
    var totalPages = Math.ceil(totalRows / pageSize) || 1;
    if (page > totalPages) page = totalPages;
    if (page < 1) page = 1;
    var start = (page - 1) * pageSize + 1;
    var end = Math.min(page * pageSize, totalRows);
    var h = '<div class="pagination">';
    h += '<div class="pagination-info">Showing ' + start.toLocaleString() + '\u2013' + end.toLocaleString() + ' of ' + totalRows.toLocaleString() + ' rows</div>';
    h += '<div class="pagination-controls">';
    h += '<select class="page-size-select" data-key="' + key + '">';
    [10, 20, 50, 100].forEach(function(s) {{
      h += '<option value="' + s + '"' + (s === pageSize ? ' selected' : '') + '>' + s + ' / page</option>';
    }});
    h += '</select>';
    h += '<button class="page-btn" data-key="' + key + '" data-action="first"' + (page <= 1 ? ' disabled' : '') + '>First</button>';
    h += '<button class="page-btn" data-key="' + key + '" data-action="prev"' + (page <= 1 ? ' disabled' : '') + '>Prev</button>';
    h += '<span class="page-info">Page ' + page + ' of ' + totalPages + '</span>';
    h += '<button class="page-btn" data-key="' + key + '" data-action="next"' + (page >= totalPages ? ' disabled' : '') + '>Next</button>';
    h += '<button class="page-btn" data-key="' + key + '" data-action="last"' + (page >= totalPages ? ' disabled' : '') + '>Last</button>';
    h += '</div></div>';
    return h;
  }}

  function storePageData(key, columns, rows, pageSize) {{
    pageStore[key] = {{columns: columns, rows: rows, page: 1, pageSize: pageSize}};
  }}

  function refreshTableBody(key) {{
    var st = pageStore[key];
    if (!st) return;
    var totalPages = Math.ceil(st.rows.length / st.pageSize) || 1;
    if (st.page > totalPages) st.page = totalPages;
    if (st.page < 1) st.page = 1;
    var start = (st.page - 1) * st.pageSize;
    var end = Math.min(start + st.pageSize, st.rows.length);
    var visibleRows = st.rows.slice(start, end);

    var tbody = document.getElementById(key + '-body');
    if (tbody) {{
      var h = '';
      visibleRows.forEach(function(row) {{
        h += '<tr>';
        st.columns.forEach(function(c) {{
          var val = typeof row === 'object' ? (row[c] != null ? row[c] : '') : row;
          var maxLen = key === 'dd' ? 32 : 40;
          h += '<td>' + esc(shortLabel(String(val), maxLen)) + '</td>';
        }});
        h += '</tr>';
      }});
      tbody.innerHTML = h;
    }}

    var pagEl = document.getElementById(key + '-pag');
    if (pagEl) {{
      pagEl.innerHTML = paginationHTML(key, st.page, st.pageSize, st.rows.length);
    }}
    reportHeight();
  }}

  function changePage(key, action) {{
    var st = pageStore[key];
    if (!st) return;
    var totalPages = Math.ceil(st.rows.length / st.pageSize) || 1;
    if (action === 'first') st.page = 1;
    else if (action === 'prev') st.page = Math.max(1, st.page - 1);
    else if (action === 'next') st.page = Math.min(totalPages, st.page + 1);
    else if (action === 'last') st.page = totalPages;
    refreshTableBody(key);
  }}

  function changePageSize(key, newSize) {{
    var st = pageStore[key];
    if (!st) return;
    st.pageSize = parseInt(newSize, 10) || 20;
    st.page = 1;
    refreshTableBody(key);
  }}

  function getCssVar(name) {{
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }}

  // -------------------------------------------------------------------
  // Schema validators — return {{valid, error, expected}}
  // -------------------------------------------------------------------

  function validateDataDetail(data) {{
    if (!data || typeof data !== 'object') {{
      return {{valid:false, error:'Data must be an object.',
        expected:'{{\\n  "columns": ["col1","col2"],\\n  "rows": [{{"col1":"...","col2":"..."}}]\\n}}'}};
    }}
    var rows = data.rows;
    if (!Array.isArray(rows) || rows.length === 0) {{
      return {{valid:false, error:'"rows" is required and must be a non-empty array.',
        expected:'"rows": [{{"col1": "value", "col2": 123}}, ...]'}};
    }}
    var columns = data.columns;
    if (!Array.isArray(columns) || columns.length === 0) {{
      return {{valid:false, error:'"columns" is required and must be a non-empty array of strings.',
        expected:'"columns": ["col1", "col2"]'}};
    }}
    return {{valid:true}};
  }}

  function validateChart(data) {{
    if (!data || typeof data !== 'object') {{
      return {{valid:false, error:'Data must be an object.',
        expected:'{{\\n  "series": [\\n    {{"label": "Jan", "value": 120}},\\n    {{"label": "Feb", "value": 148}}\\n  ]\\n}}'}};
    }}
    var series = data.series;
    if (!Array.isArray(series) || series.length === 0) {{
      return {{valid:false, error:'"series" is required and must be a non-empty array.',
        expected:'"series": [{{"label": "Jan", "value": 120}}, {{"label": "Feb", "value": 148}}]'}};
    }}
    var yCols = data.y_columns || ['value'];
    var xCol = data.x_column || 'label';
    for (var i = 0; i < series.length; i++) {{
      var item = series[i];
      if (typeof item !== 'object' || item[xCol] === undefined) {{
        return {{valid:false, error:'Each series item must have "' + xCol + '" (x-axis label).',
          expected:'{{"' + xCol + '": "Jan", ' + yCols.join(': 0, ') + ': 0}}'}};
      }}
      for (var j = 0; j < yCols.length; j++) {{
        if (item[yCols[j]] === undefined) {{
          return {{valid:false, error:'series[' + i + '] missing column "' + yCols[j] + '".',
            expected:'{{"label": "Jan", ' + yCols.join(': 0, ') + ': 0}}'}};
        }}
      }}
    }}
    return {{valid:true}};
  }}

  function validateTable(data) {{
    if (!data || typeof data !== 'object') {{
      return {{valid:false, error:'Data must be an object.',
        expected:'{{\\n  "columns": ["Region","Revenue"],\\n  "rows": [{{"Region":"North","Revenue":"$1.2M"}}]\\n}}'}};
    }}
    var rows = data.rows;
    if (!Array.isArray(rows) || rows.length === 0) {{
      return {{valid:false, error:'"rows" is required and must be a non-empty array.',
        expected:'"rows": [{{"Region": "North", "Revenue": "$1.2M"}}, ...]'}};
    }}
    return {{valid:true}};
  }}

  function validateDashboard(data) {{
    if (!data || typeof data !== 'object') {{
      return {{valid:false, error:'Data must be an object.',
        expected:'{{\\n  "metrics": [{{"label":"Revenue","value":"$3.87M","delta":"+12.4%"}}],\\n  "chartTitle": "Trend",\\n  "series": [{{"label":"Jan","value":120}}]\\n}}'}};
    }}
    var metrics = data.metrics;
    if (!Array.isArray(metrics) || metrics.length === 0) {{
      return {{valid:false, error:'"metrics" is required and must be a non-empty array.',
        expected:'"metrics": [{{"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"}}]'}};
    }}
    for (var i = 0; i < metrics.length; i++) {{
      var m = metrics[i];
      if (typeof m !== 'object' || m.label === undefined || m.value === undefined) {{
        return {{valid:false, error:'Each metric must have "label" (string) and "value" (string or number).',
          expected:'{{"label": "Revenue", "value": "$3.87M"}}'}};
      }}
    }}
    return {{valid:true}};
  }}

  // -------------------------------------------------------------------
  // Error state
  // -------------------------------------------------------------------

  function renderError(title, message, expected) {{
    var html = '<div class="error-card">';
    html += '<div class="error-icon">!</div>';
    html += '<div class="error-title">' + esc(title) + '</div>';
    html += '<div class="error-msg">' + esc(message) + '</div>';
    html += '<div class="error-expected">' + esc(expected) + '</div>';
    html += '</div>';
    stage.innerHTML = html;
  }}

  // -------------------------------------------------------------------
  // Helpers
  // -------------------------------------------------------------------

  function esc(s) {{
    return String(s == null ? '' : s).replace(/[&<>"]/g, function(c) {{
      return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c];
    }});
  }}

  function num(v) {{
    var n = Number(v);
    return isFinite(n) ? n : 0;
  }}

  function shortLabel(s, maxLen) {{
    s = String(s || '');
    maxLen = maxLen || 14;
    return s.length > maxLen ? s.slice(0, maxLen - 1) + '\u2026' : s;
  }}

  function deltaClass(s) {{
    s = String(s || '');
    if (s.charAt(0) === '+' || s.indexOf('up') === 0 || s.indexOf('incr') === 0) return 'positive';
    if (s.charAt(0) === '-' || s.indexOf('down') === 0 || s.indexOf('decr') === 0) return 'negative';
    return '';
  }}

  // -------------------------------------------------------------------
  // Render: data_detail
  // -------------------------------------------------------------------

  function renderDataDetail(data) {{
    var v = validateDataDetail(data);
    if (!v.valid) {{ renderError('Invalid data for data_detail', v.error, v.expected); return; }}
    var columns = data.columns;
    var rows = data.rows;
    var sql = data.sql || '';
    var explanation = data.explanation || '';
    var pageSize = 10;
    storePageData('dd', columns, rows, pageSize);
    var end = Math.min(pageSize, rows.length);
    var html = '<div class="data-detail">';
    if (sql) {{
      html += '<details class="fold"><summary>SQL</summary><pre>' + esc(sql) + '</pre></details>';
    }}
    if (explanation) {{
      html += '<details class="fold"><summary>Explanation</summary><div class="explanation">' + esc(explanation) + '</div></details>';
    }}
    html += '<h3>Data table</h3>';
    html += '<table><thead><tr>';
    columns.forEach(function(c) {{ html += '<th>' + esc(shortLabel(c, 18)) + '</th>'; }});
    html += '</tr></thead><tbody id="dd-body">';
    rows.slice(0, end).forEach(function(row) {{
      html += '<tr>';
      columns.forEach(function(c) {{
        var val = typeof row === 'object' ? (row[c] != null ? row[c] : '') : row;
        html += '<td>' + esc(shortLabel(String(val), 32)) + '</td>';
      }});
      html += '</tr>';
    }});
    html += '</tbody></table>';
    html += '<div id="dd-pag">' + paginationHTML('dd', 1, pageSize, rows.length) + '</div>';
    html += '</div>';
    stage.innerHTML = html;
  }}

  // -------------------------------------------------------------------
  // Render: chart (line / bar / pie via Chart.js)
  // -------------------------------------------------------------------

  function renderChart(chartType, data) {{
    if (chartType === 'table') {{
      if (!data.rows && data.series) {{
        var yc = data.y_columns || ['value'];
        // Use x_column from Python data, or auto-detect as fallback
        var xCol = data.x_column || 'label';
        if (!data.x_column && data.series.length > 0) {{
          var keys = Object.keys(data.series[0]);
          for (var k = 0; k < keys.length; k++) {{
            if (yc.indexOf(keys[k]) === -1) {{ xCol = keys[k]; break; }}
          }}
        }}
        data = {{rows: data.series, columns: [xCol].concat(yc)}};
      }}
      renderTable(data); return;
    }}
    var v = validateChart(data);
    if (!v.valid) {{ renderError('Invalid data for chart', v.error, v.expected); return; }}
    var series = data.series;
    var yCols = data.y_columns || ['value'];
    var isMulti = yCols.length > 1;
    var xCol = data.x_column || 'label';
    var labels = series.map(function(d) {{ return String(d[xCol]); }});

    // Build datasets — one per y_column
    var datasets = yCols.map(function(col, i) {{
      var color = COLORS[i % COLORS.length];
      var ds = {{
        label: isMulti ? col : undefined,
        data: series.map(function(d) {{ return num(d[col]); }}),
        borderColor: color,
        backgroundColor: chartType === 'bar' ? color : color + '20',
        fill: chartType === 'line',
        tension: 0.3,
        pointRadius: chartType === 'line' ? 4 : undefined,
        pointBackgroundColor: chartType === 'line' ? color : undefined,
        pointBorderColor: chartType === 'line' ? getCssVar('--color-bg-primary') : undefined,
        pointBorderWidth: chartType === 'line' ? 2 : undefined,
        pointHoverRadius: chartType === 'line' ? 6 : undefined,
        borderRadius: chartType === 'bar' ? 4 : undefined,
        borderSkipped: chartType === 'bar' ? false : undefined,
        borderWidth: chartType === 'pie' ? 2 : undefined,
        hoverBorderWidth: chartType === 'pie' ? 3 : undefined
      }};
      return ds;
    }});

    var extraH = (isMulti && chartType !== 'pie') ? 24 : 0;
    var h = chartType === 'pie'
      ? Math.min(440, Math.max(260, 200 + series.length * 14))
      : Math.min(420, Math.max(240, 200 + series.length * 16 + extraH));
    stage.innerHTML = '<div style="position:relative; height:' + h + 'px;"><canvas id="chartCanvas"></canvas></div>';
    var ctx = document.getElementById('chartCanvas').getContext('2d');
    var textColor = getCssVar('--color-text-secondary');
    var gridColor = getCssVar('--color-border-tertiary');
    var bgColor = getCssVar('--color-bg-primary');

    if (chartType === 'pie') {{
      // Pie only uses first y_column (single ring)
      currentChart = new Chart(ctx, {{
        type: 'doughnut',
        data: {{
          labels: labels,
          datasets: [{{
            data: series.map(function(d) {{ return num(d[yCols[0]]); }}),
            backgroundColor: COLORS,
            borderColor: bgColor,
            borderWidth: 2,
            hoverBorderWidth: 3
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          cutout: '60%',
          plugins: {{
            legend: {{
              position: 'right',
              labels: {{ color: textColor, font: {{size:12}}, padding: 16, usePointStyle: true }}
            }},
            tooltip: {{ backgroundColor: getCssVar('--color-bg-secondary'), titleColor: textColor, bodyColor: textColor, borderColor: gridColor, borderWidth: 0.5 }}
          }}
        }}
      }});
    }} else if (chartType === 'bar') {{
      currentChart = new Chart(ctx, {{
        type: 'bar',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: isMulti, position: 'top', labels: {{ color: textColor, font: {{size:11}}, usePointStyle: true, padding: 12 }} }},
            tooltip: {{ backgroundColor: getCssVar('--color-bg-secondary'), titleColor: textColor, bodyColor: textColor, borderColor: gridColor, borderWidth: 0.5 }}
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{size:11}} }}, border: {{ color: gridColor }} }},
            y: {{ grid: {{ color: gridColor }}, ticks: {{ color: textColor, font: {{size:11}} }}, border: {{ display: false }} }}
          }}
        }}
      }});
    }} else {{
      currentChart = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          interaction: {{ intersect: false, mode: 'index' }},
          plugins: {{
            legend: {{ display: isMulti, position: 'top', labels: {{ color: textColor, font: {{size:11}}, usePointStyle: true, padding: 12 }} }},
            tooltip: {{ backgroundColor: getCssVar('--color-bg-secondary'), titleColor: textColor, bodyColor: textColor, borderColor: gridColor, borderWidth: 0.5 }}
          }},
          scales: {{
            x: {{ grid: {{ display: false }}, ticks: {{ color: textColor, font: {{size:11}}, maxRotation: 45 }}, border: {{ color: gridColor }} }},
            y: {{ grid: {{ color: gridColor }}, ticks: {{ color: textColor, font: {{size:11}} }}, border: {{ display: false }} }}
          }}
        }}
      }});
    }}
  }}

  // -------------------------------------------------------------------
  // Render: table (HTML table)
  // -------------------------------------------------------------------

  function renderTable(data) {{
    var v = validateTable(data);
    if (!v.valid) {{ renderError('Invalid data for table', v.error, v.expected); return; }}
    var rows = data.rows;
    var columns = data.columns;
    var first = rows[0] || {{}};
    if (!Array.isArray(columns) || !columns.length) {{
      columns = typeof first === 'object' && !Array.isArray(first) ? Object.keys(first) : ['label', 'value'];
    }}
    var pageSize = 10;
    storePageData('ct', columns, rows, pageSize);
    var end = Math.min(pageSize, rows.length);
    var html = '<div class="data-table-wrap"><table><thead><tr>';
    columns.forEach(function(c) {{ html += '<th>' + esc(shortLabel(c, 18)) + '</th>'; }});
    html += '</tr></thead><tbody id="ct-body">';
    rows.slice(0, end).forEach(function(row) {{
      html += '<tr>';
      columns.forEach(function(c) {{
        var val = typeof row === 'object' ? (row[c] != null ? row[c] : '') : row;
        html += '<td>' + esc(shortLabel(String(val), 40)) + '</td>';
      }});
      html += '</tr>';
    }});
    html += '</tbody></table>';
    html += '<div id="ct-pag">' + paginationHTML('ct', 1, pageSize, rows.length) + '</div>';
    html += '</div>';
    stage.innerHTML = html;
  }}

  function renderDashboardTable(series) {{
    var columns = ['label', 'value'];
    var rows = series.map(function(row) {{
      return {{
        label: row && row.label != null ? row.label : '',
        value: row && row.value != null ? row.value : ''
      }};
    }});
    var pageSize = 10;
    storePageData('dash', columns, rows, pageSize);
    var end = Math.min(pageSize, rows.length);
    var html = '<div class="data-table-wrap"><table><thead><tr>';
    columns.forEach(function(c) {{ html += '<th>' + esc(shortLabel(c, 18)) + '</th>'; }});
    html += '</tr></thead><tbody id="dash-body">';
    rows.slice(0, end).forEach(function(row) {{
      html += '<tr>';
      columns.forEach(function(c) {{
        html += '<td>' + esc(shortLabel(String(row[c]), 40)) + '</td>';
      }});
      html += '</tr>';
    }});
    html += '</tbody></table>';
    html += '<div id="dash-pag">' + paginationHTML('dash', 1, pageSize, rows.length) + '</div>';
    html += '</div>';
    return html;
  }}

  // -------------------------------------------------------------------
  // Render: dashboard
  // -------------------------------------------------------------------

  function renderDashboard(data, chartType) {{
    var v = validateDashboard(data);
    if (!v.valid) {{ renderError('Invalid data for dashboard', v.error, v.expected); return; }}
    var metrics = data.metrics;
    var chartTitle = data.chartTitle || 'Trend';
    var series = data.series;

    var html = '<div class="dashboard">';
    html += '<div class="metrics-strip">';
    metrics.forEach(function(m) {{
      html += '<div class="metric-card">';
      html += '<div class="metric-label">' + esc(m.label) + '</div>';
      html += '<div class="metric-value">' + esc(m.value) + '</div>';
      if (m.delta) {{
        html += '<div class="metric-delta ' + deltaClass(m.delta) + '">' + esc(m.delta) + '</div>';
      }}
      html += '</div>';
    }});
    html += '</div>';

    if (series && Array.isArray(series) && series.length > 0) {{
      if (chartType === 'table') {{
        html += renderDashboardTable(series);
      }} else {{
        var dashH = chartType === 'pie'
          ? Math.min(380, Math.max(220, 180 + series.length * 12))
          : Math.min(360, Math.max(200, 180 + series.length * 14));
        html += '<div style="position:relative; height:' + dashH + 'px;"><canvas id="dashCanvas"></canvas></div>';
      }}
    }}
    html += '</div>';
    stage.innerHTML = html;

    if (series && Array.isArray(series) && series.length > 0) {{
      if (chartType === 'table') return;
      var labels = series.map(function(d) {{ return String(d.label); }});
      var values = series.map(function(d) {{ return num(d.value); }});
      var ctx = document.getElementById('dashCanvas').getContext('2d');
      var textColor = getCssVar('--color-text-secondary');
      var gridColor = getCssVar('--color-border-tertiary');
      var bgColor = getCssVar('--color-bg-primary');

      if (chartType === 'pie') {{
        currentChart = new Chart(ctx, {{
          type: 'doughnut',
          data: {{ labels: labels, datasets: [{{ data: values, backgroundColor: COLORS, borderColor: bgColor, borderWidth: 2 }}] }},
          options: {{
            responsive: true, maintainAspectRatio: false, cutout: '60%',
            plugins: {{ legend: {{ position: 'bottom', labels: {{ color: textColor, font: {{size:11}}, usePointStyle: true }} }} }}
          }}
        }});
      }} else if (chartType === 'bar') {{
        currentChart = new Chart(ctx, {{
          type: 'bar',
          data: {{ labels: labels, datasets: [{{ data: values, backgroundColor: series.map(function(_,i){{return COLORS[i%COLORS.length];}}), borderRadius: 4, borderSkipped: false }}] }},
          options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{ x: {{ grid: {{display:false}}, ticks: {{color:textColor,font:{{size:11}}}}, border: {{color:gridColor}} }}, y: {{ grid: {{color:gridColor}}, ticks: {{color:textColor,font:{{size:11}}}}, border: {{display:false}} }} }}
          }}
        }});
      }} else {{
        currentChart = new Chart(ctx, {{
          type: 'line',
          data: {{ labels: labels, datasets: [{{ data: values, borderColor: COLORS[0], backgroundColor: COLORS[0]+'20', fill: true, tension: 0.3, pointRadius: 3, pointBackgroundColor: COLORS[0] }}] }},
          options: {{
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{ x: {{ grid: {{display:false}}, ticks: {{color:textColor,font:{{size:11}},maxRotation:45}}, border: {{color:gridColor}} }}, y: {{ grid: {{color:gridColor}}, ticks: {{color:textColor,font:{{size:11}}}}, border: {{display:false}} }} }}
          }}
        }});
      }}
    }}
  }}

  // -------------------------------------------------------------------
  // Main render dispatch
  // -------------------------------------------------------------------

  function render() {{
    var t0 = performance.now();
    var tpl = payload.template;
    var chartType = chartSwitch.value;

    if (currentChart) {{ currentChart.destroy(); currentChart = null; }}

    if (tpl === 'data_detail') {{
      renderDataDetail(payload.data);
    }} else if (tpl === 'dashboard') {{
      renderDashboard(payload.data, chartType);
    }} else {{
      renderChart(chartType, payload.data);
    }}

    var renderMs = (performance.now() - t0).toFixed(1);
    var showStats = payload.options.showStats !== false;
    if (showStats) {{
      var jsonChars = (serverStats && serverStats.jsonLength) ? serverStats.jsonLength.toLocaleString() : '?';
      var htmlChars = (serverStats && serverStats.htmlLength) ? serverStats.htmlLength.toLocaleString() : '?';
      var serverMs = (serverStats && serverStats.buildMs != null) ? serverStats.buildMs.toFixed(1) : '?';
      stats.innerHTML =
        '<span class="stat">template <strong>' + esc(tpl) + '</strong></span>' +
        '<span class="stat">chart <strong>' + esc(chartType) + '</strong></span>' +
        '<span class="stat">json <strong>' + jsonChars + '</strong> chars</span>' +
        '<span class="stat">html <strong>' + htmlChars + '</strong> chars</span>' +
        '<span class="stat">server <strong>' + serverMs + '</strong> ms</span>' +
        '<span class="stat">client <strong>' + renderMs + '</strong> ms</span>';
    }} else {{
      stats.innerHTML = '';
    }}
    reportHeight();
  }}

  // -------------------------------------------------------------------
  // Export & utilities
  // -------------------------------------------------------------------

  function reportHeight() {{
    var h = Math.ceil(document.documentElement.scrollHeight);
    try {{ parent.postMessage({{type:'resize', height:h}}, '*'); }} catch(e) {{}}
  }}

  function toast(msg) {{
    var el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(toast._t);
    toast._t = setTimeout(function() {{ el.classList.remove('show'); }}, 1600);
  }}

  function exportPng() {{
    var canvas = document.querySelector('#stage canvas');
    if (!canvas) {{
      toast('No chart to export');
      return;
    }}
    canvas.toBlob(function(blob) {{
      if (!blob) {{ toast('PNG export failed'); return; }}
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url;
      a.download = (payload.title || 'visualization').replace(/[<>:"\\\\/|?*]+/g, '-') + '.png';
      a.click();
      setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1200);
      toast('PNG exported');
    }}, 'image/png');
  }}

  function exportCsv() {{
    var data = payload.data;
    var columns = data.columns;
    var rows = data.rows;
    if (!columns || !rows) {{
      toast('No data to export');
      return;
    }}
    function csvEscape(v) {{
      var s = String(v == null ? '' : v);
      if (/[",\\n\\r]/.test(s)) {{
        return '"' + s.replace(/"/g, '""') + '"';
      }}
      return s;
    }}
    var lines = [columns.map(csvEscape).join(',')];
    rows.forEach(function(row) {{
      lines.push(columns.map(function(c) {{ return csvEscape(row[c]); }}).join(','));
    }});
    var bom = '\\uFEFF';
    var blob = new Blob([bom + lines.join('\\n')], {{type: 'text/csv;charset=utf-8'}});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = (payload.title || 'data').replace(/[<>:"\\\\/|?*]+/g, '-') + '.csv';
    a.click();
    setTimeout(function() {{ URL.revokeObjectURL(url); }}, 1200);
    toast('CSV exported');
  }}

  // -------------------------------------------------------------------
  // Init
  // -------------------------------------------------------------------

  chartSwitch.value = (payload.options && payload.options.chartType) || 'line';
  if (payload.template === 'data_detail') {{
    chartSwitch.style.display = 'none';
    document.getElementById('pngBtn').style.display = 'none';
    document.getElementById('csvBtn').style.display = '';
  }}

  document.getElementById('pngBtn').addEventListener('click', exportPng);
  document.getElementById('csvBtn').addEventListener('click', exportCsv);
  chartSwitch.addEventListener('change', render);
  window.addEventListener('resize', reportHeight);

  // Pagination event delegation
  stage.addEventListener('click', function(e) {{
    var btn = e.target.closest('.page-btn');
    if (btn && !btn.disabled) {{
      changePage(btn.dataset.key, btn.dataset.action);
    }}
  }});
  stage.addEventListener('change', function(e) {{
    var sel = e.target.closest('.page-size-select');
    if (sel) {{
      changePageSize(sel.dataset.key, sel.value);
    }}
  }});

  render();
}})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Shared render helper — builds HTML, replaces stats placeholder, returns response
# ---------------------------------------------------------------------------


def _render_response(
    *,
    title: str,
    template: str,
    data: Dict[str, Any],
    chart_type: str,
    show_stats: bool,
    label: str,
) -> tuple:
    """Build HTML, measure timing, replace __SERVER_STATS__, return (HTMLResponse, context)."""
    started = time.perf_counter()

    payload_for_len = {
        "title": title,
        "template": template,
        "data": data,
        "chartType": chart_type,
    }
    json_length = len(_json_for_script(payload_for_len))

    content = _build_html(
        title=title,
        template=template,
        data=data,
        chart_type=chart_type,
        show_stats=show_stats,
    )

    server_stats = {
        "template": template,
        "jsonLength": json_length,
        "htmlLength": 0,
        "buildMs": (time.perf_counter() - started) * 1000,
    }
    for _ in range(3):
        rendered = content.replace(
            "__SERVER_STATS__", _json_for_script(server_stats)
        )
        if server_stats["htmlLength"] == len(rendered):
            content = rendered
            break
        server_stats["htmlLength"] = len(rendered)
    else:
        content = content.replace(
            "__SERVER_STATS__", _json_for_script(server_stats)
        )

    point_count = (
        len(data.get("series", data.get("rows", data.get("metrics", []))))
        if isinstance(data, dict)
        else 0
    )
    context = (
        f'{label} "{title}" rendered with {point_count} entries '
        f"(template={template}, chart_type={chart_type}). "
        f"Do not emit HTML after this tool call. Summarize what the visualization shows."
    )
    return HTMLResponse(content=content, headers={"Content-Disposition": "inline"}), context


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


class Tools:
    """Template visualizer — three self-describing functions with flat parameters."""

    class Valves(BaseModel):
        show_stats: bool = Field(
            default=False,
            description="DEBUG: Show template, payload size, generated HTML size, and render timing inside the visualization.",
        )

    def __init__(self):
        self.valves = self.Valves()

    # ================================================================
    # render_data_detail
    # ================================================================

    async def render_data_detail(
        self,
        columns: Any,
        rows: Any,
        sql: str = "",
        explanation: str = "",
        title: str = "Data Detail",
    ) -> tuple:
        """
        Render a data detail view with optional SQL, explanation, and data table.

        Use this whenever the user asks to see SQL, query explanations, or data
        table previews. Also use it BEFORE render_chart or render_dashboard to
        show the source data and query logic.

        :param columns: List of column name strings, e.g. ["month", "revenue"].
        :param rows: List of row objects, e.g. [{"month": "Jan", "revenue": 120}].
        :param sql: Optional SQL query string to display.
        :param explanation: Optional plain-text explanation of the data.
        :param title: Short title displayed in the toolbar.
        :return: Inline HTML visualization.
        """
        # Coerce and validate columns
        coerced_cols = _coerce_str_list(columns)
        if not coerced_cols:
            return (
                "Error: 'columns' is required and must be a non-empty list of column name strings. "
                'Example: columns=["month", "revenue", "growth"]'
            )

        # Coerce and validate rows
        coerced_rows = _coerce_list(rows)
        if not isinstance(coerced_rows, list) or len(coerced_rows) == 0:
            return (
                "Error: 'rows' is required and must be a non-empty list of objects. "
                'Example: rows=[{"month": "Jan", "revenue": 120}]'
            )
        for i, row in enumerate(coerced_rows):
            if not isinstance(row, dict):
                return (
                    f"Error: rows[{i}] must be an object (dict), "
                    f'got {type(row).__name__}. Example: {{"month": "Jan", "revenue": 120}}'
                )

        data = {
            "columns": coerced_cols,
            "rows": coerced_rows,
            "sql": str(sql).strip() if sql else "",
            "explanation": str(explanation).strip() if explanation else "",
        }

        return _render_response(
            title=title,
            template="data_detail",
            data=data,
            chart_type="line",
            show_stats=self.valves.show_stats,
            label="Data detail",
        )

    # ================================================================
    # render_chart
    # ================================================================

    async def render_chart(
        self,
        series: Any,
        chart_type: ChartType = "line",
        y_columns: Any = None,
        title: str = "Chart",
    ) -> tuple:
        """
        Render a chart: line, bar, pie (doughnut), or table.

        Call this when the user asks for a chart or table visualization of data.
        Use render_data_detail first if the user also wants to see SQL or the
        underlying data table.

        Supports both single-series and multi-series data:

        Single series (backward compatible):
            series=[{"label": "Jan", "value": 120}, {"label": "Feb", "value": 148}]

        Multi-series (multiple metrics on the same chart):
            series=[
                {"label": "Jan", "revenue": 120, "users": 500},
                {"label": "Feb", "revenue": 148, "users": 600}
            ]
            y_columns=["revenue", "users"]

        :param series: List of data objects. Each must have a "label" key plus
            one or more numeric value columns.
        :param chart_type: "line" (default), "bar", "pie" (doughnut), or "table".
        :param y_columns: Optional list of column names to plot on y-axis.
            If omitted, auto-detects: uses ["value"] if present, otherwise all
            numeric columns except "label".
        :param title: Short title displayed in the toolbar.
        :return: Inline HTML visualization with Chart.js rendering.
        """
        # Coerce and validate series
        coerced = _coerce_list(series)
        if not isinstance(coerced, list) or len(coerced) == 0:
            return (
                "Error: 'series' is required and must be a non-empty list. "
                'Example: series=[{"label": "Jan", "value": 120}, {"label": "Feb", "value": 148}]'
            )

        clean: List[Dict[str, Any]] = []
        for i, item in enumerate(coerced):
            item = _coerce_dict(item)
            if not isinstance(item, dict):
                return (
                    f"Error: series[{i}] must be an object. "
                    f'Got {type(item).__name__}. Example: {{"month": "Jan", "revenue": 120}}'
                )
            clean.append(dict(item))

        if not clean:
            return (
                "Error: 'series' is required and must be a non-empty list. "
                'Example: series=[{"month": "Jan", "revenue": 120}]'
            )

        # Resolve y_columns: explicit > "value" key detection > auto-detect numerics
        coerced_y = _coerce_list(y_columns) if y_columns is not None else None
        if coerced_y and isinstance(coerced_y, list) and len(coerced_y) > 0:
            resolved_y = [str(c) for c in coerced_y]
        elif all("value" in item for item in clean):
            # Backward compat: all items have "value" → single series
            resolved_y = ["value"]
        else:
            # Auto-detect: all numeric keys (int/float, not bool)
            first = clean[0]
            resolved_y = [
                k for k in first.keys()
                if isinstance(first[k], (int, float)) and not isinstance(first[k], bool)
            ]
            if not resolved_y:
                return (
                    "Error: no numeric value columns found in series. "
                    "Each item must have at least one numeric field. "
                    f'Got keys: {list(first.keys())}. '
                    'Example: {"month": "Jan", "revenue": 120, "users": 500}'
                )

        # Validate all y_columns exist in all items
        for i, item in enumerate(clean):
            for col in resolved_y:
                if col not in item:
                    return (
                        f"Error: series[{i}] missing column '{col}'. "
                        f"All y_columns must be present in every item. "
                        f"Got keys: {list(item.keys())}"
                    )

        # Detect x column: first key in first item that isn't a y_column
        x_col = "label"  # fallback for empty
        if clean:
            for key in clean[0].keys():
                if key not in resolved_y:
                    x_col = key
                    break

        # Validate x_column exists in all items
        for i, item in enumerate(clean):
            if x_col not in item:
                return (
                    f"Error: series[{i}] missing x-axis column '{x_col}'. "
                    f"Each series item must have the same x-axis key. "
                    f"Got keys: {list(item.keys())}"
                )

        # Normalize: ensure x_column value is string
        for item in clean:
            item[x_col] = str(item[x_col])

        data: Dict[str, Any] = {
            "series": clean,
            "y_columns": resolved_y,
            "x_column": x_col,
        }

        # For table chart_type, auto-detect x-column from keys
        if chart_type == "table":
            data = {
                "rows": clean,
                "columns": [x_col] + resolved_y,
            }

        return _render_response(
            title=title,
            template="chart",
            data=data,
            chart_type=chart_type,
            show_stats=self.valves.show_stats,
            label=f"Chart ({len(resolved_y)} series)",
        )

    # ================================================================
    # render_dashboard
    # ================================================================

    async def render_dashboard(
        self,
        metrics: Any,
        series: Any = None,
        chart_title: str = "",
        chart_type: DashChartType = "line",
        title: str = "Dashboard",
    ) -> tuple:
        """
        Render a dashboard with KPI metric cards and an optional trend chart.

        Use this when the user asks for KPIs, business metrics overview, or
        an executive summary combining numbers with a trend visualization.

        :param metrics: List of {label, value, delta?} objects.
            label=string, value=string|number, delta=optional change string (e.g. "+12.4%").
            Example: [{"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"}]
        :param series: Optional list of {label, value} for a trend chart.
            Example: [{"label": "Jan", "value": 120}, {"label": "Feb", "value": 148}]
        :param chart_title: Label for the trend chart (optional).
        :param chart_type: "line" (default), "bar", "pie", or "table" for the trend chart.
        :param title: Short title displayed in the toolbar.
        :return: Inline HTML visualization with metric cards and Chart.js chart.
        """
        # Coerce and validate metrics
        coerced_metrics = _coerce_list(metrics)
        if not isinstance(coerced_metrics, list) or len(coerced_metrics) == 0:
            return (
                "Error: 'metrics' is required and must be a non-empty list. "
                'Example: metrics=[{"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"}]'
            )

        clean_metrics: List[Dict[str, Any]] = []
        for i, m in enumerate(coerced_metrics):
            m = _coerce_dict(m)
            if not isinstance(m, dict):
                return (
                    f"Error: metrics[{i}] must be an object. "
                    f'Got {type(m).__name__}. Example: {{"label": "Revenue", "value": "$3.87M"}}'
                )
            if "label" not in m or "value" not in m:
                return (
                    f"Error: metrics[{i}] missing required fields. "
                    f'Each metric must have "label" and "value". '
                    f'Got keys: {list(m.keys())}. '
                    f'Example: {{"label": "Revenue", "value": "$3.87M", "delta": "+12.4%"}}'
                )
            clean_metrics.append({
                "label": str(m["label"]),
                "value": m["value"],
                "delta": str(m.get("delta", "")),
            })

        data: Dict[str, Any] = {
            "metrics": clean_metrics,
            "chartTitle": chart_title or "Trend",
        }

        # Coerce and validate optional series
        clean_series: Optional[List[Dict[str, Any]]] = None
        if series is not None:
            coerced_series = _coerce_list(series)
            if isinstance(coerced_series, list) and len(coerced_series) > 0:
                clean_series = []
                for i, item in enumerate(coerced_series):
                    item = _coerce_dict(item)
                    if not isinstance(item, dict):
                        return (
                            f"Error: series[{i}] must be an object. "
                            f'Example: {{"label": "Jan", "value": 120}}'
                        )
                    if "label" not in item or "value" not in item:
                        return (
                            f"Error: series[{i}] must have 'label' and 'value'. "
                            f'Got keys: {list(item.keys())}'
                        )
                    clean_series.append({
                        "label": str(item["label"]),
                        "value": item["value"],
                    })
                data["series"] = clean_series

        metric_count = len(clean_metrics)
        return _render_response(
            title=title,
            template="dashboard",
            data=data,
            chart_type=chart_type,
            show_stats=self.valves.show_stats,
            label=f"Dashboard ({metric_count} metrics)",
        )
