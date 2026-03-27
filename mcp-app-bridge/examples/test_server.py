"""
Minimal MCP Apps test server.

Run with:
  python test_server.py

Exposes three tools with ui:// resources:
  - show_chart:     animated bar chart
  - show_dashboard: KPI dashboard with sparklines
  - show_donut:     animated donut chart with breakdown

Listens on http://localhost:8765/mcp via streamable HTTP.
"""

import json
import uvicorn
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo MCP Apps Server")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@mcp.tool(
    name="show_chart",
    description="Display data as an interactive bar chart with animated bars.",
    meta={"ui": {"resourceUri": "ui://demo/chart"}},
)
def show_chart(title: str, labels: str, values: str) -> str:
    """
    Show data as an interactive bar chart.

    :param title: Chart title.
    :param labels: Comma-separated category labels (e.g. "Q1,Q2,Q3,Q4").
    :param values: Comma-separated numeric values (e.g. "45,62,38,71").
    """
    return json.dumps({
        "title": title,
        "labels": [l.strip() for l in labels.split(",")],
        "values": [float(v.strip()) for v in values.split(",")],
    })


@mcp.tool(
    name="show_dashboard",
    description="Display a KPI dashboard with key metrics, trend indicators, and mini sparklines.",
    meta={"ui": {"resourceUri": "ui://demo/dashboard"}},
)
def show_dashboard(names: str, values: str, units: str, trends: str) -> str:
    """
    Show a KPI dashboard with multiple metrics.

    :param names: Comma-separated metric names (e.g. "Revenue,Users,Conversion").
    :param values: Comma-separated numeric values (e.g. "142000,8420,4.8").
    :param units: Comma-separated units (e.g. "$,,%" — use empty for no unit).
    :param trends: Comma-separated trend percentages (e.g. "12.5,-3.2,0.7"). Positive = up, negative = down.
    """
    import re
    n = [x.strip() for x in names.split(",")]
    v = [float(re.sub(r"[^\d.\-]", "", x.strip()) or "0") for x in values.split(",")]
    u = [x.strip() for x in units.split(",")]
    t = [float(re.sub(r"[^\d.\-]", "", x.strip()) or "0") for x in trends.split(",")]
    metrics = []
    for i in range(len(n)):
        metrics.append({
            "name": n[i],
            "value": v[i] if i < len(v) else 0,
            "unit": u[i] if i < len(u) else "",
            "trend": t[i] if i < len(t) else 0,
        })
    return json.dumps(metrics)


@mcp.tool(
    name="show_donut",
    description="Display data as an animated donut/ring chart with category breakdown.",
    meta={"ui": {"resourceUri": "ui://demo/donut"}},
)
def show_donut(title: str, labels: str, values: str) -> str:
    """
    Show data as an animated donut chart.

    :param title: Chart title.
    :param labels: Comma-separated category labels (e.g. "Marketing,Engineering,Sales").
    :param values: Comma-separated numeric values (e.g. "35,45,20").
    """
    return json.dumps({
        "title": title,
        "labels": [l.strip() for l in labels.split(",")],
        "values": [float(v.strip()) for v in values.split(",")],
    })


@mcp.tool(
    name="greet",
    description="A simple greeting tool with no UI resource — just returns text.",
)
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! 👋"


