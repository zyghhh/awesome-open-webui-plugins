"""
Minimal MCP Apps test server.

Run with:
  python test_server.py

Exposes a tool "show_chart" with a ui:// resource that renders an
interactive bar chart using the tool result data.
Listens on http://localhost:8765/mcp via streamable HTTP.
"""

import json
import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo MCP Apps Server")


# ---------------------------------------------------------------------------
# Tool with UI resource metadata
# ---------------------------------------------------------------------------

@mcp.tool(
    name="show_chart",
    description="Display data as an interactive bar chart. Returns the data and renders a chart UI.",
    meta={"ui": {"resourceUri": "ui://demo/chart"}},
)
def show_chart(title: str, labels: str, values: str) -> str:
    """
    Show data as an interactive bar chart.

    :param title: Chart title.
    :param labels: Comma-separated category labels (e.g. "Jan,Feb,Mar").
    :param values: Comma-separated numeric values (e.g. "10,25,18").
    """
    data = {
        "title": title,
        "labels": [l.strip() for l in labels.split(",")],
        "values": [float(v.strip()) for v in values.split(",")],
    }
    return json.dumps(data)


@mcp.tool(
    name="greet",
    description="A simple greeting tool with no UI resource.",
)
def greet(name: str) -> str:
    """Greet someone by name. No UI resource — just returns text."""
    return f"Hello, {name}! 👋"


# ---------------------------------------------------------------------------
# UI Resource — the HTML that gets rendered as a Rich UI embed
# ---------------------------------------------------------------------------

CHART_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0e0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    padding: 20px;
  }
  h1 { font-size: 1.6em; margin-bottom: 20px; color: #fff; text-shadow: 0 0 20px rgba(100,100,255,0.5); }
  .chart-container {
    width: 100%;
    max-width: 500px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }
  .bar-row {
    display: flex;
    align-items: center;
    margin: 10px 0;
    gap: 10px;
  }
  .bar-label {
    width: 80px;
    text-align: right;
    font-size: 0.9em;
    color: #bbb;
    flex-shrink: 0;
  }
  .bar-track {
    flex: 1;
    height: 28px;
    background: rgba(255,255,255,0.06);
    border-radius: 8px;
    overflow: hidden;
    position: relative;
  }
  .bar-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 8px;
    font-size: 0.8em;
    font-weight: 600;
    color: #fff;
    min-width: 36px;
  }
  .badge {
    display: inline-block;
    margin-top: 16px;
    padding: 6px 14px;
    border-radius: 20px;
    background: rgba(118, 75, 162, 0.3);
    border: 1px solid rgba(118, 75, 162, 0.5);
    font-size: 0.8em;
    color: #c4b5fd;
  }
  .error {
    color: #f87171;
    background: rgba(248,113,113,0.1);
    padding: 12px;
    border-radius: 8px;
    text-align: center;
  }
</style>
</head>
<body>
  <div class="chart-container">
    <h1 id="chart-title">Loading...</h1>
    <div id="bars"></div>
    <div style="text-align:center">
      <span class="badge">MCP App · Rich UI Embed</span>
    </div>
  </div>

<script>
  // Data injected by the MCP App Bridge tool
  const raw = window.__MCP_TOOL_RESULT__;
  const container = document.getElementById('bars');
  const titleEl = document.getElementById('chart-title');

  try {
    const data = JSON.parse(raw);
    titleEl.textContent = data.title || 'Chart';
    const maxVal = Math.max(...data.values, 1);

    data.labels.forEach((label, i) => {
      const val = data.values[i] || 0;
      const pct = (val / maxVal) * 100;

      const row = document.createElement('div');
      row.className = 'bar-row';
      row.innerHTML =
        '<div class="bar-label">' + label + '</div>' +
        '<div class="bar-track">' +
          '<div class="bar-fill" style="width:0%">' + val + '</div>' +
        '</div>';
      container.appendChild(row);

      // Animate in
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          row.querySelector('.bar-fill').style.width = pct + '%';
        });
      });
    });
  } catch (e) {
    titleEl.textContent = 'MCP App Demo';
    container.innerHTML = '<div class="error">No chart data (tool result: ' +
      (raw || 'none') + ')</div>';
  }
</script>
</body>
</html>
"""


@mcp.resource("ui://demo/chart", name="Chart UI", mime_type="text/html")
def chart_resource() -> str:
    """The interactive chart HTML."""
    return CHART_HTML


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # FastMCP creates a Starlette app; run it with uvicorn
    app = mcp.streamable_http_app()
    print("MCP Apps test server running at http://localhost:8765/mcp")
    uvicorn.run(app, host="0.0.0.0", port=8765)
