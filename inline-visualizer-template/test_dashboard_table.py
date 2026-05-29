import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest


TOOL_PATH = Path(__file__).with_name("tool.py")


def load_tool_module():
    fastapi = types.ModuleType("fastapi")
    fastapi_responses = types.ModuleType("fastapi.responses")

    class HTMLResponse:
        def __init__(self, content="", headers=None):
            self.body = content.encode("utf-8")
            self.headers = headers or {}

    fastapi_responses.HTMLResponse = HTMLResponse
    sys.modules.setdefault("fastapi", fastapi)
    sys.modules.setdefault("fastapi.responses", fastapi_responses)

    pydantic = types.ModuleType("pydantic")

    class BaseModel:
        pass

    def Field(default=None, **_kwargs):
        return default

    pydantic.BaseModel = BaseModel
    pydantic.Field = Field
    sys.modules.setdefault("pydantic", pydantic)

    spec = importlib.util.spec_from_file_location("ivt_tool", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DashboardTableTest(unittest.TestCase):
    def render_chart_html(self, **kwargs):
        module = load_tool_module()
        tool = module.Tools()
        response, _ = asyncio.run(tool.render_chart(**kwargs))
        return response.body.decode("utf-8")

    def render_dashboard_html(self, **kwargs):
        module = load_tool_module()
        tool = module.Tools()
        response, _ = asyncio.run(tool.render_dashboard(**kwargs))
        return response.body.decode("utf-8")

    def test_dashboard_table_chart_type_renders_table_branch(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Revenue", "value": "$120"}],
            series=[
                {"label": "Jan", "value": 120},
                {"label": "Feb", "value": 148},
            ],
            chart_type="table",
            title="Revenue Dashboard",
        )

        self.assertIn('"chartType":"table"', html)
        self.assertIn("if (chartType === 'table')", html)
        self.assertIn("renderDashboardTable(series, dashXCol, dashYCols)", html)
        self.assertNotIn("if (chartType === 'table') { chartType = 'line'; }", html)

    def test_dashboard_multi_series_auto_detects_x_and_y_columns(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Revenue", "value": "$120"}],
            series=[
                {"month": "Jan", "revenue": 120, "users": 500},
                {"month": "Feb", "revenue": 148, "users": 600},
            ],
            chart_type="line",
            title="Revenue Dashboard",
        )

        self.assertIn('"x_column":"month"', html)
        self.assertIn('"y_columns":["revenue","users"]', html)
        self.assertIn('"month":"Jan","revenue":120,"users":500', html)

    def test_dashboard_single_series_keeps_label_value_compatibility(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Revenue", "value": "$120"}],
            series=[
                {"label": "Jan", "value": 120},
                {"label": "Feb", "value": 148},
            ],
            chart_type="bar",
            title="Revenue Dashboard",
        )

        self.assertIn('"x_column":"label"', html)
        self.assertIn('"y_columns":["value"]', html)
        self.assertIn('"label":"Jan","value":120', html)

    def test_chart_and_dashboard_share_dataset_builder(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Revenue", "value": "$120"}],
            series=[
                {"month": "Jan", "revenue": 120, "users": 500},
                {"month": "Feb", "revenue": 148, "users": 600},
            ],
            chart_type="line",
            title="Revenue Dashboard",
        )

        self.assertIn("function buildChartDatasets(", html)
        self.assertIn("buildChartDatasets(series, yCols, isMulti, chartType", html)
        self.assertIn("buildChartDatasets(series, dashYCols, dashMulti, chartType", html)

    def test_render_chart_accepts_rows_alias_after_data_detail(self):
        html = self.render_chart_html(
            rows=[
                {"month": "Jan", "revenue": 120},
                {"month": "Feb", "revenue": 148},
            ],
            chart_type="line",
            title="Monthly Revenue",
        )

        self.assertIn('"series":[{"month":"Jan","revenue":120},{"month":"Feb","revenue":148}]', html)
        self.assertIn('"x_column":"month"', html)
        self.assertIn('"y_columns":["revenue"]', html)

    def test_render_chart_uses_explicit_y_axis_label(self):
        html = self.render_chart_html(
            series=[
                {"month": "Jan", "revenue": 120},
                {"month": "Feb", "revenue": 148},
            ],
            chart_type="line",
            y_axis_label="Revenue (USD)",
            title="Monthly Revenue",
        )

        self.assertIn('"y_axis_label":"Revenue (USD)"', html)
        self.assertIn("function yScaleOptions(yAxisLabel, textColor, gridColor)", html)
        self.assertIn("title: {", html)
        self.assertIn("text: yAxisLabel", html)
        self.assertIn("y: yScaleOptions(yAxisLabel, textColor, gridColor)", html)

    def test_render_chart_combines_single_y_column_with_explicit_unit(self):
        html = self.render_chart_html(
            series=[
                {"time": "00:00", "requests": 120},
                {"time": "01:00", "requests": 148},
            ],
            chart_type="bar",
            y_axis_unit="rpm",
            title="Request Rate",
        )

        self.assertIn('"y_columns":["requests"]', html)
        self.assertIn('"y_axis_label":"requests (rpm)"', html)

    def test_render_chart_does_not_apply_unit_to_multiple_y_columns(self):
        html = self.render_chart_html(
            series=[
                {"month": "Jan", "revenue": 120, "users": 500},
                {"month": "Feb", "revenue": 148, "users": 600},
            ],
            chart_type="line",
            y_columns=["revenue", "users"],
            y_axis_unit="USD",
            title="Revenue and Users",
        )

        self.assertIn('"y_columns":["revenue","users"]', html)
        self.assertIn('"y_axis_label":"revenue, users"', html)
        self.assertNotIn('"y_axis_label":"revenue, users (USD)"', html)
        self.assertNotIn('"y_axis_label":"revenue (USD), users (USD)"', html)

    def test_render_dashboard_applies_same_y_axis_label_rules(self):
        html = self.render_dashboard_html(
            metrics=[{"label": "Peak", "value": "5,677 rpm"}],
            series=[
                {"time": "00:00", "requests": 120},
                {"time": "01:00", "requests": 148},
            ],
            chart_type="line",
            y_axis_label="Requests (rpm)",
            title="Traffic Dashboard",
        )

        self.assertIn('"y_axis_label":"Requests (rpm)"', html)
        self.assertIn("var dashYAxisLabel = axisTitleFromData(data, dashYCols);", html)
        self.assertIn("y: yScaleOptions(dashYAxisLabel, textColor, gridColor)", html)


if __name__ == "__main__":
    unittest.main()