# ---------------------------------------------------------------------------
# UI Resources
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
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
  }
  h1 { font-size: 1.6em; margin-bottom: 20px; color: #fff; text-shadow: 0 0 20px rgba(100,100,255,0.5); }
  .card {
    width: 100%; max-width: 500px;
    background: rgba(255,255,255,0.08); backdrop-filter: blur(12px);
    border-radius: 16px; padding: 24px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }
  .bar-row { display: flex; align-items: center; margin: 10px 0; gap: 10px; }
  .bar-label { width: 80px; text-align: right; font-size: 0.9em; color: #bbb; flex-shrink: 0; }
  .bar-track { flex: 1; height: 28px; background: rgba(255,255,255,0.06); border-radius: 8px; overflow: hidden; }
  .bar-fill {
    height: 100%; border-radius: 8px;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex; align-items: center; justify-content: flex-end;
    padding-right: 8px; font-size: 0.8em; font-weight: 600; color: #fff; min-width: 36px;
  }
  .badge { display: inline-block; margin-top: 16px; padding: 6px 14px; border-radius: 20px;
    background: rgba(118,75,162,0.3); border: 1px solid rgba(118,75,162,0.5);
    font-size: 0.8em; color: #c4b5fd; }
</style>
</head>
<body>
  <div class="card">
    <h1 id="title">Loading...</h1>
    <div id="bars"></div>
    <div style="text-align:center"><span class="badge">MCP App · Bar Chart</span></div>
  </div>
<script>
  const raw = window.__MCP_TOOL_RESULT__;
  try {
    const d = JSON.parse(raw);
    document.getElementById('title').textContent = d.title || 'Chart';
    const mx = Math.max(...d.values, 1);
    d.labels.forEach((l, i) => {
      const v = d.values[i] || 0, pct = (v / mx) * 100;
      const row = document.createElement('div'); row.className = 'bar-row';
      row.innerHTML = '<div class="bar-label">' + l + '</div><div class="bar-track"><div class="bar-fill" style="width:0%">' + v + '</div></div>';
      document.getElementById('bars').appendChild(row);
      requestAnimationFrame(() => requestAnimationFrame(() => row.querySelector('.bar-fill').style.width = pct + '%'));
    });
  } catch(e) { document.getElementById('title').textContent = 'No data'; }
</script>
</body>
</html>
"""

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #0a0a1a, #1a1a3e, #0a0a1a);
    color: #e0e0e0;
    padding: 24px; min-height: 100vh;
  }
  h1 { font-size: 1.4em; color: #fff; margin-bottom: 20px; text-align: center;
    text-shadow: 0 0 30px rgba(100,200,255,0.3); }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; max-width: 700px; margin: 0 auto;
  }
  .kpi {
    background: rgba(255,255,255,0.06); backdrop-filter: blur(12px);
    border-radius: 14px; padding: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    transition: transform 0.3s, box-shadow 0.3s;
    animation: fadeIn 0.6s ease both;
  }
  .kpi:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }
  @keyframes fadeIn { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
  .kpi-name { font-size: 0.8em; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .kpi-value { font-size: 2em; font-weight: 700; color: #fff; }
  .kpi-trend { font-size: 0.85em; margin-top: 6px; }
  .kpi-trend.up { color: #4ade80; }
  .kpi-trend.down { color: #f87171; }
  .sparkline { margin-top: 12px; height: 30px; }
  .sparkline svg { width: 100%; height: 100%; }
  .sparkline path { fill: none; stroke-width: 2; stroke-linecap: round; }
  .badge { display: block; text-align: center; margin-top: 20px; padding: 6px 14px;
    font-size: 0.75em; color: #64748b; }
</style>
</head>
<body>
  <h1>📊 Dashboard</h1>
  <div class="grid" id="grid"></div>
  <div class="badge">MCP App · KPI Dashboard</div>
<script>
  const raw = window.__MCP_TOOL_RESULT__;
  const grid = document.getElementById('grid');
  const colors = ['#667eea','#a78bfa','#f472b6','#38bdf8','#4ade80','#fbbf24'];

  function fmt(v, u) {
    if (u === '$' || u === '€' || u === '£') return u + (v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(1)+'K' : v.toLocaleString());
    if (u === '%') return v + '%';
    return (v >= 1e6 ? (v/1e6).toFixed(1)+'M' : v >= 1e3 ? (v/1e3).toFixed(1)+'K' : v.toLocaleString()) + (u ? ' '+u : '');
  }

  function spark(color) {
    const pts = Array.from({length:12}, () => Math.random());
    const mx = Math.max(...pts), mn = Math.min(...pts);
    const norm = pts.map(p => (p-mn)/(mx-mn||1));
    const d = norm.map((y,i) => (i===0?'M':'L')+(i/(norm.length-1)*100).toFixed(1)+','+(30-y*28).toFixed(1)).join(' ');
    return '<div class="sparkline"><svg viewBox="0 0 100 30" preserveAspectRatio="none"><path d="'+d+'" stroke="'+color+'" opacity="0.6"/></svg></div>';
  }

  try {
    const metrics = typeof raw === 'string' ? JSON.parse(raw) : raw;
    metrics.forEach((m, i) => {
      const c = colors[i % colors.length];
      const card = document.createElement('div');
      card.className = 'kpi'; card.style.animationDelay = (i*0.1)+'s';
      const trend = m.trend || 0;
      const arrow = trend >= 0 ? '↑' : '↓';
      card.innerHTML =
        '<div class="kpi-name">' + (m.name||'Metric') + '</div>' +
        '<div class="kpi-value">' + fmt(m.value||0, m.unit||'') + '</div>' +
        '<div class="kpi-trend ' + (trend>=0?'up':'down') + '">' + arrow + ' ' + Math.abs(trend) + '%</div>' +
        spark(c);
      grid.appendChild(card);
    });
  } catch(e) { grid.innerHTML = '<div style="color:#f87171">Could not parse metrics</div>'; }
</script>
</body>
</html>
"""

DONUT_HTML = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #1a1a3e, #24243e);
    color: #e0e0e0;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 100vh; padding: 20px;
  }
  h1 { font-size: 1.5em; margin-bottom: 20px; color: #fff; text-shadow: 0 0 20px rgba(100,100,255,0.4); }
  .card {
    width: 100%; max-width: 420px;
    background: rgba(255,255,255,0.06); backdrop-filter: blur(12px);
    border-radius: 16px; padding: 28px; text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  }
  .donut-wrap { position: relative; width: 220px; height: 220px; margin: 0 auto 20px; }
  .donut-wrap svg { width: 100%; height: 100%; transform: rotate(-90deg); }
  .donut-wrap circle { fill: none; stroke-width: 20; stroke-linecap: round; }
  .center-label { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
    font-size: 2em; font-weight: 700; color: #fff; }
  .legend { display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; margin-top: 12px; }
  .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.85em; }
  .legend-dot { width: 10px; height: 10px; border-radius: 50%; }
  .badge { display: inline-block; margin-top: 16px; padding: 6px 14px; border-radius: 20px;
    background: rgba(118,75,162,0.3); border: 1px solid rgba(118,75,162,0.5);
    font-size: 0.8em; color: #c4b5fd; }
</style>
</head>
<body>
  <div class="card">
    <h1 id="title">Loading...</h1>
    <div class="donut-wrap">
      <svg viewBox="0 0 120 120" id="donut"></svg>
      <div class="center-label" id="total"></div>
    </div>
    <div class="legend" id="legend"></div>
    <span class="badge">MCP App · Donut Chart</span>
  </div>
<script>
  const raw = window.__MCP_TOOL_RESULT__;
  const colors = ['#667eea','#a78bfa','#f472b6','#38bdf8','#4ade80','#fbbf24','#fb923c','#e879f9'];
  const R = 50, C = 2 * Math.PI * R;

  try {
    const d = JSON.parse(raw);
    document.getElementById('title').textContent = d.title || 'Breakdown';
    const total = d.values.reduce((a,b) => a+b, 0);
    document.getElementById('total').textContent = total.toLocaleString();

    const svg = document.getElementById('donut');
    const legend = document.getElementById('legend');
    let offset = 0;

    d.labels.forEach((label, i) => {
      const v = d.values[i], pct = v / total;
      const c = colors[i % colors.length];
      const circle = document.createElementNS('http://www.w3.org/2000/svg','circle');
      circle.setAttribute('cx','60'); circle.setAttribute('cy','60'); circle.setAttribute('r', R);
      circle.style.stroke = c;
      circle.style.strokeDasharray = '0 ' + C;
      circle.style.strokeDashoffset = -offset;
      circle.style.transition = 'stroke-dasharray 1s cubic-bezier(0.4,0,0.2,1)';
      svg.appendChild(circle);

      requestAnimationFrame(() => requestAnimationFrame(() => {
        circle.style.strokeDasharray = (pct * C) + ' ' + C;
      }));

      offset += pct * C;

      legend.innerHTML += '<div class="legend-item"><div class="legend-dot" style="background:'+c+'"></div>'+label+' ('+Math.round(pct*100)+'%)</div>';
    });
  } catch(e) { document.getElementById('title').textContent = 'No data'; }
</script>
</body>
</html>
"""


@mcp.resource("ui://demo/chart", name="Bar Chart", mime_type="text/html")
def chart_resource() -> str:
    return CHART_HTML

@mcp.resource("ui://demo/dashboard", name="KPI Dashboard", mime_type="text/html")
def dashboard_resource() -> str:
    return DASHBOARD_HTML

@mcp.resource("ui://demo/donut", name="Donut Chart", mime_type="text/html")
def donut_resource() -> str:
    return DONUT_HTML


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = mcp.streamable_http_app()
    print("MCP Apps test server running at http://localhost:8765/mcp")
    print("Tools: show_chart, show_dashboard, show_donut, greet")
    uvicorn.run(app, host="0.0.0.0", port=8765)
