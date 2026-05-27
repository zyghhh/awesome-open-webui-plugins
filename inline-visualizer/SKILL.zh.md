---
name: visualize
description: 使用 render_visualization 工具，直接在聊天中内联渲染丰富的交互式视觉内容，包括 SVG 图、HTML 小组件、Chart.js 图表和交互式解释器。当用户要求可视化、画图、生成图表、绘制、梳理地图或图示说明某个内容时使用；当主题包含空间、顺序或系统关系，且图示比文字更清楚时也使用。对于数据对比、指标、架构、流程或机制等适合视觉表达的内容，也可以主动使用。
---

# Inline Visualizer

使用 `render_visualization` 直接在聊天中内联渲染丰富的交互式视觉内容。

## 使用方法

1. 调用 `render_visualization(html_code, title)`，传入 HTML 或 SVG **内容片段**
2. 不要包含 `<!DOCTYPE>`、`<html>`、`<head>` 或 `<body>`，工具会自动包裹你的内容
3. 结构顺序：先写 `<style>`（优先使用内联样式）→ 可见内容 → 最后写 `<script>`
4. 工具会自动注入：主题 CSS、SVG 类、色阶、自动高度上报、`sendPrompt()` 桥接和 `openLink()` 桥接
5. 可以考虑用 `sendPrompt()` 让图表变成**可对话的图示**，具体模式和示例见 [sendPrompt 桥接：可对话图示](#sendprompt-桥接可对话图示)

## 输出规则

这些规则能让视觉内容保持简洁、可访问，并与宿主 UI 风格一致：

- **扁平设计**：不要使用渐变、投影、模糊、发光或噪声纹理（宿主 UI 是扁平的，保持一致能避免视觉突兀）
- **不要使用 emoji**：用 CSS 形状或 SVG 路径做图标（emoji 在不同平台上渲染不一致）
- **句式大小写**：所有标签和标题都使用 sentence case
- **展示数字要取整**：使用 Math.round、toLocaleString 或 Intl.NumberFormat
- **最小字号 11px**：更小的字号在大多数屏幕上会难以阅读
- **文字字重**：400 为常规，500 只用于强调
- **所有解释性文字放在你的普通回复中**，不要放进视觉内容里（这样能让视觉内容保持高信息密度，同时由模型回复提供上下文）

---

## 设计系统

### CSS 变量（自动注入：始终使用这些变量，不要硬编码颜色）

工具会注入支持主题的 CSS 变量，并自动适配浅色/深色模式。硬编码十六进制颜色会导致其中一种模式下显示异常。

| Token | 用途 |
|-------|------|
| `--color-text-primary` | 主文本 |
| `--color-text-secondary` | 标签、弱化文本 |
| `--color-text-tertiary` | 提示、占位符 |
| `--color-text-info/success/warning/danger` | 语义文本 |
| `--color-bg-primary` | 主背景 |
| `--color-bg-secondary` | 卡片、表面 |
| `--color-bg-tertiary` | 页面背景 |
| `--color-border-tertiary` | 默认边框（0.15 alpha） |
| `--color-border-secondary` | 悬停边框（0.3 alpha） |
| `--font-sans` | 默认字体 |
| `--font-mono` | 代码字体 |
| `--radius-md / --radius-lg / --radius-xl` | 8px / 12px / 16px |

### 色阶（9 组色阶，自动适配浅色/深色）

每组色阶都提供填充、描边和文本变体，并通过 CSS 类自动适配当前主题。

| Ramp | 50（浅色填充） | 200 | 400 | 600（浅色描边） | 800（浅色标题） |
|------|------|------|------|------|------|
| purple | #EEEDFE | #AFA9EC | #7F77DD | #534AB7 | #3C3489 |
| teal | #E1F5EE | #5DCAA5 | #1D9E75 | #0F6E56 | #085041 |
| coral | #FAECE7 | #F0997B | #D85A30 | #993C1D | #712B13 |
| pink | #FBEAF0 | #ED93B1 | #D4537E | #993556 | #72243E |
| gray | #F1EFE8 | #B4B2A9 | #888780 | #5F5E5A | #444441 |
| blue | #E6F1FB | #85B7EB | #378ADD | #185FA5 | #0C447C |
| green | #EAF3DE | #97C459 | #639922 | #3B6D11 | #27500A |
| amber | #FAEEDA | #EF9F27 | #BA7517 | #854F0B | #633806 |
| red | #FCEBEB | #F09595 | #E24B4A | #A32D2D | #791F1F |

**颜色分配规则：**
- 颜色表示**含义**，不是顺序，不要像彩虹一样循环使用
- 按类别给节点分组，同一类型使用同一种颜色
- 使用 **gray** 表示中性/结构性节点（开始、结束、通用节点）
- 每张图最多使用 **2–3 种颜色**
- 将 blue/green/amber/red 保留给语义含义（信息/成功/警告/错误）

### 图表数据集颜色（使用 400 档）

| Series | Color | Hex |
|--------|-------|-----|
| 1 | teal-400 | #1D9E75 |
| 2 | purple-400 | #7F77DD |
| 3 | coral-400 | #D85A30 |
| 4 | blue-400 | #378ADD |
| 5 | amber-400 | #BA7517 |

对于面积图/折线图填充，使用相同颜色并设置 20% 透明度。

---

## SVG 设置

始终使用这个 SVG 样板：

```svg
<svg width="100%" viewBox="0 0 680 H">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
</svg>
```

- viewBox 宽度**始终为 680**，将 H 设置为**刚好包住内容**（最后一个元素底部 + 40px）。**不要过大**，计算最后一个 SVG 元素的实际底部并加 40px。如果内容在 y=180 结束，H 应为 220，而不是 500
- 安全区域：x=40 到 x=640
- 背景透明，宿主提供容器

### SVG 类（自动注入）

| Class | 用途 |
|-------|------|
| `.t` | 14px 主文本 |
| `.ts` | 12px 次级文本 |
| `.th` | 14px 加粗（500）主文本 |
| `.box` | 中性矩形（次级背景、三级边框） |
| `.node` | 可点击元素（指针光标、悬停透明度） |
| `.arr` | 箭头线（1.5px，border-secondary） |
| `.leader` | 虚线引导线（0.5px，tertiary） |
| `.c-{ramp}` | 应用在 `<g>` 上的色阶类，会自动设置子级 rect/circle/ellipse 的填充/描边和文本颜色 |

### 字体宽度校准
- 14px：每个字符约 8px
- 12px：每个字符约 7px
- 盒子宽度 = max(title_chars × 8, subtitle_chars × 7) + 24

### 文本定位
盒子内的每段文本都需要设置 `dominant-baseline="central"`，并将 y 放在对应槽位的垂直中心。否则文本会大约高出 4px，看起来没有对齐。

---

## 图示类型

### 流程图：顺序步骤、决策

**适用场景：** “带我走一遍步骤”、“流程是什么”

- 每张图最多 **4–5 个节点**，6 个以上就拆成概览 + 子流程
- 盒子间距：盒子之间 60px，内部 padding 24px
- 单行节点：高度 44px；双行节点：高度 56px
- 箭头不能穿过任何盒子，需要时使用 L 形折线
- 箭头路径使用 `marker-end="url(#arrow)"`

单行节点：
```svg
<g class="node c-teal" onclick="sendPrompt('Tell me about X')">
  <rect x="100" y="20" width="180" height="44" rx="8"/>
  <text class="th" x="190" y="42" text-anchor="middle" dominant-baseline="central">Label</text>
</g>
```

双行节点：
```svg
<g class="node c-teal">
  <rect x="100" y="20" width="200" height="56" rx="8"/>
  <text class="th" x="200" y="38" text-anchor="middle" dominant-baseline="central">Title</text>
  <text class="ts" x="200" y="56" text-anchor="middle" dominant-baseline="central">Subtitle</text>
</g>
```

### 结构图：包含关系、架构

**适用场景：** “架构是什么”、“X 位于哪里”

- 最外层容器：rx=20–24，最浅填充色（50 档），0.5px 描边
- 内部区域：rx=8–12，下一层色阶；如果语义不同，使用不同色阶
- 容器内部最小 padding 20px
- 最多 2–3 层嵌套

### 说明性图示：空间隐喻、机制

**适用场景：** “X 实际如何工作”、“解释 X”（空间概念）

- 画出**机制本身**，不要只是画“关于它的图”
- 形状可以自由：路径、椭圆、多边形、曲线
- 颜色表示强度（暖色 = 活跃，冷色 = 平静，灰色 = 惰性）
- 标签放在对象外部，并用引导线连接，预留 140px 边距
- **优先交互式而非静态**：如果系统有控制项，就给图示加入对应控制

---

## 图表（Chart.js）

在 HTML 片段中加载 Chart.js：
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```

设置模式：
```html
<div style="position: relative; height: 300px;">
  <canvas id="chart"></canvas>
</div>
<script>
const ctx = document.getElementById('chart').getContext('2d');
const s = getComputedStyle(document.documentElement);
const textColor = s.getPropertyValue('--color-text-secondary').trim();
const gridColor = s.getPropertyValue('--color-border-tertiary').trim();

new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Q1','Q2','Q3','Q4'],
    datasets: [{ label: 'Revenue', data: [12,19,8,15],
      backgroundColor: '#1D9E75', borderRadius: 4, borderSkipped: false }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: textColor, font: { size: 12 } } } },
    scales: {
      x: { grid: { display: false }, ticks: { color: textColor, font: { size: 12 } }, border: { color: gridColor } },
      y: { grid: { color: gridColor }, ticks: { color: textColor, font: { size: 12 } }, border: { display: false } }
    }
  }
});
</script>
```

**图表规则：**
- 用带有 `position: relative` 和明确高度的容器包裹 canvas
- 始终设置 `responsive: true` 和 `maintainAspectRatio: false`
- 从 CSS 变量读取文本/边框颜色，不要硬编码
- 柱状图使用 `borderRadius: 4`
- 折线图使用 `tension: 0.3` 让曲线更平滑
- 环形图使用 `cutout: '60%'`，不要使用饼图

**图表类型选择：**

| 数据形态 | 类型 | 说明 |
|----------|------|------|
| 分类 + 数值 | Bar | 标签较长时使用横向柱状图 |
| 时间序列 | Line | tension: 0.3 |
| 整体的组成部分 | Doughnut | cutout: '60%' |
| 两个变量 | Scatter | 相关时加入趋势线 |

### 内联 SVG 图表（无需库）

水平条形图：
```svg
<svg width="100%" viewBox="0 0 680 80">
  <text class="ts" x="40" y="30">Category A</text>
  <rect x="160" y="16" width="360" height="20" rx="4" fill="#1D9E75" opacity="0.8"/>
  <text class="ts" x="530" y="30">72%</text>
