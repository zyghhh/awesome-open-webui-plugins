"""
title: MCP App Bridge
author: Classic298
version: 0.2.0
description: Proof of concept — wraps MCP server tools and renders MCP App UI resources (ui://) as Rich UI embeds using Open WebUI's existing embed system. Honors server-declared CSP and permissions per the MCP Apps spec. No middleware changes needed.
"""

import json
from typing import Literal
from contextlib import AsyncExitStack

from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_dict(obj) -> dict:
    """Convert an MCP SDK model or dict to a plain dict."""
    if obj is None:
        return {}
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if isinstance(obj, dict):
        return obj
    return {}


def _extract_ui_resource_uri(tool) -> str | None:
    """Extract ui:// resource URI from tool metadata, if present."""
    meta_dict = _to_dict(getattr(tool, "meta", None))
    if not meta_dict:
        return None

    # Nested format: _meta.ui.resourceUri
    ui_meta = meta_dict.get("ui", {})
    if isinstance(ui_meta, dict):
        uri = ui_meta.get("resourceUri", "")
        if isinstance(uri, str) and uri.startswith("ui://"):
            return uri

    # Flat format: _meta["ui/resourceUri"]
    flat_uri = meta_dict.get("ui/resourceUri", "")
    if isinstance(flat_uri, str) and flat_uri.startswith("ui://"):
        return flat_uri

    return None


def _extract_tool_result_text(call_result) -> str:
    """Extract text content from an MCP call_tool result."""
    if not call_result or not getattr(call_result, "content", None):
        return ""
    parts = []
    for item in call_result.content:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


def _build_csp_meta_tag(csp: dict) -> str:
    """Build a <meta> CSP tag from a server-declared _meta.ui.csp object.

    Per the MCP Apps spec (SEP-1865), the csp object has:
      connectDomains   -> connect-src
      resourceDomains  -> script-src, style-src, img-src, font-src, media-src
      frameDomains     -> frame-src
      baseUriDomains   -> base-uri
    """
    if not csp:
        # Restrictive default per spec: block all outbound, allow inline scripts/styles
        return (
            '<meta http-equiv="Content-Security-Policy" content="'
            "default-src 'none'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "media-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'none'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
            '">\n'
        )

    resource_domains = " ".join(csp.get("resourceDomains") or [])
    connect_domains = " ".join(csp.get("connectDomains") or [])
    frame_domains = " ".join(csp.get("frameDomains") or [])
    base_uri_domains = " ".join(csp.get("baseUriDomains") or [])

    rd = f" {resource_domains}" if resource_domains else ""
    cd = f" {connect_domains}" if connect_domains else " 'none'"
    fd = f" {frame_domains}" if frame_domains else " 'none'"
    bd = f" {base_uri_domains}" if base_uri_domains else " 'self'"

    policy = (
        f"default-src 'none'; "
        f"script-src 'self' 'unsafe-inline'{rd}; "
        f"style-src 'self' 'unsafe-inline'{rd}; "
        f"img-src 'self' data:{rd}; "
        f"font-src 'self'{rd}; "
        f"media-src 'self' data:{rd}; "
        f"connect-src{cd}; "
        f"frame-src{fd}; "
        f"object-src 'none'; "
        f"base-uri{bd}"
    )
    return f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n'


def _get_resource_ui_meta(resources_list, uri: str) -> dict:
    """Find a resource in the listing by URI and return its _meta.ui dict."""
    for res in resources_list:
        res_dict = _to_dict(res)
        res_uri = str(res_dict.get("uri", ""))
        if res_uri == uri:
            meta = _to_dict(res_dict.get("meta"))
            return meta.get("ui", {}) if isinstance(meta, dict) else {}
    return {}


async def _connect_mcp(url: str, headers: dict | None) -> tuple[AsyncExitStack, ClientSession]:
    """Open a streamable-HTTP MCP connection. Caller owns the returned stack."""
    stack = AsyncExitStack()
    try:
        transport = await stack.enter_async_context(
            streamablehttp_client(url, headers=headers)
        )
        read_stream, write_stream, _ = transport
        session = await stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        await session.initialize()
        return stack, session
    except Exception:
        await stack.aclose()
        raise


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------


