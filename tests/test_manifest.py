import json
from pathlib import Path
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "noctalia-track-accent"


class ManifestTests(unittest.TestCase):
    def test_versions_match(self) -> None:
        manifest = tomllib.loads((PLUGIN_DIR / "plugin.toml").read_text())
        catalog = tomllib.loads((ROOT / "catalog.toml").read_text())

        self.assertEqual(manifest["version"], catalog["plugin"][0]["version"])

    def test_all_setting_translation_keys_exist(self) -> None:
        manifest = tomllib.loads((PLUGIN_DIR / "plugin.toml").read_text())
        translations = json.loads(
            (PLUGIN_DIR / "translations" / "en.json").read_text()
        )

        for setting in manifest["setting"]:
            with self.subTest(setting=setting["key"]):
                self.assertIn(setting["label_key"], translations)
                if "description_key" in setting:
                    self.assertIn(setting["description_key"], translations)
                for option in setting.get("options", ()):
                    self.assertIn(option["label_key"], translations)

    def test_shader_controls_use_fine_grained_integer_percentages(self) -> None:
        manifest = tomllib.loads((PLUGIN_DIR / "plugin.toml").read_text())
        settings = {setting["key"]: setting for setting in manifest["setting"]}
        expected_ranges = {
            "silence_brightness_percent": (0, 100, 40),
            "spectrum_gain_percent": (0, 300, 180),
            "bass_gain_percent": (0, 150, 35),
            "gradient_speed_percent": (-50, 50, 0),
            "dark_color_floor_percent": (0, 100, 50),
        }

        for key, (minimum, maximum, default) in expected_ranges.items():
            with self.subTest(setting=key):
                setting = settings[key]
                self.assertEqual(setting["type"], "int")
                self.assertEqual(setting["min"], minimum)
                self.assertEqual(setting["max"], maximum)
                self.assertEqual(setting["default"], default)


if __name__ == "__main__":
    unittest.main()