</svg>
```

---

## 组件模式

### 指标卡片
```html
<div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px;">
  <div style="background:var(--color-bg-secondary); border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--radius-lg); padding:16px;">
    <div style="font-size:12px; color:var(--color-text-secondary);">Label</div>
    <div style="font-size:28px; font-weight:500; color:var(--color-text-primary); margin-top:4px;">$3,870</div>
  </div>
  <!-- repeat -->
</div>
```

### 对比布局
并排卡片，共用一个标题行，每列展示各自的指标。

### 交互式解释器
使用滑块或按钮通过 JavaScript 更新可见状态。例如：一个滑块控制变量，并实时更新 SVG 或数值显示。

---

## sendPrompt 桥接：可对话图示

`sendPrompt(text)` 是让可视化内容具备对话能力的函数。调用它时，会把给定文本注入聊天输入框并提交，效果就像用户自己输入并发送了这段话。模型随后会收到这条消息并正常回复，从而在视觉内容和对话之间形成反馈循环。

这正是静态图和**探索式界面**之间的区别。用户看到一个系统架构图，点击 “Load Balancer” 节点，模型就会收到 “Tell me more about the load balancer — how does it distribute traffic across the backend services?” 作为用户消息。模型随后回复细节，甚至可以生成一个新的子图来展示负载均衡器内部结构。用户不需要打字，只需要点击。

### 为什么这很重要

没有 sendPrompt 时，iframe 内的交互元素是隔离的：它们可以切换可见性、播放动画或过滤数据，但无法把信息传回模型。用户会看到一个很酷的图，但必须手动输入追问。有了 sendPrompt，每个可点击元素都能成为对话入口。图示本身就变成了主题的导航界面。

### 技术上如何工作

该函数由工具自动注入。它使用 Open WebUI 原生的 `postMessage` 协议，将文本作为用户消息提交。如果 AI 仍在生成回复，该消息会自动排队，并在生成完成后发送。这要求在 Open WebUI 设置中启用 **iframe Sandbox Allow Same Origin**；如果没有启用，函数会静默失败（可视化本身仍然可用，但点击没有效果）。

### 编写好的 sendPrompt 文本

传给 sendPrompt 的文本会成为用户发给模型的消息。把它写成自然的追问：对话式、具体，并引用图中的上下文。

**好的 prompt 文本**（具体、有上下文、引用图示）：
- `"Explain the attention mechanism — how does it decide which tokens to focus on?"`
- `"Break down the CI/CD pipeline stage. What tools are typically used here?"`
- `"Show me a more detailed diagram of the data processing layer"`
- `"What happens when the load balancer detects a failed backend node?"`
- `"Compare the pros and cons of the monolith vs microservices approach shown here"`

**差的 prompt 文本**（模糊、泛泛而谈、丢失上下文）：
- `"Tell me more"`：更多关于什么？
- `"Explain"`：解释什么？
- `"Details"`：不是一个句子，模型不知道该做什么

### 使用模式

简单模式：在节点或按钮上单击触发 sendPrompt：
- **深入解释**：在图示节点上使用 `onclick="sendPrompt('Explain the API gateway — what does it handle?')"`
- **测验答案**：在答案按钮上使用 `onclick="sendPrompt('I chose B: O(n log n). Am I right? Explain why.')"`
- **引导式探索**：在 “Go deeper →” 按钮上使用 `onclick="sendPrompt('Show me a more advanced example with edge cases.')"`
- **对比**：在两个节点之一上使用 `onclick="sendPrompt('Compare REST vs GraphQL — when should I use each?')"`

**表单/偏好收集器**：收集多个用户选择，然后一次性发送。使用本地 JS 跟踪选择（按钮高亮、状态对象），再用提交按钮根据收集到的答案组合 sendPrompt：
```html
<script>
var choices = {};
function pick(category, value, btn) {
  choices[category] = value;
  // Highlight selected button, dim siblings
  btn.parentElement.querySelectorAll('button').forEach(function(b) {
    b.classList.toggle('active', b === btn);
  });
}
function submitChoices() {
  var parts = [];
  for (var k in choices) parts.push(k + ': ' + choices[k]);
  sendPrompt('Here are my preferences:\n' + parts.join('\n') + '\nGive me a personalized recommendation based on these choices.');
}
</script>

