from pathlib import Path
import re
import unittest


ROOT = Path(__file__).parent.parent


class VersionCompatibilityTest(unittest.TestCase):
    def test_v3_declares_open_webui_0102_compatibility(self):
        tool_source = (ROOT / "tool.py").read_text(encoding="utf-8")

        self.assertRegex(tool_source, r"(?m)^title: Inline Visualizer Template v3$")
        self.assertRegex(tool_source, r"(?m)^version: 0\.6\.0$")
        self.assertRegex(
            tool_source,
            r"(?m)^required_open_webui_version: 0\.10\.2$",
        )
        self.assertRegex(tool_source, r'(?m)^_BUILD = "0\.6\.0"$')

    def test_readme_identifies_v3_and_its_version_boundary(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("Inline Visualizer Template v3", readme)
        self.assertIn("Open WebUI 0.10.2+", readme)

    def test_v3_keeps_message_level_embed_delivery(self):
        tool_source = (ROOT / "tool.py").read_text(encoding="utf-8")

        self.assertIn('"type": "embeds"', tool_source)
        self.assertIn('"replace": False', tool_source)
        self.assertEqual(len(re.findall(r"__event_emitter__: Any = None", tool_source)), 5)


if __name__ == "__main__":
    unittest.main()
