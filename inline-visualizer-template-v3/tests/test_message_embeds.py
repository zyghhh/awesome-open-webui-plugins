import asyncio
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))

from test_dashboard_table import load_tool_module


class MessageEmbedDeliveryTest(unittest.TestCase):
    def test_render_chart_emits_message_embed_and_returns_context(self):
        module = load_tool_module()
        tool = module.Tools()
        events = []

        async def emit(event):
            events.append(event)

        result = asyncio.run(
            tool.render_chart(
                series=[
                    {"region": "华东电网(整体)", "peak_load": 10442.8},
                    {"region": "上海电网", "peak_load": 3899.8},
                ],
                chart_type="bar",
                title="华东五省一市电网最大负荷日对比",
                __event_emitter__=emit,
            )
        )

        self.assertIsInstance(result, str)
        self.assertIn("Chart (1 series)", result)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["type"], "embeds")
        self.assertFalse(events[0]["data"]["replace"])
        self.assertEqual(len(events[0]["data"]["embeds"]), 1)
        self.assertIn("<!DOCTYPE html>", events[0]["data"]["embeds"][0])
        self.assertIn('"template":"chart"', events[0]["data"]["embeds"][0])

    def test_render_chart_without_emitter_keeps_htmlresponse_tuple(self):
        module = load_tool_module()
        result = asyncio.run(
            module.Tools().render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                chart_type="line",
                title="Monthly Revenue",
            )
        )

        response, context = result
        self.assertIn("inline", response.headers["Content-Disposition"])
        self.assertIn(b"<!DOCTYPE html>", response.body)
        self.assertIn("rendered with 1 entries", context)

    def test_sequential_visualizations_append_message_embeds(self):
        module = load_tool_module()
        tool = module.Tools()
        events = []

        async def emit(event):
            events.append(event)

        async def render_both():
            await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
                __event_emitter__=emit,
            )
            await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
                __event_emitter__=emit,
            )

        asyncio.run(render_both())

        self.assertEqual(len(events), 2)
        self.assertTrue(all(event["type"] == "embeds" for event in events))
        self.assertTrue(all(event["data"]["replace"] is False for event in events))

    def test_validation_error_does_not_emit_embed(self):
        module = load_tool_module()
        events = []

        async def emit(event):
            events.append(event)

        result = asyncio.run(
            module.Tools().render_chart(
                series=[],
                __event_emitter__=emit,
            )
        )

        self.assertTrue(result.startswith("Error:"))
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