<h3>What's your style?</h3>
<p style="margin:8px 0 4px;">Pace</p>
<button onclick="pick('pace','relaxed',this)">Relaxed</button>
<button onclick="pick('pace','moderate',this)">Moderate</button>
<button onclick="pick('pace','intensive',this)">Intensive</button>

<p style="margin:8px 0 4px;">Focus</p>
<button onclick="pick('focus','culture',this)">Culture</button>
<button onclick="pick('focus','nature',this)">Nature</button>
<button onclick="pick('focus','food',this)">Food</button>

<button onclick="submitChoices()" style="margin-top:12px; font-weight:500;">Get my recommendation →</button>
```
这个模式很强大，因为模型会在一条消息中收到所有用户偏好的结构化摘要。选择 UI 使用本地 JS（即时反馈），只在最终提交时调用 sendPrompt。

### 什么时候使用 sendPrompt，什么时候使用本地 JS：
| 用户操作 | 使用 | 原因 |
|----------|------|------|
| 了解某个组件的更多信息 | `sendPrompt` | 模型能给出上下文解释 |
| 探索某个阶段 / 深入展开 | `sendPrompt` | 模型可以生成子图 |
| 提交答案或偏好 | `sendPrompt` | 模型可以评估或个性化 |
| 切换视图、调整滑块 | 本地 JS | 即时反馈，不需要推理 |
| 过滤/排序数据 | 本地 JS | 即时响应，不需要模型 |

---

## 默认加入交互

可视化应该有生命力并且完成度高，而不是把静态图片丢进聊天里。构建能邀请用户互动的界面：

- **可展开区域**：使用可折叠的 `<details>` 元素或 JS 切换区块，让用户按自己的节奏探索，而不是一开始就被大量信息淹没
- **悬停效果**：节点、按钮和卡片都应响应 hover（`.node` 类会为 SVG 元素添加该效果；HTML 元素可使用 `:hover` 样式）
- **平滑过渡**：给交互元素添加 `transition: all 0.2s ease`，让体验更精致
- **激活状态**：当用户选择选项或点击标签页时，用 `.active` 类或明显样式清楚显示当前选择
- **渐进披露**：先展示清晰概览，再允许用户点击展开细节（标签页、手风琴，或用 sendPrompt 做模型驱动的深入探索）

目标是构建一个嵌在聊天中的真实应用组件，而不是一张截图。如果可视化有多个方面，就给用户控件去探索。如果信息有层级，就让用户展开和折叠。如果有数据，就让用户排序或过滤。

---

## openLink 桥接：从可视化中打开 URL

`openLink(url)` 会从可视化 iframe 内部在新的浏览器标签页中打开 URL。iframe 内普通的 `<a href="...">` 链接行为可能不可预测（在 iframe 内打开、被沙盒限制阻止等）。该函数通过在父窗口中打开链接来处理这个问题。

```html
<button onclick="openLink('https://docs.example.com/api-reference')">
  Open API docs ↗
