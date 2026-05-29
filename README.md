# Open WebUI Plugins — Inline Visualizer Collection

A curated collection of plugins for [Open WebUI](https://github.com/open-webui/open-webui) — tools, skills, filters, pipes, and actions that extend your AI chat experience.

> **Acknowledgement:** This project is based on and inspired by [Classic298/open-webui-plugins](https://github.com/Classic298/open-webui-plugins). The `inline-visualizer` (v1) foundation was created by Classic298. The `inline-visualizer-v3` and `inline-visualizer-template` plugins are independently developed by **Derek**.

---

## Plugins Overview

| Plugin | Type | Author | Description |
|--------|------|--------|-------------|
| [Inline Visualizer v2](inline-visualizer-v2/) | Tool + Skill | Classic298 | Streaming live-render visualization engine — watch HTML/SVG paint token-by-token |
| [Inline Visualizer v3](inline-visualizer-v3/) | Tool + Skill | **Derek** | Next-gen streaming visualizer with enhanced design system, bilingual skill support, and expanded bridge architecture |
| [Inline Visualizer Template](inline-visualizer-template/) | Tool + Skill | **Derek** | Rapid template-based visualization — 4 self-describing functions, flat parameters, zero code generation |
| [Inline Visualizer v1](inline-visualizer/) | Tool + Skill | Classic298 | Legacy static render engine — one-shot HTMLResponse mode |
| [Email Composer](email-composer/) | Tool | Classic298 | AI-powered email drafting with rich UI card |
| [MCP App Bridge](mcp-app-bridge/) | Tool | Classic298 | Renders MCP Apps (SEP-1865) as Rich UI embeds |

---

## Featured Plugins — Deep Dive

### v2 — Inline Visualizer (Streaming Edition)

The breakthrough streaming visualization engine. The model calls `render_visualization(title=...)`, then emits HTML/SVG between `@@@VIZ-START` / `@@@VIZ-END` markers. A same-origin iframe observer tails the chat DOM and reconciles new nodes in real time — you watch cards, SVGs, and charts appear as the model types, not as a single pop-in when the message completes.

**Core capabilities:**

- **Live streaming render** — First elements appear within ~50ms of the opening marker. Token-by-token DOM reconciliation via a custom safe-cut HTML parser and incremental reconciler. Existing nodes never re-mount, animations never re-trigger, zero flicker.
- **Full design system** — 9 color ramps (purple, teal, coral, pink, gray, blue, green, amber, red) with auto light/dark adaptation. SVG utility classes (`.t`, `.ts`, `.th`, `.box`, `.node`, `.arr`, `.leader`, `.c-{ramp}`). Pre-styled bare HTML elements — drop a vanilla `<button>`, `<input>`, `<textarea>`, `<select>`, `<table>`, `<details>`, `<dl>` (grid/inline layouts) and they render theme-matched with no class or style needed.
- **`data-accent` palette** — Set `data-accent="teal"` on any element to recolor focus rings, checkboxes, radios, and `var(--accent)` consumers. 9 named values matching the chart ramps.
- **6 interactive bridges** — `sendPrompt(text)` for conversational drill-down, `openLink(url)`, `copyText(text)` with auto-toast, `toast(msg, kind)` with success/info/warn/error levels, `saveState(k,v)` / `loadState(k,fallback)` for per-message localStorage persistence that survives reloads.
- **CDN library ecosystem** — First-class support for Chart.js, D3.js, Vega-Lite, ECharts, Plotly, vis-network, and Tone.js/Wavesurfer — each with vetted CDN URLs and usage guidance. Allowlisted in strict CSP out of the box.
- **46-language i18n** — 230 translations across 5 UI strings. Auto-detected from server-injected `<html data-iv-lang>`, parent `localStorage.locale`, and `navigator.language`.
- **Configurable CSP** — Strict (no external fetch/images), Balanced (images allowed), None (full access). Switch via tool valve.
- **Stream-completion feedback** — Localized "Visualization ready" toast + optional soft C-major arpeggio chime (Web Audio sine oscillators). Off-switchable globally or per-viz.
- **Production hardening** — Script-boundary safety guards, tool-result-example bleed protection, bootstrap resilience with independent guard layers, per-tick efficiency caching, dynamic script injection via Promise chains.

**Effect:** Users experience fluid, painterly visual generation. Complex dashboards, interactive diagrams, and data explorations materialize in real time — not as a static result, but as a live creative act.

---

### v3 — Inline Visualizer v3 (Next-Gen Streaming)

Independently developed by **Derek**, v3 evolves the streaming architecture with a refined design system, expanded bridge capabilities, and first-class bilingual (Chinese/English) skill support. Built for production-grade visualization workflows.

**What v3 brings over v2:**

- **Redesigned design system** — Refined color palette, enhanced SVG primitives, and more expressive pre-styled components. The bare HTML styling covers an even wider range of form elements and layout patterns.
- **Bilingual skill support** — `SKILL.md` (English) + `SKILL.zh.md` (Chinese) included out of the box. Models can load the skill handbook in either language, dramatically improving visualization quality for Chinese-language users.
- **Expanded bridge architecture** — All v2 bridges plus additional communication primitives for richer interactivity between visualizations and the parent chat.
- **Improved rendering engine** — Optimized DOM reconciler with better handling of edge cases, faster paint cycles, and reduced memory footprint.
- **Enhanced CDN library integration** — Tighter integration with the visualization library ecosystem, ensuring scripts load reliably and charts render correctly on first paint.
- **Comprehensive error recovery** — Multi-layer fallback system ensures visualizations degrade gracefully rather than failing silently.
- **Production-tested** — Includes runtime guard tests (`test_streaming_runtime_guards.py`) and dry-run validation (`dry_run_v3.py`) for deployment verification.

**Effect:** v3 delivers the most polished streaming visualization experience in the ecosystem. Chinese-speaking users get native-language skill guidance. Developers get a battle-tested, well-documented foundation for building custom visualization workflows.

---

### Template — Inline Visualizer Template (Rapid Templating)

Independently developed by **Derek**, this plugin takes a fundamentally different approach: instead of having the model generate HTML/CSS/JS from scratch, it provides **4 self-describing functions** with flat parameter signatures. The model passes structured JSON data, and the tool handles all rendering internally using Chart.js.

**Design philosophy:** v3's `render_visual_template` uses a single function with a `template` enum + nested `data` dict. Models see `data: Optional[Dict[str, Any]]` and cannot understand the expected structure. Template v4 (this plugin) splits into 4 independent functions where **each function's parameters ARE its schema** — models understand the contract directly from the function signature.

| Dimension | v3 (generic function) | Template (4 functions) |
|-----------|----------------------|------------------------|
| Function count | 1 generic function | 4 independent functions |
| Parameter design | Nested `data` dict | Flat typed parameters |
| Schema definition | SKILL.md documentation | Function signature + parameter names |
| Validation location | Browser JS | Python side |
| Error feedback | HTML error card | Plain text error message |
| Model instructions | External SKILL.md | Built-in `tool_instructions` |

**Four functions:**

1. **`render_data_detail`** — SQL + explanation + data table preview. `columns` and `rows` required. SQL and explanation auto-collapsed, table always visible with pagination for >10 rows.

2. **`render_chart`** — Line, bar, pie (doughnut via Chart.js), or table. `series` as row objects with one x-axis key plus one or more numeric y columns (`[{label, value}]` remains a simple compatibility form). Multi-column support with `y_columns`. Auto-detects numeric columns. Unit-safe y-axis labels for line/bar charts. Chart type switcher, PNG export.

3. **`render_dashboard`** — KPI metric cards + optional trend chart. `metrics` as `[{label, value, delta?}]`. Delta auto-colored (green for `+`, red for `-`). Optional `series` for trend chart below cards.

4. **`render_analysis_dashboard`** — Comprehensive monitoring/diagnostic dashboard with KPI, trend, breakdown, ranking, narrative, and alert modules.

**Key advantages:**

- **Near-zero model burden** — Model passes flat JSON parameters instead of generating hundreds of lines of HTML/CSS/JS. Dramatically fewer token errors, faster generation, higher success rate.
- **Python-side validation** — Invalid parameters return plain text error messages the model can read and correct immediately. No broken HTML cards.
- **Built-in interactivity** — Chart type switching (line/bar/pie/table), PNG export, auto dark mode, render statistics (JSON length, HTML length, build time, render time).
- **Complements v3, not replaces it** — Use Template for high-frequency data charts, KPI dashboards, and SQL data previews. Use v3 for complex custom visualizations, interactive diagrams, maps, and creative layouts.

**Recommended call flow:** `render_data_detail` first (show data source + SQL) → then `render_chart` for single charts, `render_dashboard` for lightweight KPI overviews, or `render_analysis_dashboard` for explicit comprehensive, monitoring, or diagnostic dashboard requests.

**Effect:** Template turns "show me a chart of this data" from a multi-hundred-token HTML generation task into a ~50-token JSON parameter pass. Success rate approaches 100% for structured data visualization. The model focuses on data analysis, not frontend coding.

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

## Quick Start — Visualization Plugins

```bash
# v2 (Streaming) — Live token-by-token render
cp inline-visualizer-v2/tool.py → Workspace → Tools
cp inline-visualizer-v2/SKILL.md → Workspace → Skills (name: "visualize")

# v3 (Next-Gen) — Enhanced streaming with bilingual support
cp inline-visualizer-v3/tool.py → Workspace → Tools
cp inline-visualizer-v3/SKILL.md → Workspace → Skills (name: "visualize")

# Template — Rapid templated charts & dashboards
cp inline-visualizer-template/tool.py → Workspace → Tools
cp inline-visualizer-template/SKILL.md → Workspace → Skills (name: "visual_template")
```

**Required:** Enable **Allow iframe same origin** in Open WebUI Settings → Interface (required for v2 and v3 streaming mode).

---

## Version Selection Guide

| Use case | Recommended plugin |
|----------|-------------------|
| High-frequency data charts (line, bar, pie, table) | Template |
| KPI dashboards with metric cards | Template |
| SQL data preview with explanation | Template |
| Complex SVG diagrams (architecture, flowcharts) | v3 |
| Interactive maps, periodic tables, quizzes | v3 |
| Custom creative visualizations | v3 |
| Live streaming visual experience | v2 or v3 |
| Chinese-language chat environments | v3 (bilingual skill) |

---

Each plugin folder is self-contained with all necessary files and documentation.

---

## Contributing

Found a bug or have an idea? Open an issue or submit a pull request.

---

## Credits

- [Classic298/open-webui-plugins](https://github.com/Classic298/open-webui-plugins) — Original inline-visualizer v1, v2, email-composer, and MCP app bridge
- **Derek** — Independent development of inline-visualizer-v3 and inline-visualizer-template
