# 📊 Inline Visualizer

> [!IMPORTANT]
> **This is v1.** A newer version with **live streaming support** is available: [Inline Visualizer v2](../inline-visualizer-v2/)

Renders interactive HTML/SVG visualizations inline in chat. Includes a full design system with theme-aware colors, SVG utility classes, and a communication bridge that lets visualizations send prompts back to the chat.

> [!TIP]
> **🚀 [Jump to Setup Guide](#setup)** — get up and running in under 1 minute.

<table>
  <tr>
    <td><img src="assets/screenshot_stock_dashboard.png" alt="Stock dashboard (Qwen 3.5 27B)" width="400"/></td>
    <td><img src="assets/screenshot_tactical_analysis.png" alt="Tactical analysis dashboard (Qwen 3.5 MoE 3B)" width="400"/></td>
  </tr>
  <tr>
    <td><img src="assets/screenshot_1.png" alt="Interactive quiz" width="400"/></td>
    <td><img src="assets/screenshot_2.png" alt="Transformer architecture" width="400"/></td>
  </tr>
  <tr>
    <td><img src="assets/screenshot_3.png" alt="Periodic table" width="400"/></td>
    <td><img src="assets/screenshot_4.png" alt="Bar chart" width="400"/></td>
  </tr>
</table>

## Features

- Interactive HTML/SVG visualizations embedded as Rich UI cards
- Auto-detected light/dark theme with live switching support
- Configurable Content Security Policy (strict / standard / none)
- 9-color ramp with fill, stroke, and text variants
- SVG utility classes for text, shapes, connectors, and color-coded nodes
- Pre-styled interactive elements (buttons, sliders, selects)
- Chart.js and D3.js support via CDN
- `sendPrompt(text)` bridge — visualizations can send messages back to the chat for conversational exploration (works out of the box since Open WebUI 0.8.11; see [step 4](#4-enable-same-origin-access) for auto-submit)
- `openLink(url)` bridge — open URLs in a new tab from within visualizations

## Components

This plugin has two parts that work together:

| File | Type | Install location |
|------|------|-----------------|
| `tool.py` | Tool | Workspace → Tools |
| `skill.md` | Skill | Workspace → Knowledge → Create Skill |

The **tool** handles rendering and injects the design system (CSS, JS bridges). The **skill** teaches the model *how* to use the design system — color ramps, SVG patterns, diagram types, and when to use `sendPrompt` for interactive exploration.

## Setup

**Prerequisite**: Fast model is recommended, strong model is required for complex and visually stunning interactive visualizations.
Tested with Claude Haiku 4.5, Claude Opus 4.5, Claude Opus 4.6, Gemini 3 Flash Preview, and Qwen 3.5 27B.

### 1. Install the Tool

1. Copy the contents of `tool.py`
2. In Open WebUI, go to **Workspace → Tools → + Create New**
3. Paste the code and click **Save**

### 2. Install the Skill

1. Copy the contents of `skill.md`
2. In Open WebUI, go to **Workspace → Skills → + Create New**
3. Give it the name **visualize** (this exact name is required)
4. Paste the contents and click **Save**

### 3. Attach to a Model

1. Go to **Admin Panel → Settings → Models** and edit your model
2. Under **Tools**, enable the **Inline Visualizer** tool
3. Under **Skills**, attach the **visualize** skill
4. Ensure native function calling is enabled for your model
5. Save

### 4. Enable Same-Origin Access

> [!IMPORTANT]
> **COMPLETELY OPTIONAL** - As of **Open WebUI 0.8.11**, interactive buttons that send prompts back to the chat (`sendPrompt`) work **without** enabling same-origin. A confirmation dialog will appear each time, letting you review the prompt before it is submitted.
> Same-origin access is only required if you want to **auto-submit** without confirmation.

If you prefer **auto-submit without confirmation**, enable same-origin:

1. Go to **Settings → Interface**
2. Enable **iframe Sandbox Allow Same Origin**

> [!NOTE]
> Enabling same-origin has security implications — JavaScript inside the visualization gains access to the parent page. If you're fine with the confirmation dialog, you can skip this step entirely. Read more [here](#security).

## Usage

Ask your model to visualize, diagram, or chart something. The model will call `view_skill("visualize")` to load the design system rules, then call `render_visualization(...)` with the HTML/SVG content.

### Example prompts

- *"Visualize the architecture of a microservices system"*
- *"Show me a flowchart of how Git branching works"*
- *"Create an interactive quiz about European capitals"*

### How sendPrompt works

Visualizations can include clickable elements that send a message back to the chat:

```html
<button onclick="sendPrompt('Tell me more about Node A')">Explore Node A</button>
```

When clicked, this fills the chat input and sends the message automatically, enabling conversational drill-down into diagram components.

## Security

> [!WARNING]
> When *iframe Sandbox Allow Same Origin* is enabled (optional step 4), JavaScript inside the visualization can access the parent Open WebUI page. This is a platform-level setting that the tool cannot restrict. Since Open WebUI 0.8.11, the `sendPrompt` bridge works without same-origin (via a confirmation dialog), so you can leave same-origin **disabled** for maximum isolation without losing functionality.

The tool applies a Content Security Policy (CSP) to every rendered visualization. The security level is configurable via the tool's **Valves** in Open WebUI (Workspace → Tools → Inline Visualizer → gear icon).

<img src="assets/screenshot_tools_workspace.png" alt="Tools workspace with Valves button" width="600"/>

*Open the Valves by clicking the gear icon next to the Inline Visualizer tool.*

<img src="assets/screenshot_valve_dropdown.png" alt="Security level dropdown" width="400"/>

*Select the security level from the dropdown. Strict is the recommended default.*

| Level | Outbound requests | External images | URL param stripping | Use case |
|-------|:-:|:-:|:-:|------|
| **Strict** (default) | ❌ Blocked | ❌ Blocked | ✅ Active | Maximum safety. Most visualizations work normally. |
| **Balanced** | ❌ Blocked | ✅ Allowed | — | Visualizations that display external images (flags, logos). |
| **None** | ✅ Allowed | ✅ Allowed | — | Visualizations that fetch live API data (stock prices, weather). |

**Strict** (recommended) is the default and works for the vast majority of visualizations. All core features — HTML rendering, SVGs, Chart.js charts, D3 diagrams, emoji icons, quizzes, forms, interactive buttons, animations, and the `sendPrompt` / `openLink` bridges — work normally in every mode.

**What won't work in Strict mode:**
- Visualizations that load images from the web (e.g. product photos, map tiles, external diagrams)
- Visualizations that fetch live data directly from external APIs within the embed

**What won't work in Balanced mode:**
- Visualizations that fetch live data directly from external APIs within the embed

If you're unsure, leave it on **Strict**. You'll know when you need to change it — the visualization will be missing an image or fail to load data.

> [!NOTE]
> Even in **None** mode, external API requests may still fail due to CORS (Cross-Origin Resource Sharing) restrictions. This happens when the remote server does not allow cross-origin requests — it is standard browser security behavior and not a tool limitation.