</button>
```

或在 SVG 中：
```svg
<g class="node c-blue" onclick="openLink('https://github.com/org/repo')">
  <rect x="100" y="20" width="200" height="44" rx="8"/>
  <text class="th" x="200" y="42" text-anchor="middle" dominant-baseline="central">View source ↗</text>
</g>
```

将 `openLink` 用于外部参考、文档链接或源码链接。不同于 `sendPrompt`，它会离开聊天并打开外部资源。因此，当用户需要访问外部资源时使用它；如果用户需要模型解释某事，则不要使用它。

---

## 快速参考

| Rule | Value |
|------|-------|
| SVG viewBox width | 始终 680px |
| Font sizes | 14px 标签，12px 副标题 |
| Stroke width | 边框 0.5px |
| Max colors per diagram | 2–3 组色阶 |
| Subtitle max length | 5 个词 |
| Corner radius (SVG) | 默认 rx=4，强调 rx=8 |
| Corner radius (HTML) | var(--radius-md) 或 -lg |
| Min font size | 11px |
| Heading sizes | h1=22px，h2=18px，h3=16px |

## 常见失败

1. **箭头穿过盒子**：根据每个盒子的坐标检查路径
2. **文本溢出**：检查 (text_width + 2×padding) 是否能放进 rect
3. **viewBox 太小**：底部内容被裁切
4. **viewBox 太大**：在图下方产生浪费性的空白。计算实际内容底部 + 40px
5. **漂浮标签**：每段文本都需要盒子、图例或引导线
6. **连接线缺少 fill="none"**：会渲染成黑色形状
7. **缺少 dominant-baseline="central"**：文本会高出 4px
8. **defs 中缺少箭头 marker**：始终包含它
9. **硬编码颜色**：始终使用 CSS 变量或色阶类
