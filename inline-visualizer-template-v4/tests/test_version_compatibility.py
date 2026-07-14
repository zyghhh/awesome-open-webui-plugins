from pathlib import Path
import re
import unittest


ROOT = Path(__file__).parent.parent


class VersionCompatibilityTest(unittest.TestCase):
    def test_v4_declares_open_webui_0102_compatibility(self):
        tool_source = (ROOT / "tool.py").read_text(encoding="utf-8")

        self.assertRegex(tool_source, r"(?m)^title: Inline Visualizer Template v4$")
        self.assertRegex(tool_source, r"(?m)^version: 0\.7\.0$")
        self.assertRegex(
            tool_source,
            r"(?m)^required_open_webui_version: 0\.10\.2$",
        )
        self.assertRegex(tool_source, r'(?m)^_BUILD = "0\.7\.0"$')

    def test_readme_identifies_v4_and_its_native_embed_delivery(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Inline Visualizer Template v4", readme)
        self.assertIn("Open WebUI 0.10.2+", readme)
        self.assertIn("工具调用级", readme)

    def test_v4_uses_native_tool_result_delivery(self):
        tool_source = (ROOT / "tool.py").read_text(encoding="utf-8")

        self.assertNotIn('"type": "embeds"', tool_source)
        self.assertNotIn("_MESSAGE_EMBEDS_METADATA_KEY", tool_source)
        self.assertEqual(len(re.findall(r"__event_emitter__: Any = None", tool_source)), 0)
        self.assertEqual(len(re.findall(r"__metadata__: Any = None", tool_source)), 0)

    def test_skill_identifies_v4(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("name: inline-visualizer-template-v4", skill)
        self.assertIn("# 模板可视化 v4", skill)


if __name__ == "__main__":
    unittest.main()
