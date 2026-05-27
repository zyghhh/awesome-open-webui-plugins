# ✉️ Email Composer

AI-powered email drafting with an interactive Rich UI card embedded directly in chat.

> [!TIP]
> **🚀 [Jump to Setup Guide](#setup)** — get up and running in under 1 minute.

![Preview](assets/preview.png)

## Features

- Rich text editing with formatting toolbar (bold, italic, underline, headings, lists)
- To / CC / BCC address chips with keyboard shortcuts
- Priority badges (high / normal / low)
- Copy body as rich text
- Download as `.eml` file
- One-click send via `mailto:`
- Autosave (requires *Allow Iframe Same-Origin Access*)
- Word and character count

## Components

| File | Type | Install location |
|------|------|-----------------|
| `tool.py` | Tool | Workspace → Tools |

## Setup

1. Copy the contents of `tool.py`
2. In Open WebUI, go to **Workspace → Tools → + Create New**
3. Paste the code and click **Save**
4. In Open WebUI, go to **Admin Panel → Settings → Models** and edit your model
5. Under **Tools**, enable the **Email Composer** tool (or enable it in the chat on demand)
6. Ensure native function calling is enabled for your model
7. Save

### Optional

- Enable **iframe Sandbox Allow Same Origin** in Settings → Interface **(for autosave support only - all other features work without it)**

## Usage

Ask your model to compose, write, or draft an email. The tool renders an interactive card where you can edit all fields, then copy, download, or send.
