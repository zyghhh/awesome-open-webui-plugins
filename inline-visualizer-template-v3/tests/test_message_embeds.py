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
        self.assertTrue(events[0]["data"]["replace"])
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

    def test_sequential_visualizations_emit_cumulative_message_embeds(self):
        module = load_tool_module()
        tool = module.Tools()
        events = []
        message_embeds = []
        metadata = {}

        async def emit(event):
            nonlocal message_embeds
            events.append(event)
            if event["type"] == "embeds":
                # Open WebUI v0.10.2 assigns the incoming array; it does not
                # append based on the event's `replace` field.
                message_embeds = event["data"]["embeds"]

        async def render_both():
            await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            metadata_after_detail = dict(metadata)
            await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            return metadata_after_detail

        metadata_after_detail = asyncio.run(render_both())

        self.assertEqual(len(events), 2)
        self.assertTrue(all(event["type"] == "embeds" for event in events))
        self.assertEqual(len(events[0]["data"]["embeds"]), 1)
        self.assertEqual(len(events[1]["data"]["embeds"]), 2)
        self.assertIn('"template":"data_detail"', events[1]["data"]["embeds"][0])
        self.assertIn('"template":"chart"', events[1]["data"]["embeds"][1])
        self.assertEqual(message_embeds, events[1]["data"]["embeds"])
        self.assertEqual(len(message_embeds), 2)
        self.assertTrue(metadata_after_detail)
        self.assertEqual(
            set(metadata[module._MESSAGE_EMBEDS_METADATA_KEY]),
            {"data_detail", "visualization"},
        )

    def test_reverse_tool_order_still_emits_detail_before_visualization(self):
        module = load_tool_module()
        tool = module.Tools()
        events = []
        message_embeds = []
        metadata = {}

        async def emit(event):
            nonlocal message_embeds
            events.append(event)
            if event["type"] == "embeds":
                message_embeds = event["data"]["embeds"]

        async def render_in_reverse_order():
            await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            metadata_after_chart = dict(metadata)
            await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            return metadata_after_chart

        metadata_after_chart = asyncio.run(render_in_reverse_order())

        self.assertEqual(len(events), 2)
        self.assertEqual(len(events[0]["data"]["embeds"]), 1)
        self.assertIn('"template":"chart"', events[0]["data"]["embeds"][0])
        self.assertEqual(len(events[1]["data"]["embeds"]), 2)
        self.assertIn('"template":"data_detail"', events[1]["data"]["embeds"][0])
        self.assertIn('"template":"chart"', events[1]["data"]["embeds"][1])
        self.assertEqual(message_embeds, events[1]["data"]["embeds"])
        self.assertTrue(metadata_after_chart)
        self.assertEqual(
            set(metadata[module._MESSAGE_EMBEDS_METADATA_KEY]),
            {"data_detail", "visualization"},
        )

    def test_extra_visualization_keeps_detail_and_replaces_previous_visualization(self):
        module = load_tool_module()
        tool = module.Tools()
        events = []
        metadata = {}

        async def emit(event):
            events.append(event)

        async def render_detail_chart_then_dashboard():
            await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            await tool.render_dashboard(
                metrics=[{"label": "Revenue", "value": "$120"}],
                title="Revenue Dashboard",
                __event_emitter__=emit,
                __metadata__=metadata,
            )

        asyncio.run(render_detail_chart_then_dashboard())

        final_embeds = events[-1]["data"]["embeds"]
        self.assertEqual(len(final_embeds), 2)
        self.assertIn('"template":"data_detail"', final_embeds[0])
        self.assertIn('"template":"dashboard"', final_embeds[1])
        self.assertNotIn('"template":"chart"', final_embeds[1])

    def test_cumulative_events_replace_persisted_embeds_for_reload(self):
        module = load_tool_module()
        tool = module.Tools()
        metadata = {}
        persisted_embeds = []

        async def emit(event):
            nonlocal persisted_embeds
            incoming_embeds = list(event["data"]["embeds"])
            if not event["data"].get("replace", False):
                # Open WebUI v0.10.2 prepends the incoming embeds to the
                # message's persisted embeds when replace is false.
                incoming_embeds.extend(persisted_embeds)
            persisted_embeds = incoming_embeds

        async def render_in_reverse_order():
            await tool.render_chart(
                series=[{"month": "Jan", "revenue": 120}],
                title="Monthly Revenue",
                __event_emitter__=emit,
                __metadata__=metadata,
            )
            await tool.render_data_detail(
                columns=["month", "revenue"],
                rows=[{"month": "Jan", "revenue": 120}],
                title="Sales Data",
                __event_emitter__=emit,
                __metadata__=metadata,
            )

        asyncio.run(render_in_reverse_order())

        self.assertEqual(len(persisted_embeds), 2)
        self.assertIn('"template":"data_detail"', persisted_embeds[0])
        self.assertIn('"template":"chart"', persisted_embeds[1])

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
