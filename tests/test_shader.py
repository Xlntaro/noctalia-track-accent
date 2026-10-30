import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "noctalia-track-accent"
    / "noctalia-track-accent.py"
)
SPEC = importlib.util.spec_from_file_location("noctalia_track_accent", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PLUGIN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PLUGIN)


class ShaderSourceTests(unittest.TestCase):
    def test_silence_floor_keeps_dark_tint_visible(self) -> None:
        source = PLUGIN.shader_source(((1, 2, 3),))

        self.assertIn("float color_peak = max(max(color.r, color.g), color.b);", source)
        self.assertIn("color.rgb * max(1.0, 0.5 / color_peak)", source)
        self.assertIn("float brightness = clamp(0.4 + signal * 1.8 + bass * 0.35", source)
        self.assertIn("vec4(visible_color * color.a * brightness, color.a)", source)
        self.assertNotIn("clamp(0.15 + signal", source)

    def test_audio_spectrum_still_drives_generated_shader(self) -> None:
        source = PLUGIN.shader_source(((16, 32, 48), (128, 64, 32)))

        self.assertIn("float signal = umbriel_audio_spectrum(band);", source)
        self.assertIn("float bass = umbriel_audio_spectrum(0.0);", source)
        self.assertIn("signal * 1.8 + bass * 0.35", source)
        self.assertIn("const int noctalia_track_accent_count = 2;", source)

    def test_missing_cover_preserves_native_umbriel_border(self) -> None:
        source = PLUGIN.shader_source(())

        self.assertIn(
            "if (!noctalia_track_accent_available) return umbriel_sample(uv);",
            source,
        )
        self.assertNotIn("umbriel_palette_at(0.0)", source)

    def test_generated_shader_has_balanced_delimiters(self) -> None:
        source = PLUGIN.shader_source(((4, 8, 12),) * 4)

        for opening, closing in (("{", "}"), ("(", ")")):
            with self.subTest(delimiter=opening + closing):
                depth = 0
                for character in source:
                    if character == opening:
                        depth += 1
                    elif character == closing:
                        depth -= 1
                    self.assertGreaterEqual(depth, 0)
                self.assertEqual(depth, 0)


if __name__ == "__main__":
    unittest.main()