class Tools:
    """MCP App Bridge — renders MCP App UI resources as Rich UI embeds.

    Configure the MCP server URL and optional auth token via Valves,
    then the model can discover and call MCP tools. If a tool declares
    a ``ui://`` resource, the HTML is fetched and rendered inline.

    Security: honors server-declared CSP (``_meta.ui.csp``) and
    permissions (``_meta.ui.permissions``) per the MCP Apps spec.
    """

    class Valves(BaseModel):
        mcp_server_url: str = Field(
            default="",
            description="Streamable-HTTP URL of the MCP server.",
        )
        auth_token: str = Field(
            default="",
            description="Bearer token for MCP server authentication (optional).",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _build_headers(self) -> dict | None:
        if not self.valves.auth_token:
            return None
        return {"Authorization": f"Bearer {self.valves.auth_token}"}

    async def list_mcp_tools(self) -> str:
        """
        List all tools available on the configured MCP server.
        Shows name, description, and whether each tool has a UI resource.

        :return: JSON list of available tools with their metadata.
        """
        stack, session = await _connect_mcp(
            self.valves.mcp_server_url, self._build_headers()
        )
        try:
            result = await session.list_tools()
            tools = []
            for tool in result.tools:
                ui_uri = _extract_ui_resource_uri(tool)
                tools.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "",
                        "has_ui": ui_uri is not None,
                        "parameters": tool.inputSchema,
                    }
                )
            return json.dumps(tools, indent=2, ensure_ascii=False)
        finally:
            await stack.aclose()

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: str = "{}",
    ) -> str | HTMLResponse:
        """
        Call a tool on the configured MCP server.

        If the tool declares a UI resource (MCP Apps extension, ui:// URI),
        the HTML is fetched and rendered inline as a Rich UI embed —
        exactly like the Inline Visualizer renders its output.

        Security is enforced via the server's declared CSP policy, which is
        injected as a <meta> Content-Security-Policy tag per the MCP Apps spec.

        If the tool has no UI resource, returns the plain text result.

        :param tool_name: Name of the MCP tool to call.
        :param arguments: JSON string of tool arguments.
        :return: Rich UI embed with the MCP App HTML, or plain text result.
        """
        args = json.loads(arguments) if isinstance(arguments, str) else arguments

        stack, session = await _connect_mcp(
            self.valves.mcp_server_url, self._build_headers()
        )
        try:
            # --- Find the tool and check for UI resource ---
            tools_result = await session.list_tools()
            ui_resource_uri = None

            for tool in tools_result.tools:
                if tool.name == tool_name:
                    ui_resource_uri = _extract_ui_resource_uri(tool)
                    break

            # --- Call the tool ---
            call_result = await session.call_tool(tool_name, args)
            result_text = _extract_tool_result_text(call_result)

            # --- If no UI resource, return plain text ---
            if not ui_resource_uri:
                return result_text or "Tool executed (no output)."

            # --- Fetch resource listing for CSP/permissions metadata ---
            resources_result = await session.list_resources()
            resources_list = (
                resources_result.resources
                if resources_result and hasattr(resources_result, "resources")
                else []
            )
            ui_meta = _get_resource_ui_meta(resources_list, ui_resource_uri)
            csp_data = ui_meta.get("csp") if isinstance(ui_meta, dict) else None

            # --- Fetch the UI resource content ---
            resource_result = await session.read_resource(ui_resource_uri)
            html_content = ""
            if resource_result and getattr(resource_result, "contents", None):
                for item in resource_result.contents:
                    text = getattr(item, "text", None)
                    if text:
                        html_content = text
                        break

            if not html_content:
                return result_text or "Tool executed (UI resource was empty)."

            # --- Build injection: CSP + tool data + auto-height ---
            csp_tag = _build_csp_meta_tag(csp_data)

            data_script = (
                "<script>\n"
                f"  window.__MCP_TOOL_RESULT__ = {json.dumps(result_text)};\n"
                f"  window.__MCP_TOOL_ARGS__   = {json.dumps(args, ensure_ascii=False)};\n"
                f"  window.__MCP_TOOL_NAME__   = {json.dumps(tool_name)};\n"
                "</script>\n"
            )

            height_script = (
                "<script>\n"
                "function reportHeight(){\n"
                "  var h=document.documentElement.scrollHeight;\n"
                "  window.parent.postMessage({type:'iframe:height',height:h},'*');\n"
                "}\n"
                "window.addEventListener('load',function(){reportHeight();setTimeout(reportHeight,200)});\n"
                "new MutationObserver(reportHeight).observe(document.body,{childList:true,subtree:true});\n"
                "window.addEventListener('resize',reportHeight);\n"
                "</script>\n"
            )

            injection = csp_tag + data_script + height_script

            if "<head>" in html_content:
                html_content = html_content.replace("<head>", "<head>\n" + injection, 1)
            elif "<html>" in html_content:
                html_content = html_content.replace(
                    "<html>", "<html>\n<head>" + injection + "</head>", 1
                )
            else:
                html_content = "<head>" + injection + "</head>\n" + html_content

            # --- Return as Rich UI embed ---
            return HTMLResponse(
                content=html_content,
                headers={"Content-Disposition": "inline"},
            )
        finally:
            await stack.aclose()
