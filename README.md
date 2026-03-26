# 🧩 Open WebUI Plugins

A curated collection of plugins for [Open WebUI](https://github.com/open-webui/open-webui) — tools, skills, filters, pipes, and actions that extend your AI chat experience.

Each plugin lives in its own folder with a README explaining what it does, what components it includes, and how to set it up.

---

## Plugins

| Plugin | Description | Components |
|--------|-------------|------------|
| [Email Composer](email-composer/) | AI-powered email drafting with an interactive Rich UI card. Rich text editing, To/CC/BCC chips, priority, download .eml, one-click send via mailto. | Tool |
| [Inline Visualizer](inline-visualizer/) | Interactive HTML/SVG visualizations inline in chat. Full design system with theme-aware colors, SVG utilities, Chart.js/D3 support, and a sendPrompt bridge for conversational drill-down. | Tool + Skill |
| [MCP App Bridge](mcp-app-bridge/) | Renders MCP Apps (SEP-1865) as Rich UI embeds. Connects to MCP servers, calls tools with `ui://` resources, injects server-declared CSP, and renders the HTML inline — no middleware changes needed. | Tool |

---

## Plugin Types

| Type | What it does | Where to install |
|------|-------------|-----------------|
| **Tools** | Give your model new capabilities it can call (web search, APIs, rendering) | Workspace → Tools |
| **Skills** | Structured instructions that teach a model how to do specified tasks or workflows | Workspace → Skills |
| **Filters** | Transform messages before they reach the model or before they're shown to you | Admin Panel → Functions |
| **Pipes** | Custom model endpoints — proxy, merge, or create entirely new model behaviors | Admin Panel → Functions |
| **Actions** | Buttons that appear below messages for quick actions | Admin Panel → Functions |

---

## How to Install

1. Open the plugin's folder and read its **README** for specific instructions
2. Each README lists the components (tool, skill, filter, etc.) and where to install them
3. Some plugins are a single file, others are multi-component — the README will guide you

---

Each plugin folder is self-contained with all necessary files and documentation.

---

## Contributing

Found a bug or have an idea? Open an issue.
