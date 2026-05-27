# 🔌 MCP App Bridge

Renders [MCP Apps](https://github.com/modelcontextprotocol/ext-apps) (SEP-1865) as Rich UI embeds in Open WebUI — using the existing embed system, no middleware changes needed.

> [!TIP]
> **🚀 [Jump to Setup Guide](#setup)** — get up and running in under 1 minute.

> [!NOTE]
> This tool follows the MCP protocol's [dynamic tool discovery pattern](#mcp-dynamic-tool-discovery) — and aligns with Anthropic's [Tool Search Tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/tool-search-tool) concept, where tools are discovered and loaded on demand rather than pre-registered in the model's context.

When an MCP server declares a `ui://` resource on a tool, this bridge fetches the HTML, injects the tool result data, applies the server-declared Content Security Policy, and renders it inline in the chat.

### Demo

| Bar Chart | KPI Dashboard | Donut Chart |
|---|---|---|
| ![Bar Chart](assets/demo-bar-chart.png) | ![Dashboard](assets/demo-dashboard.png) | ![Donut Chart](assets/demo-donut-chart.png) |

## How It Works

1. **Model calls `list_mcp_tools`** → discovers tools on the MCP server, including which ones have UI resources
2. **Model calls `call_mcp_tool`** → executes the tool, checks for `_meta.ui.resourceUri`
3. **If a UI resource exists** → fetches the HTML, injects CSP + tool result data + auto-height script, returns it as a Rich UI embed via `HTMLResponse`
4. **Open WebUI renders it** in a sandboxed iframe — same as the [Inline Visualizer](../inline-visualizer/)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  LLM calls  │────▶│  MCP App    │────▶│  MCP Server │
│  call_mcp_  │     │  Bridge     │     │  (tool +    │
│  tool()     │◀────│  (Tool)     │◀────│  ui:// res) │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │            ┌──────┴──────┐
       │            │ Injects:    │
       │            │ • CSP tag   │
       │            │ • Tool data │
       │            │ • Auto-size │
       │            └──────┬──────┘
       ▼                   ▼
┌────────────────────────────┐
│  Open WebUI renders HTML   │
│  as Rich UI embed (iframe) │
└────────────────────────────┘
```

## Security

The bridge honors the MCP Apps spec security model:

| Spec Feature | Implementation |
|---|---|
| Server-declared CSP (`_meta.ui.csp`) | Injected as `<meta http-equiv="Content-Security-Policy">` tag |
| `connectDomains` | Maps to `connect-src` directive |
| `resourceDomains` | Maps to `script-src`, `style-src`, `img-src`, `font-src`, `media-src` |
| `frameDomains` | Maps to `frame-src` directive |
| `baseUriDomains` | Maps to `base-uri` directive |
| No CSP declared | Restrictive default: blocks all outbound, allows only inline scripts/styles |
| Iframe sandboxing | Uses Open WebUI's existing sandbox with configurable same-origin toggle |

> [!WARNING]
> **Same-origin access and MCP Apps:** If "iframe Sandbox Allow Same Origin" is enabled in Open WebUI settings, the MCP App's HTML gains full access to the parent page — including session tokens, cookies, localStorage, and the ability to make authenticated API requests as the user. CSP cannot prevent this; it only controls network requests, not parent DOM access. Since MCP App HTML originates from an **external** server (unlike locally installed tools where you control the HTML), enabling same-origin carries higher risk. **Leave same-origin disabled unless you fully trust the MCP server.**

## Setup

### 1. Install the Tool

1. Copy the contents of `tool.py`
2. In Open WebUI, go to **Workspace → Tools → + Create New**
3. Paste the code
4. Name it **MCP App Bridge** (or whatever you want) and click **Save**

### 2. Configure Valves

1. Click the **gear icon** next to the MCP App Bridge tool
2. Set **mcp_server_url** to your MCP server's streamable HTTP endpoint
3. Set **auth_token** if your server requires authentication
4. Save

### 3. Attach to a Model

1. Go to **Admin Panel → Settings → Models** and edit your model
2. Under **Tools**, enable the **MCP App Bridge** tool
3. Save

### 4. Use It

Ask your model to interact with the MCP server. It will call `list_mcp_tools` to discover available tools, then `call_mcp_tool` to execute them. Tools with UI resources render as interactive embeds inline in the chat.

## Testing with the Demo Server

A minimal test server is included in `examples/test_server.py`. It exposes a `show_chart` tool with a `ui://demo/chart` resource that renders an animated bar chart.

```
python examples/test_server.py
```

Then set the valve `mcp_server_url` to `http://localhost:8765/mcp` and ask the model:

> "Use the show_chart tool to display quarterly revenue: Q1=45, Q2=62, Q3=38, Q4=71"

## Why a Tool?

The MCP Apps spec (SEP-1865) defines how MCP servers can serve interactive UIs. Some implementations require extensive middleware changes, new frontend components, and additional npm dependencies to support this.

This bridge demonstrates that Open WebUI's existing infrastructure — `HTMLResponse` for Rich UI embeds, sandboxed iframes, auto-height reporting — already provides the rendering pipeline needed. A single Tool file is sufficient to bridge the gap.

## MCP Dynamic Tool Discovery

This tool follows the MCP protocol's dynamic tool discovery pattern — and aligns with Anthropic's [Tool Search Tool](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/tool-search-tool) concept, where tools are discovered and loaded on demand rather than pre-registered in the model's context.

The two-step flow maps directly to MCP primitives:

| Bridge Function | MCP Primitive | Purpose |
|---|---|---|
| `list_mcp_tools` | `tools/list` | On-demand discovery — model learns what's available only when needed |
| `call_mcp_tool` | `tools/call` | On-demand execution — model invokes tools by name with arguments |

This avoids pre-loading every MCP tool definition into the model's context window, which is especially important for MCP servers that expose many tools. The model discovers relevant tools first, then calls only what it needs — exactly the pattern the MCP spec and Anthropic's dynamic tool loading approach advocate for.

## MCP Apps vs Open WebUI Rich UI

Open WebUI already has a native Rich UI system: tools that return `HTMLResponse` render interactive HTML inline in the chat inside a sandboxed iframe. This bridge uses that same system to render MCP Apps — no additional rendering infrastructure is needed.

> [!NOTE]
> Tools returning `HTMLResponse` always render inside an iframe, regardless of whether the "iframe Sandbox Allow Same Origin" toggle is enabled. That toggle only controls whether the iframe gets `allow-same-origin` access — the iframe isolation itself is always enforced.

| Capability | MCP Apps (via this bridge) | Open WebUI Rich UI (native) |
|---|---|---|
| Render interactive HTML inline | ✅ | ✅ |
| Sandboxed iframe isolation | ✅ Always | ✅ Always |
| Content Security Policy | ✅ Server-declared CSP | ✅ Via Tool declared CSP (e.g. Inline Visualizer's strict/balanced/none) |
| Auto-height resize | ✅ Injected via the tool | ✅ Built into HTML or injected by tool |
| Theme awareness | ❌ Not in spec | ✅ Via auto-injected CSS variables |
| Dynamic content per call | ℹ️ Static resource + data injection | ✅ Fully dynamic HTML per invocation |
| Bidirectional communication | ℹ️ JSON-RPC via SDK | ✅ Via native postMessage bridge (sendPrompt, openLink) |
| External dependencies | ⚠️ Requires MCP server with ext-apps | ✅ None — tool generates HTML directly |
| Ecosystem portability | ✅ Works across MCP-Apps compatible hosts | ❌ Open WebUI only |

The key tradeoff: MCP Apps offer **ecosystem portability** — the same UI resource works in any MCP-compatible host. Open WebUI's native Rich UI offers **more flexibility, tighter integration and no additional dependencies** — fully dynamic HTML generation, theme awareness, and bidirectional communication without external dependencies.

This bridge lets you have both: MCP App UIs render in Open WebUI using the same Rich UI pipeline that native tools use.
