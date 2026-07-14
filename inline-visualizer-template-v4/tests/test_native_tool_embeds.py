import asyncio
import inspect
import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))

from test_dashboard_table import load_tool_module


class NativeToolEmbedDeliveryTest(unittest.TestCase):
    def test_render_functions_do_not_accept_message_embed_state(self):
        module = load_tool_module()

        for name in (
            "render_data_detail",
            "render_chart",
            "render_dashboard",
            "render_analysis_dashboard",
        ):
            parameters = inspect.signature(getattr(module.Tools, name)).parameters
            self.assertNotIn("__event_emitter__", parameters)
            self.assertNotIn("__metadata__", parameters)

    def test_detail_and_chart_return_independent_inline_html_responses(self):
        module = load_tool_module()
        tool = module.Tools()

        async def render_both():
            detail = await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
            )
            chart = await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
            )
            return detail, chart

        detail, chart = asyncio.run(render_both())

        for result, template in ((detail, "data_detail"), (chart, "chart")):
            response, context = result
            self.assertIn("inline", response.headers["Content-Disposition"])
            self.assertIn(b"<!DOCTYPE html>", response.body)
            self.assertIn(f'"template":"{template}"'.encode(), response.body)
            self.assertIn("rendered with 1 entries", context)

        self.assertIsNot(detail[0], chart[0])

    def test_validation_error_remains_plain_text(self):
        module = load_tool_module()
        result = asyncio.run(module.Tools().render_chart(series=[]))

        self.assertTrue(result.startswith("Error:"))

    def test_embed_html_survives_open_webui_attribute_entity_decode(self):
        module = load_tool_module()
        response, _ = asyncio.run(
            module.Tools().render_chart(
                series=[{"label": "A &quot;quoted&quot; value", "value": 1}],
                title='Load "detail"',
            )
        )
        content = response.body.decode("utf-8")

        # Open WebUI v0.10.2 decodes HTML entities on the complete serialized
        # embeds attribute before JSON.parse. A literal &quot; therefore becomes
        # an unescaped quote and makes the embeds array unparsable.
        self.assertNotIn("&quot;", content)

        payload_match = re.search(
            r'<script id="payload" type="application/json">(.*?)</script>',
            content,
            re.DOTALL,
        )
        self.assertIsNotNone(payload_match)
        payload = json.loads(payload_match.group(1))
        self.assertEqual(payload["title"], 'Load "detail"')
        self.assertEqual(
            payload["data"]["series"][0]["label"],
            "A &quot;quoted&quot; value",
        )


if __name__ == "__main__":
    unittest.main()
