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


if __name__ == "__main__":
    unittest.main()
