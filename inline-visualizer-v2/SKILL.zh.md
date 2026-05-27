---
name: visualize
description: 使用 visualize() 直接在聊天中内联渲染丰富的交互式视觉内容，包括 SVG 图示、HTML 小组件、Chart.js 图表和交互式解释器。仅当用户明确要求可视化、图示、图表、曲线图、绘图、地图、仪表盘或类似视觉产物时使用。不要用于普通 markdown、代码块、文件预览或回答排版。
---

# Inline Visualizer

这是 visualizer 工具的使用手册/教程。
visualizer 工具可以使用 visualize 直接在聊天中内联渲染丰富的交互式视觉内容。

## 使用方法

你已经调用 view_skill() 工具来读取这个工具的教程/手册。
请仔细阅读整份手册并严格遵守规则，否则可视化内容可能无法正确渲染，甚至完全损坏。
这份教程/手册会说明如何实际使用该工具并构建漂亮的可视化。

1. 调用 visualize(title="…")。你必须调用该工具，否则你输出的可视化不会在聊天中渲染。
2. 调用工具后，一个 iFrame wrapper sandbox 会立即出现在聊天中（仅用户可见）。在你调用工具之后，这个 iFrame sandbox 会自动绘制/渲染你在标记之间输出的所有内容。
3. 调用工具后，先在单独一行输出开始标记 @@@VIZ-START
4. 然后在开始标记后输出 HTML/SVG 内容（不要包含 <!DOCTYPE>、<html>、<head>、<body>）
5. 写完可视化代码后，立即在单独一行用 @@@VIZ-END 关闭
6. 完成。可视化已经结束。之后可以继续给用户写任何后续文字。

原始 markers + SVG 源码会自动从聊天正文中隐藏，用户只会看到正在实时填充的渲染 iframe。

**示例回复结构：**

"""
I'll visualize the attention mechanism for you.

@@@VIZ-START
<svg viewBox="0 0 680 240">
  <!-- content streams here, renders live -->
</svg>
@@@VIZ-END

As you can see, each query token attends to all key tokens simultaneously.
"""

