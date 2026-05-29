import asyncio
import inspect
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parent))

from test_dashboard_table import load_tool_module


class AnalysisDashboardTest(unittest.TestCase):
    def render_analysis_html(self, **kwargs):
        module = load_tool_module()
        tool = module.Tools()
        response, _ = asyncio.run(tool.render_analysis_dashboard(**kwargs))
        return response.body.decode("utf-8")

    def test_analysis_dashboard_renders_configurable_modules(self):
        html = self.render_analysis_html(
            title="Service Traffic Analysis",
            subtitle="24-hour monitor overview",
            hero_chart={
                "title": "Traffic Trend",
                "chart_type": "line",
                "series": [
                    {"time": "00:00", "requests": 120, "errors": 3},
                    {"time": "01:00", "requests": 148, "errors": 5},
                ],
                "y_columns": ["requests", "errors"],
            },
            rankings={
                "title": "Peak Services",
                "items": [
                    {"label": "api-a", "value": 5677, "unit": "rpm"},
                    {"label": "api-b", "value": 4805, "unit": "rpm"},
                ],
            },
            small_charts=[
                {
                    "title": "Error Rate",
                    "chart_type": "line",
                    "series": [
                        {"time": "00:00", "rate": 1.2},
                        {"time": "01:00", "rate": 1.5},
                    ],
                }
            ],
            summary_cards=[
                {"label": "Peak", "value": "5,677 rpm", "delta": "+8%"},
                {"label": "Avg", "value": "3,120 rpm"},
            ],
        )

        self.assertIn('"template":"analysis_dashboard"', html)
        self.assertIn('"title":"Traffic Trend"', html)
        self.assertIn('"rankings":{"title":"Peak Services"', html)
        self.assertIn('"smallCharts":[{"title":"Error Rate"', html)
        self.assertIn("renderAnalysisDashboard(payload.data)", html)

    def test_analysis_dashboard_hides_missing_optional_modules(self):
        html = self.render_analysis_html(
            title="Sales Overview",
            hero_chart={
                "title": "Monthly Revenue",
                "chart_type": "bar",
                "series": [
                    {"month": "Jan", "revenue": 120},
                    {"month": "Feb", "revenue": 148},
                ],
            },
        )

        self.assertIn('"template":"analysis_dashboard"', html)
        self.assertIn('"heroChart"', html)
        self.assertNotIn('"rankings"', html)
        self.assertNotIn('"detailTable"', html)
        self.assertNotIn('"summaryCards"', html)

    def test_skill_keeps_data_detail_as_source_of_record(self):
        skill = __import__("pathlib").Path(__file__).with_name("SKILL.md").read_text(encoding="utf-8")

        self.assertIn("render_data_detail", skill)
        self.assertIn("数据来源", skill)
        self.assertIn("render_analysis_dashboard", skill)
        self.assertIn("必须先调用 `render_data_detail`", skill)
        self.assertIn("不再包含详细数据模块", skill)
        self.assertNotIn("detail_table", skill)

    def test_tool_instructions_make_data_detail_first_a_hard_rule(self):
        module = load_tool_module()

        self.assertIn("MUST call render_data_detail first", module.__doc__)
        self.assertIn("never call render_chart, render_dashboard, or render_analysis_dashboard before render_data_detail", module.__doc__)
        self.assertIn("Data detail first does not imply analysis dashboard", module.__doc__)
        self.assertIn("For a simple trend, bar, pie, or table request, use render_chart", module.__doc__)
        self.assertIn("For hourly changes of one metric, use render_chart", module.__doc__)
        self.assertIn("convert the same rows into the render_chart series parameter", module.__doc__)
        self.assertIn("render_dashboard is only for KPI cards plus an optional trend chart", module.__doc__)
        self.assertIn("Do not use render_analysis_dashboard for simple hourly changes", module.__doc__)
        self.assertIn("y_axis_label: complete y-axis label", module.__doc__)
        self.assertIn("y_axis_unit: unit for exactly one y-axis column", module.__doc__)
        self.assertIn("Never guess units from values", module.__doc__)

    def test_skill_limits_analysis_dashboard_to_explicit_multi_module_requests(self):
        skill = __import__("pathlib").Path(__file__).with_name("SKILL.md").read_text(encoding="utf-8")

        self.assertIn("不要因为必须先展示数据详情表，就自动选择综合分析看板", skill)
        self.assertIn("普通单图、趋势、柱状、饼图或表格请求必须优先使用 `render_chart`", skill)
        self.assertIn("只有当用户明确要求综合分析、监控看板、诊断、多角度展示", skill)
        self.assertNotIn("关键明细", skill)
        self.assertNotIn("| 任何可视化请求 |", skill)

    def test_analysis_dashboard_png_menu_exports_whole_dashboard_and_charts(self):
        html = self.render_analysis_html(
            title="Service Traffic Analysis",
            hero_chart={
                "title": "Traffic Trend",
                "chart_type": "line",
                "series": [
                    {"time": "00:00", "requests": 120},
                    {"time": "01:00", "requests": 148},
                ],
            },
            small_charts=[
                {
                    "title": "Error Rate",
                    "chart_type": "line",
                    "series": [
                        {"time": "00:00", "rate": 1.2},
                        {"time": "01:00", "rate": 1.5},
                    ],
                }
            ],
        )

        self.assertIn("html2canvas", html)
        self.assertIn("exportWholeDashboardPng()", html)
        self.assertIn('data-export-canvas="analysisHero"', html)
        self.assertIn('data-export-canvas="\' + canvas.id + \'"', html)
        self.assertIn("pngMenu", html)

    def test_analysis_dashboard_has_no_detail_table_module(self):
        module = load_tool_module()
        signature = inspect.signature(module.Tools.render_analysis_dashboard)

        self.assertNotIn("detail_table", signature.parameters)

        html = self.render_analysis_html(
            title="Grid Load Analysis",
            hero_chart={
                "title": "Max Load",
                "chart_type": "bar",
                "series": [
                    {"province": "江苏电网", "max_load": 5677},
                    {"province": "浙江电网", "max_load": 4805},
                ],
            },
        )

        self.assertNotIn('"detailTable"', html)
        self.assertNotIn("renderAnalysisTable", html)

    def test_single_series_bar_keeps_per_bar_colors(self):
        html = self.render_analysis_html(
            title="Grid Load Analysis",
            hero_chart={
                "title": "Max Load",
                "chart_type": "bar",
                "series": [
                    {"province": "江苏电网", "max_load": 5677},
                    {"province": "浙江电网", "max_load": 4805},
                ],
            },
        )

        self.assertIn("series.map(function(_, i) { return COLORS[i % COLORS.length]; })", html)

    def test_analysis_dashboard_chart_blocks_support_y_axis_labels(self):
        html = self.render_analysis_html(
            title="Grid Load Analysis",
            hero_chart={
                "title": "Hourly Load",
                "chart_type": "line",
                "series": [
                    {"hour": "00:00", "load": 1200},
                    {"hour": "01:00", "load": 1480},
                ],
                "y_axis_unit": "MW",
            },
            small_charts=[
                {
                    "title": "Temperature",
                    "chart_type": "line",
                    "series": [
                        {"hour": "00:00", "temperature": 31},
                        {"hour": "01:00", "temperature": 32},
                    ],
                    "y_axis_label": "Temperature (C)",
                }
            ],
        )

        self.assertIn('"y_axis_label":"load (MW)"', html)
        self.assertIn('"y_axis_label":"Temperature (C)"', html)
        self.assertIn("var yAxisLabel = axisTitleFromData(block, yCols);", html)
        self.assertIn("y: yScaleOptions(yAxisLabel, textColor, gridColor)", html)


if __name__ == "__main__":
    unittest.main()
