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
    def test_dashboard_table_chart_type_renders_table_branch(self):
        module = load_tool_module()
        tool = module.Tools()

        response, _ = asyncio.run(
            tool.render_dashboard(
                metrics=[{"label": "Revenue", "value": "$120"}],
                series=[
                    {"label": "Jan", "value": 120},
                    {"label": "Feb", "value": 148},
                ],
                chart_type="table",
                title="Revenue Dashboard",
            )
        )

        html = response.body.decode("utf-8")

        self.assertIn('"chartType":"table"', html)
        self.assertIn("if (chartType === 'table')", html)
        self.assertIn("renderDashboardTable(series)", html)
        self.assertNotIn("if (chartType === 'table') { chartType = 'line'; }", html)


if __name__ == "__main__":
    unittest.main()