**流式规则：**
- 分隔符必须精确使用 @@@VIZ-START 和 @@@VIZ-END，区分大小写，并且各自独占一行。不要把内容放进 ```、~~~、::: 代码围栏或任何其他 markdown 代码块中。
- 不要用 <viz> 或 <svg data-iv> 这类 HTML 标签包裹，只有文本 markers 会被检测。
- 每次工具调用必须输出**恰好一组** @@@VIZ-START … @@@VIZ-END。多个可视化要多次调用工具。
- 内容结构始终为：先 `<style>` → 可见内容 → 最后 `<script>`。
- 不要用 prose 描述 HTML 源码，用户看不到源码。请描述可视化**展示了什么**。
- 需要在 Open WebUI Settings → Interface 中启用 **iframe Sandbox Allow Same Origin**。如果禁用，wrapper 会显示提示，用户不会看到可视化本身，只会看到提示。
- 你包含的任何 `<script>` 都只会在完整 block 流式输出完成后**运行一次**。

## 自动注入的内容

- 主题 CSS、SVG 类、色阶、自动高度上报、sendPrompt() bridge 和 openLink() bridge
- 预样式化的裸标签表单元素（见下文），可节省简单表单的 token
- 可以考虑用 sendPrompt() 让图示变成**可对话的**，模式和示例见下方 “sendPrompt bridge” 部分

### 预样式化表单元素

这些标签在**没有 class 或 inline style 属性时**会获得主题感知的默认样式。
其他属性（placeholder、value、id、aria-*、min/max 等）都可以，它们不会禁用默认样式。
添加 class 或 style 会被视为 opt-out：默认样式会被抑制，你可以从零开始自定义。
适用于短表单或快速 UI，不需要偏离设计系统时可以节省 token。

工具中包含的预样式化元素：

- <button>：主题化按钮。用于操作。
- <input type="text|number|email|search|password|tel|url|date|time|datetime-local">：主题化文本输入。用于用户输入或选择值。
- <input type="range">：滑块。用于区间选择、强度旋钮，或任何连续值且不需要精确输入的场景。
- <input type="checkbox">、<input type="radio">：多选/单选。含义自明。
- <textarea>：多行文本输入。
- <select>：下拉框。当选项列表太长不适合 radio 时使用。
- <label>、<fieldset>、<legend>：表单结构。用于分组相关输入并提供标签。
- <kbd>：键盘按键胶囊。每当提到快捷键时使用，让按键视觉上像键帽。
  - Mac: <kbd>⌘</kbd><kbd>K</kbd>
  - Windows / Linux: <kbd>Ctrl</kbd><kbd>K</kbd>
- <hr>：水平分隔线。用于分隔卡片内的区块或内容组。
- <details> / <summary>：可折叠披露控件。用于渐进披露，把次要细节藏在可点击 summary 后面，保持表面简洁。
- <blockquote>：引用/提示块。用于突出引用、旁注或希望读者停顿注意的上下文。
- <table>（配合 <thead> / <tbody> / <th> / <td> / <caption>）：多行多列表格。当行列关系重要时使用。数字列给单元格加 align="right" 或 class="num"（右对齐 + tabular-nums）。
- <mark>：高亮。谨慎使用，用于突出句子里的关键词或数字。
- <dl> / <dt> / <dd>：定义列表。**比表格更适合低成本表达 label/value 布局**。三种模式：
  - 裸 <dl> → **堆叠 glossary**。适合每个术语需要一两句话解释的情况：定义、FAQ、术语下方解释。
  - <dl data-layout="grid"> → **双列卡片**。当你有 key/value 对但不需要行分隔线或 hover 时，是表格的轻量替代：联系人卡、元数据块、摘要面板、设置行。
  - <dl data-layout="inline"> → **label: value 的 pill 行**（每组 <dt>/<dd> 包在一个 <div> 中）。适合卡片或图表顶部紧凑事实条：小数字、状态标记、标签。CSS 会自动添加冒号分隔符。

裸元素的额外能力：

- aria-invalid="true" 会给 input/textarea/select 绘制危险色边框
- :focus-visible 键盘焦点会绘制清晰的 --accent outline（鼠标焦点保持低调）

### Accent 色彩调色板

默认 accent 是 **purple**。可以通过 data-accent 属性切换到其他色阶。
所选颜色会驱动 --accent 和 --accent-foreground，进而影响焦点环、checkbox/radio 填充，以及你自己写的任何 var(--accent) 引用。
同样九个名称与图表色阶匹配，所以 teal accent 表单会自然地与 teal 图表并排。

可用值：purple（默认）、teal、coral、pink、gray、blue、green、amber、red

**将 accent color 应用于整个可视化**：用一个根 <div data-accent="…"> 包裹全部内容。
内部所有支持的元素都会继承所选 accent。

<div data-accent="teal">
  <style>/* CSS */</style>
  …all focus rings, checkboxes, and var(--accent) consumers go teal…
</div>

**将 accent color 应用于某个特定区域**：在任意内部容器上设置 data-accent，只为该子树重新着色：

<div data-accent="teal">
  <button>Save</button>            <!-- teal focus ring -->
  <input type="checkbox" checked>  <!-- teal accent -->
</div>
<button>Cancel</button>            <!-- still default purple -->

**将 accent color 应用于单个元素**：直接在元素上设置，只为它重新着色：

<button data-accent="green">Approve</button>
<button data-accent="red">Reject</button>

浅色和深色主题都已处理，accent 值会自动跟随每个主题的色阶档位，foreground 文本颜色也会在深色模式下翻转以保证可读性。
不需要手动覆盖。

选择与主题匹配的 accent：green 适合金融/正向，red 适合警告/危险操作，blue 适合信息型仪表盘，amber 适合注意/谨慎等。
中性或通用可视化默认使用 purple。

## 输出规则

这些规则能让视觉内容保持简洁、可访问，并与宿主 UI 一致：

- **扁平设计**：不要使用渐变、投影、模糊、发光或噪声纹理（宿主 UI 是扁平的，保持一致可以避免视觉突兀）
- **尽量不要使用 emoji**，改用 CSS 形状或 SVG 路径做图标（emoji 在不同平台渲染不一致）
- **Sentence case**：所有标签和标题使用句式大小写
- **展示数字要取整**：使用 Math.round、toLocaleString 或 Intl.NumberFormat
- **最小字号 11px**：更小的字号在大多数屏幕上难以阅读
- **文字字重**：400 为常规，500 仅用于强调
- 长篇解释放在 prose 回复中。视觉内部只使用简洁标签、说明、图例、辅助文字和短注释，且仅在它们能提升理解时使用。
- **主题支持时要大胆构建。** 把每个可视化都当作一个小产品界面，而不是单个静态图形。组合多个元素：图表配指标条、图示配可折叠深挖、对比卡片配滑块让用户探索取舍。动画、hover 和点击交互应帮助用户注意或探索，而不是装饰。如果用户要求 “a chart”，且主题自然扩展成小仪表盘，就构建仪表盘。只有在额外结构会分散注意力时才克制；默认追求丰富，而不是极简。

---

## 设计系统

### CSS 变量（自动注入，优先使用这些变量以确保浅/深色模式正常）

工具会注入主题感知 CSS 变量，自动适配浅色/深色模式。默认用它们处理文本、表面和边框颜色；只有当设计确实需要固定颜色时（品牌标识、明确不随主题变化的 accent）才使用特定 hex。

| Token | 用途 |
|-------|------|
| --color-text-primary | 主文本 |
| --color-text-secondary | 标签、弱化文本 |
| --color-text-tertiary | 提示、占位符 |
| --color-text-info/success/warning/danger | 语义文本 |
| --color-bg-primary | 主背景 |
| --color-bg-secondary | 卡片、表面 |
| --color-bg-tertiary | 页面背景 |
| --color-border-tertiary | 默认边框（0.15 alpha） |
| --color-border-secondary | hover 边框（0.3 alpha） |
| --font-sans | 默认字体 |
| --font-mono | 代码字体 |
| --radius-md / --radius-lg / --radius-xl | 8px / 12px / 16px |

### 色阶（9 组色阶，自动适配浅/深色）

每个色阶都提供填充、描边和文本变体，并通过 CSS 类自动适配主题。

| Ramp | 50 (light fill) | 200 | 400 | 600 (light stroke) | 800 (light title) |
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

### 图表数据集颜色（使用 400 档）

| Series | Color | Hex |
|--------|-------|-----|
| 1 | teal-400 | #1D9E75 |
| 2 | purple-400 | #7F77DD |
| 3 | coral-400 | #D85A30 |
| 4 | blue-400 | #378ADD |
| 5 | amber-400 | #BA7517 |

对于面积/折线填充，使用相同颜色并设置 20% 透明度。

---

## SVG 设置

如果你要构建会在聊天中渲染的漂亮 SVG，也要遵守这些规则：
始终使用这个 SVG 样板：

<svg width="100%" viewBox="0 0 680 H">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
      markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke"
        stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>
</svg>

- viewBox 宽度**始终为 680**，将 H 设置为**紧密贴合**内容（最后一个元素底部 + 40px）。**绝不要过大**，计算最后一个 SVG 元素的实际底部并加 40px。如果内容在 y=180 结束，H 应为 220，而不是 500
- 安全区域：x=40 到 x=640
- 背景透明，宿主提供容器

### SVG 类（自动注入）

把这些类放在 SVG 元素上，而不是手写 inline fill、stroke 或 font-size。它们会自动跟随主题。

| Class | 它是什么 | 何时使用 |
|-------|----------|----------|
| .t | 14px primary-color text | 节点、轴刻度或 callout 内任何可见标签的默认选择。 |
| .ts | 12px secondary-color text | 副标题、说明、单位（如 "users"、"ms"），以及 .t 标签下方的辅助文本。 |
| .th | 14px primary text，500 weight | 节点标题、KPI 数字，以及任何需要读作小区域“标题”的内容。 |
| .box | 中性 rect：secondary bg、tertiary border | 有标签区域的默认容器。需要中性 chip/panel 且没有语义颜色时使用。 |
| .node | cursor-pointer + <g> 上的 hover opacity | 将 <g> 标记为可点击。配合 onclick="sendPrompt(...)" 让用户深入探索主题。 |
| .arr | 1.5px stroke，匹配主题边框 | 箭头线和连接线。与 marker-end="url(#arrow)" 组合使用。 |
| .leader | 0.5px 虚线 guide line | 当标签不能直接放在图形上时，将标签引到图示某一部分。 |
| .c-{ramp} | 在整个 <g> 上设置 9 个色阶之一的 fill/stroke + 文本颜色 | 按类别给节点上色。把 .c-teal 等应用在 <g> 上，里面每个 shape 和 text 都会获得匹配色阶。 |

### 盒子内文本尺寸

浏览器不会根据文本自动调整 SVG 盒子大小。选择宽度时，按每个字符的渲染字形宽度估算，并根据最长行设置盒子宽度。

- 14px 文本（.t、.th）→ 每字符约 8 px
- 12px 文本（.ts）→ 每字符约 7 px
- box_width = max(title_chars × 8, subtitle_chars × 7) + 24（两侧各 12 px padding）

### 盒子内文本居中

<text> 默认 dominant-baseline="alphabetic"，也就是 y 表示文本 baseline，而不是中心。因此，如果把标签放在盒子的垂直中点，它实际上会高出约 4 px，看起来没对齐。对于节点、callout 或任何圆角矩形内的文本，请添加 dominant-baseline="central"，并把 y 放在盒子中点。

对于**本来就应该坐在 baseline 上**的文本，保留默认值（不要设置 dominant-baseline）：轴刻度标签（贴在轴线上）、图例标签（与色块 baseline 对齐），以及任何以字形底边作为视觉锚点的内容。给这些设置 central 会让它们看起来低约 4 px。

---

## 图示类型

### Flowchart：顺序步骤、决策

- 每张图最多 **4–5 个节点**，6 个以上就拆成概览 + 子流程
- 盒子间距：盒子之间 60px，内部 padding 24px
- 单行节点：高度 44px；双行节点：高度 56px
- 箭头不得穿过任何盒子，需要时使用 L 形折线
- 箭头路径使用 marker-end="url(#arrow)"

单行节点：

<g class="node c-teal" onclick="sendPrompt('Tell me about X')">
  <rect x="100" y="20" width="180" height="44" rx="8"/>
  <text class="th" x="190" y="42" text-anchor="middle" dominant-baseline="central">Label</text>
</g>

双行节点：

<g class="node c-teal">
  <rect x="100" y="20" width="200" height="56" rx="8"/>
  <text class="th" x="200" y="38" text-anchor="middle" dominant-baseline="central">Title</text>
  <text class="ts" x="200" y="56" text-anchor="middle" dominant-baseline="central">Subtitle</text>
</g>

### Architecture：嵌套区域、分层系统

用于展示**什么包含什么**的图示：zone 里的 service、layer 里的 module、subsystem 里的 component。嵌套本身就是信息：外层区域是系统，内层区域是组成部分。

- 最外层容器：rx=20–24，最浅色阶填充（50 档），0.5px 描边
- 内部区域：rx=8–12，同一色阶更深一档；当内部区域语义明显不同（如内部 cluster 中的 external service）时使用不同色阶
- 内部区域边界与父级边缘之间至少 20px padding
- 最多 2–3 层嵌套，超过就拆成顶层概览加子图

### Illustrative：通过绘制机制来解释

适用于答案具有空间性的 “how does this actually work” 主题：光如何通过棱镜折射，transformer attention head 如何给 token 加权，热泵如何逆梯度搬运热量。**画出事物本身**，不要只是画一个关于它的带标签图。

- 形状可以自由：path、ellipse、polygon、curve，不只是圆角矩形
- 颜色表示强度或状态，而不是类别：暖色色阶表示 active / hot / energized，冷色色阶表示 calm / cold / passive，gray 表示 neutral / inert
- 标签放在对象外部，通过 .leader 线连接。在哪侧标注，就预留约 140px gutter
- 强烈优先使用**交互式**说明图：如果真实系统有旋钮、滑块或阶段，就暴露出来。带可拖动角度滑块的棱镜比五张静态帧更能解释折射。

---

## 图表（Chart.js）

在 HTML fragment 中加载 Chart.js：

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>

设置模式：

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

**图表规则：**
- 用 position: relative 和明确高度的容器包裹 canvas。否则 maintainAspectRatio: false 会让 canvas 折叠成 0
- 始终在 options 中传入 responsive: true、maintainAspectRatio: false。如果没有 maintainAspectRatio: false，Chart.js 会把 canvas 锁定为 2:1 宽高比并忽略容器高度；如果没有 responsive: true，iframe 重新测量时不会重绘。每次 new Chart(...) 都必须显式设置它们（Chart.js 在构造时读取 options，所以没有可预设的全局默认值）
- 从 CSS 变量读取文本/边框颜色，让图表跟随主题
- 柱状图设置 borderRadius: 4
- 折线图设置 tension: 0.3 得到平滑曲线
- Doughnut 使用 cutout: '60%'，不要使用 pie

**图表类型选择：**

| 数据形态 | 类型 | 说明 |
|----------|------|------|
| 分类 + 数值（少量项目，可比较量级） | **Bar** | “跨标签比较数值”的默认选择。当标签较长、类别 8+、或排序本身是重点时，切换到横向柱状图（indexAxis: 'y'）。 |
| 时间序列，任何按固定间隔采样的数据 | **Line** | 使用 tension: 0.3 获得自然曲线。比较趋势时可以堆叠多个 dataset；如果每条线独立乱走，不要堆叠，超过 4 条会难读。 |
| 整体的组成部分，≤5 个切片 | **Doughnut** | 使用 cutout: '60%'，让空心中间可以放总数或标签。如果分段非常不均（一片 >70%）则跳过，较小切片会消失；改用 stacked bar。 |
| 两个连续变量，寻找相关性 | **Scatter** | 如果关系是重点，添加趋势线。密集点云把点透明度降到 0.3–0.5，让密度可读。 |
| 随时间的堆叠/累计组成 | **Stacked bar / stacked area** | bucket 离散时用 bar（月、segment）；底层信号连续时用 area。 |
| 单值 vs 目标/阈值 | **带参考线的 Bar** 或 KPI card | 一个数字用整张图过重，考虑指标卡配 sparkline。 |
| 多维比较（3–6 个轴） | **Radar** | 仅当各轴确实可相互比较时使用，否则 small-multiples bar grid 更清楚。 |

### 内联 SVG 图表（无需库）

当数据较小、形状简单，或你希望图表与周围图示共享设计（匹配圆角、调色板、字体）时使用 inline SVG。无需脚本、无需 CDN，只有形状和文本。
当你需要坐标轴、tooltip、hover、动画或多 series 时，使用 Chart.js。

**适合 inline SVG 的场景：**
- **Progress / completion bar**：在固定 track 上渲染数值，通常右侧配百分比标签
- **Ranking strip**：少量水平条垂直堆叠，每个条用不同类别颜色，并按值缩放
- **Sparkline**：无轴的简洁趋势线，放在数字旁边给数字提供上下文
- **KPI donut / ring**：用圆弧表示单个百分比，数字放在环中间
- **Stacked composition row**：一个横向条拆成彩色 segment 展示整体组成，当 doughnut 显得太重时使用
- **Custom-shape charts**：任何图形本身是隐喻一部分的图表（温度计表示温度、电池表示电量、燃油表、潮位线）

**inline SVG 的主题一致性：**
- 在 <text> 上使用 .t / .ts / .th 类表示标签、说明和标题。它们会自动获得主题文本颜色和字体比例。除非需要特定偏离，否则不要手动设置 label text 的 font-size 或 fill。
- 对于中性背景（progress bar 后方 track、ring 中空槽位），使用 fill="var(--color-bg-secondary)"，让它融入周围卡片。
- 对于数据颜色，优先使用上表中的 chart-dataset 400-stop hex，它们经过校准，在浅色和深色背景上都可读。
  如果需要给**整个 group** 重新着色（rect + label + stroke 一起），把它包在 <g class="c-teal">（或 9 个色阶类之一）里，让 SVG 类系统一次性处理 fill + stroke + text。
- chrome（轴线、网格）stroke-width 保持 0.5 px，数据（线、sparkline）保持 1.5 px，匹配宿主 UI 其他 0.5 px 边框，避免图表比邻近内容显得更粗。
- 数据填充加 opacity="0.85"，稍微软化颜色，让它与文本相邻时不过于压迫。

**不太直观形状的数学提示：**
- Donut arc 长度：circumference = 2 × π × r。要绘制 v% 的环，在前景 circle 上设置 stroke-dasharray="{v×circumference/100} {circumference}"，并设置 transform="rotate(-90 cx cy)"，让弧从 12 点钟方向开始，而不是 3 点钟方向。
- viewBox="0 0 680 …" 中的 bar 宽度：左右各留 40 px margin，可用绘图区宽度为 600 px。

---

## 组件模式

### Metric cards：KPI 条

<div style="display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px;">
  <div style="background:var(--color-bg-secondary); border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--radius-lg); padding:16px;">
    <div style="font-size:12px; color:var(--color-text-secondary);">Revenue</div>
    <div style="font-size:28px; font-weight:500; color:var(--color-text-primary); margin-top:4px;">$3,870</div>
    <div style="font-size:12px; color:var(--color-text-success); margin-top:2px;">▲ 12.4%</div>
  </div>
  <!-- repeat for other metrics -->
</div>

下方配一张图表即可形成紧凑 dashboard。如果趋势很重要，在每个值下面添加一个 tiny inline-SVG sparkline。

### Comparison layout：并排两条路径

<div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
  <div style="background:var(--color-bg-secondary); border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--radius-lg); padding:18px;">
    <div style="font-size:14px; font-weight:500;">Monolith</div>
    <dl data-layout="grid" style="margin-top:12px;">
      <dt>Deploy unit</dt><dd>1 service</dd>
      <dt>Latency</dt><dd>Low (in-process)</dd>
      <dt>Scaling</dt><dd>Vertical</dd>
    </dl>
  </div>
  <div style="background:var(--color-bg-secondary); border:0.5px solid var(--color-border-tertiary);
    border-radius:var(--radius-lg); padding:18px;">
    <div style="font-size:14px; font-weight:500;">Microservices</div>
    <dl data-layout="grid" style="margin-top:12px;">
      <dt>Deploy unit</dt><dd>N services</dd>
      <dt>Latency</dt><dd>Higher (network)</dd>
      <dt>Scaling</dt><dd>Horizontal per service</dd>
    </dl>
  </div>
</div>

### Interactive explainer：滑块驱动输出

<label style="display:flex; gap:12px; align-items:center;">
  <span style="min-width:80px;">Interest</span>
  <input type="range" id="rate" min="0" max="20" step="0.1" value="5" style="flex:1;">
  <span id="rate-out" style="min-width:48px; font-variant-numeric:tabular-nums;">5.0%</span>
</label>
<div id="result" style="margin-top:12px; font-size:24px; font-weight:500;"></div>

<script>
var rate = document.getElementById('rate');
var out = document.getElementById('rate-out');
var result = document.getElementById('result');
function recalc() {
  var r = parseFloat(rate.value);
  out.textContent = r.toFixed(1) + '%';
  result.textContent = '$' + (10000 * Math.pow(1 + r/100, 10)).toFixed(0);
}
rate.addEventListener('input', recalc);
recalc();
</script>

该模式可以泛化：每个交互元素绑定 input listener，重新计算值，并写入结果节点。
配合每次输入变化都重绘的 inline SVG，就能形成 “live diagram”。

### Tabs：用户已经熟悉的 UI


<div style="display:flex; gap:4px; border-bottom:0.5px solid var(--color-border-tertiary);">
  <button class="tab active" onclick="showTab('a', this)">Overview</button>
  <button class="tab" onclick="showTab('b', this)">Details</button>
  <button class="tab" onclick="showTab('c', this)">Source</button>
</div>
<div id="tab-a" class="tab-panel">…</div>
<div id="tab-b" class="tab-panel" hidden>…</div>
<div id="tab-c" class="tab-panel" hidden>…</div>

<style>
  .tab { background:none; border:none; padding:8px 12px; cursor:pointer;
         border-bottom:2px solid transparent; }
  .tab.active { border-bottom-color: var(--accent); color: var(--color-text-primary); }
  .tab-panel { padding:12px 0; }
</style>

<script>
function showTab(id, btn) {
  document.querySelectorAll('.tab-panel').forEach(p => p.hidden = true);
  document.getElementById('tab-' + id).hidden = false;
  document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}
</script>

用 saveState/loadState 持久化 active tab，让它在 reload 后保持。

**非活动 tab 中的图表会以 0×0 渲染。** Plotly、ECharts 和 vis-network 都会在初始化时测量容器。
如果容器位于 hidden / display:none panel 中，它们会画进零尺寸 canvas，即使之后 tab 变为可见也保持空白。
两个解决方案，选一个：

1. **Lazy-init**：只在某个 tab 第一次显示时调用 Plotly.newPlot / echarts.init / new vis.Network（在 handler 中维护 tabInit[id] 标记）。
2. **Resize on show**：提前初始化所有内容（数据已准备好），然后在 showTab 中为该 tab 里的库调用正确 resize hook。
   注意每个库 API 不同，c.resize() 并不是对所有库都有效：

   // ECharts: instance.resize()
   echartsInstance.resize();
   // Plotly: pass the container element, no .resize() on the chart
   Plotly.Plots.resize(document.getElementById('plotly-container'));
   // vis-network: redraw + fit — the instance has no .resize()
   networkInstance.redraw();
   networkInstance.fit();
   // Chart.js: instance.resize() — but Chart.js auto-resizes on
   // container size change so usually nothing needed.

   对 D3 / Vega-Lite / inline SVG 跳过 resize 调用，它们声明式地绘制进 SVG namespace，不受 hidden parent 困扰。

### Step-through walkthrough：引导式叙事
“Next ▶” 按钮推进一系列阶段，每个阶段都有自己的说明文字，并且可以高亮同一图中的不同区域。
适合解释算法、流程，或任何顺序比总量更重要的主题。


<div id="stage" style="font-size:14px;">Click Next to begin.</div>
<button onclick="step()">Next ▶</button>

<script>
var steps = [
  'Step 1: request lands at the load balancer',
  'Step 2: routed to a healthy backend',
  'Step 3: backend writes to primary DB',
  'Step 4: replica catches up async',
];
var i = 0;
function step() {
  document.getElementById('stage').textContent = steps[i % steps.length];
  i++;
}
</script>

---

## sendPrompt bridge：可对话图示

sendPrompt(text) 是让可视化具备对话能力的函数。调用时，它会把给定文本注入聊天输入框并提交，就像用户自己输入并发送一样。模型随后会收到该消息并正常回复，在视觉内容和对话之间形成反馈循环。

这正是静态图和**探索界面**之间的区别。用户看到系统架构图，点击 "Load Balancer" 节点，模型会收到 "Tell me more about the load balancer — how does it distribute traffic across the backend services?" 作为用户消息。模型随后回复细节，甚至可以生成一个*新的*子图展示负载均衡器内部结构。用户不用打字，只需点击。

### 为什么重要

没有 sendPrompt 时，iframe 内的交互元素是隔离的：它们可以切换可见性、播放动画或过滤数据，但永远无法把信息传回模型。用户看到一个很酷的图，但必须手动输入追问。有了 sendPrompt，每个可点击元素都成为对话入口。图示本身变成了该主题的导航界面。

### 编写好的 sendPrompt 文本

传给 sendPrompt 的文本会成为用户发给模型的消息。把它写成自然的追问：对话式、具体，并引用图中的上下文：

**好的 prompt 文本**（具体、有上下文、引用图示）：
- "Explain the attention mechanism — how does it decide which tokens to focus on?"
- "Break down the CI/CD pipeline stage. What tools are typically used here?"
- "Show me a more detailed diagram of the data processing layer"
- "What happens when the load balancer detects a failed backend node?"
- "Compare the pros and cons of the monolith vs microservices approach shown here"

### 使用模式

简单模式：在节点或按钮上单击触发 sendPrompt：
- **Drill-down**：在图示节点上使用 onclick="sendPrompt('Explain the API gateway — what does it handle?')"
- **Quiz answer**：在答案按钮上使用 onclick="sendPrompt('I chose B: O(n log n). Am I right? Explain why.')"
- **Guided exploration**：在 "Go deeper →" 按钮上使用 onclick="sendPrompt('Show me a more advanced example with edge cases.')"
- **Comparison**：在两个节点之一上使用 onclick="sendPrompt('Compare REST vs GraphQL — when should I use each?')"

**表单 / 偏好收集器**：收集多个用户选择，然后一次性发送。使用本地 JS 跟踪选择（按钮高亮、状态对象），再用提交按钮根据收集到的答案组合 sendPrompt：

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

这个模式很强大，因为模型会在一条消息中收到所有用户偏好的结构化摘要。选择 UI 使用本地 JS（即时反馈），只在最终提交时调用 sendPrompt。

### 什么时候使用 sendPrompt，什么时候使用本地 JS：
| 用户操作 | 使用 | 原因 |
|----------|------|------|
| 了解某个组件的更多信息 | sendPrompt | 模型给出上下文解释 |
| 探索某个阶段 / 深入展开 | sendPrompt | 模型可以生成子图 |
| 提交答案或偏好 | sendPrompt | 模型可以评估或个性化 |
| 切换视图、调整滑块 | 本地 JS | 即时反馈，不需要推理 |
| 过滤/排序数据 | 本地 JS | 即时响应，不需要模型 |

---

## 默认交互性

构建 dashboard、chart、graph、interactive function、animated section、moving object、expandable detail section、card、copyable text element 等。如果主题允许并且适合，就构建复杂且视觉上出色的元素。

可视化应该有生命力并且完成度高，而不是丢进聊天里的静态图片。构建能邀请用户互动的界面：

- **可展开区域**：使用可折叠 <details> 元素或 JS 切换区块，让用户按自己的节奏探索，而不是一开始就被大量信息压倒
- **Hover 效果**：节点、按钮和卡片都应响应 hover（.node 类为 SVG 元素添加该效果；HTML 使用 :hover 样式）
- **平滑过渡**：为交互元素添加 transition: all 0.2s ease，让体验更精致
- **Active 状态**：当用户选择选项或点击 tab 时，用 .active 类或独特样式清晰显示当前选择
- **渐进披露**：先展示清晰概览，再让用户点击显示细节（tabs、accordions，或通过 sendPrompt 做模型驱动 drill-down）

**目标是构建一个嵌入聊天中的真实 app component，带有 reactivity、sections 和额外元素**，而不是截图。如果可视化有多个方面，就给用户控件去探索。如果它有层级信息，就让用户展开和折叠。如果它有数据，就让用户排序或过滤。

---

## openLink bridge：从可视化打开 URL

openLink(url) 会从可视化 iframe 内部在新浏览器标签页打开 URL。iframe 内普通 <a href="..."> 链接的行为可能不可预测（在 iframe 内打开、被 sandbox 限制阻止等）。该函数通过在父窗口中打开链接来处理。

<button onclick="openLink('https://docs.example.com/api-reference')">
  Open API docs ↗
</button>

或在 SVG 中：

<g class="node c-blue" onclick="openLink('https://github.com/org/repo')">
  <rect x="100" y="20" width="200" height="44" rx="8"/>
  <text class="th" x="200" y="42" text-anchor="middle" dominant-baseline="central">View source ↗</text>
</g>

将 openLink 用于外部参考、文档链接或源码链接。不同于 sendPrompt，它会离开聊天。用户需要访问外部资源时使用它；需要模型解释某事时不要使用它。

---

## copyText + toast bridges：用户操作反馈

copyText(text) 会把文本复制到系统剪贴板，并自动在 iframe 右上角显示本地化 "Copied" toast。支持 HTTPS 和 HTTP origin（如果异步 Clipboard API 被阻止，则回退到 execCommand('copy')）。在交互式可视化中的 “Copy” 按钮上使用它，如数据表、代码片段、可分享数值。

<button onclick="copyText(JSON.stringify(data, null, 2))">Copy JSON</button>

toast(message, kind) 会在 iframe 内显示一个自动消失的小横幅。kind 是可选参数，控制文本颜色：'success'（绿色，默认）、'info'（蓝色）、'warn'（琥珀色）、'error'（红色）。用于长时间运行的交互式工具内部状态提示，如 "Calculation done"、"Invalid input" 等。

<button onclick="recompute(); toast('Recomputed', 'info')">Recompute</button>

Toasts 约 2.2 秒后自动消失，如果短时间连续触发，会垂直堆叠。

---

## saveState + loadState bridges：持久化交互状态

saveState(key, value) 和 loadState(key, fallback) 会代理 parent.localStorage，并用**当前 assistant message** 作用域的 key prefix。状态会在页面刷新和 tab 切换后保留，但不同聊天（或同一聊天中的不同消息）各自拥有独立状态，不会互相污染。

<script>
  // Restore toggle state on load
  var showRaw = loadState('showRaw', false);
  document.getElementById('raw-toggle').checked = showRaw;
  applyView(showRaw);

  function onToggleChange(el) {
    saveState('showRaw', el.checked);
    applyView(el.checked);
  }
</script>

用于：选中的 tab、选择的图表范围、隐藏/显示的图层、主题覆盖、折叠区块，任何用户重新打开聊天时希望被记住的东西。

值会被 JSON 序列化。如果 localStorage 被阻止（私密浏览、sandbox），两个函数都会静默 no-op，loadState 返回 fallback。

---

## CDN libraries

Strict-mode CSP 允许三个 CDN host。来自它们的任何资源都能加载，即使在 strict security mode 下也不需要调整插件。

允许的 hosts：
- cdnjs.cloudflare.com：覆盖最广
- cdn.jsdelivr.net：基于 npm / GitHub，支持 minor-version pinning
- unpkg.com：npm mirror

常用选择：

| Library | 为什么使用 | 示例 loader |
|---------|------------|-------------|
| **Chart.js** | 开箱即用的 bar / line / doughnut / scatter 和动画 | <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script> |
| **D3.js** | 自定义数据驱动 SVG（force graph、arc、map、非标准图表） | <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script> |
| **Vega-Lite** | 声明式图形语法，给它 JSON spec，它负责绘图 | <script src="https://cdn.jsdelivr.net/npm/vega@5"></script><script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script><script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script> |
| **ECharts** | 丰富交互式 dashboard，高级图表类型 | <script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script> |
| **Plotly** | 科学 / 3D plot、统计图表 | <script src="https://cdn.jsdelivr.net/npm/plotly.js-dist@2"></script> |
| **vis-network** | Force-directed network / node-link graph | <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>（**standalone** UMD bundle，会暴露 vis.Network *和* vis.DataSet。cdnjs 上裸的 vis-network.min.js 是 *peer* build，需要另行加载 vis-data，否则 new vis.DataSet(...) 会抛出 vis is not defined。） |
| **Tone.js / Wavesurfer** | 音频合成、波形可视化 | <script src="https://cdnjs.cloudflare.com/ajax/libs/tone/15.0.4/Tone.js"></script> |

这三个 CDN 上的其他库也可以使用，如 apexcharts、d3-force、konva、flatpickr 等。选择最适合主题的库。

---

## Library init

使用 CDN library 时遵循两个模式：

### 1 · 用固定高度容器包裹 Chart.js canvas

maintainAspectRatio: false 会让 Chart.js 使用容器高度。
如果 canvas 没有内在高度（例如位于未设置高度的 flex column 内），它会折叠为 0，什么也画不出来：

<div style="position: relative; height: 260px;">
  <canvas id="chart"></canvas>
</div>
<script>
  new Chart(document.getElementById('chart').getContext('2d'), {
    type: 'bar',
    data: { /* … */ },
    options: { responsive: true, maintainAspectRatio: false, /* … */ }
  });
</script>

### 2 · Source order matters

把外部 <script src="…"> 标签放在使用它们的 inline <script> **之前**。
它们会按顺序执行，所以如果 consumer 在 library 加载前运行，会因 Chart is not defined 而失败。

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>/* uses Chart and d3 */</script>
