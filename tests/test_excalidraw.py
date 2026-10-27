"""Check figure assets and the editable Excalidraw introduction."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ["overview", "family", "creative_rankings", "elimination"]


class EditableFigures(unittest.TestCase):
    def test_all_released_figures_have_previews(self):
        for name in FIGURES:
            for extension in ("svg", "png"):
                self.assertTrue((ROOT / "figures" / f"{name}.{extension}").is_file())
        self.assertEqual([p.name for p in (ROOT / "figures").glob("*.excalidraw")], ["overview.excalidraw"])

    def test_scenes_have_native_elements_and_unique_ids(self):
        for name in ["overview"]:
            scene = json.loads((ROOT / "figures" / f"{name}.excalidraw").read_text())
            self.assertEqual(scene["type"], "excalidraw")
            self.assertEqual(scene["version"], 2)
            self.assertFalse(scene["files"])
            self.assertTrue(all(e["type"] in {"text", "rectangle", "ellipse", "line", "arrow"} for e in scene["elements"]))
            self.assertEqual(len(scene["elements"]), len({e["id"] for e in scene["elements"]}))

    def test_text_uses_excalidraw_handwriting_font(self):
        for name in ["overview"]:
            scene = json.loads((ROOT / "figures" / f"{name}.excalidraw").read_text())
            self.assertTrue(all(e["fontFamily"] == 1 for e in scene["elements"] if e["type"] == "text"))

if __name__ == "__main__":
    unittest.main()
