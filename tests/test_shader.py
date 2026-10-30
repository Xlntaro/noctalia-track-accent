import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "noctalia-track-accent"
    / "noctalia-track-accent.py"
)
SPEC = importlib.util.spec_from_file_location("noctalia_track_accent", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
PLUGIN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PLUGIN
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

    def test_idle_fallback_modes_are_generated(self) -> None:
        cases = {
            "native": "return umbriel_sample(uv);",
            "last_cover": "return umbriel_sample(uv);",
            "palette": "umbriel_palette_at(fract(gradient_position))",
            "fixed": "vec4(0.070588, 0.203922, 0.337255, 1.000000)",
            "hidden": "return vec4(0.0);",
        }
        for mode, expected in cases.items():
            with self.subTest(mode=mode):
                settings = PLUGIN.ShaderSettings(
                    idle_mode=mode,
                    fallback_color="#123456",
                )
                self.assertIn(expected, PLUGIN.shader_source((), settings))

    def test_custom_response_and_rotation_are_embedded(self) -> None:
        settings = PLUGIN.ShaderSettings(
            silence_brightness=0.25,
            dark_color_floor=0.7,
            spectrum_gain=2.25,
            bass_gain=0.8,
            gradient_speed=-0.125,
        )
        source = PLUGIN.shader_source(((12, 24, 48),), settings)

        self.assertIn("position + umbriel_time * -0.125", source)
        self.assertIn("max(1.0, 0.7 / color_peak)", source)
        self.assertIn("clamp(0.25 + signal * 2.25 + bass * 0.8", source)

    def test_last_cover_and_max_colors_are_applied_from_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary) / "state"
            shader = Path(temporary) / "shader.glsl"
            state_dir.mkdir()
            shader.write_text("vec4 border(vec2 uv) { return vec4(1.0); }\n")
            settings = PLUGIN.ShaderSettings(idle_mode="last_cover", max_colors=2)
            PLUGIN.write_settings(state_dir, settings)
            PLUGIN.write_last_accent_colors(
                state_dir,
                ((10, 20, 30), (40, 50, 60), (70, 80, 90)),
            )

            PLUGIN.apply_colors(state_dir, shader, ())
            source = shader.read_text()

        self.assertIn("const bool noctalia_track_accent_available = true;", source)
        self.assertIn("const int noctalia_track_accent_count = 2;", source)

    def test_last_cover_migrates_legacy_non_empty_colors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary) / "state"
            shader = Path(temporary) / "shader.glsl"
            state_dir.mkdir()
            shader.write_text("vec4 border(vec2 uv) { return vec4(1.0); }\n")
            PLUGIN.write_settings(
                state_dir,
                PLUGIN.ShaderSettings(idle_mode="last_cover"),
            )
            PLUGIN.write_last_colors(state_dir, ((11, 22, 33),))

            PLUGIN.apply_colors(state_dir, shader, ())

            self.assertEqual(
                PLUGIN.read_last_accent_colors(state_dir),
                ((11, 22, 33),),
            )

    def test_settings_are_clamped_and_round_trip(self) -> None:
        settings = PLUGIN.settings_from_mapping({
            "palette_mode": "gradient",
            "idle_mode": "fixed",
            "silence_brightness": 9,
            "dark_color_floor": -2,
            "spectrum_gain": 2.4,
            "bass_gain": 0.6,
            "max_colors": 99,
            "gradient_speed": -0.2,
            "fallback_color": "#ABCDEF",
        })
        self.assertEqual(settings.silence_brightness, 1.0)
        self.assertEqual(settings.dark_color_floor, 0.0)
        self.assertEqual(settings.max_colors, 4)

        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            PLUGIN.write_settings(state_dir, settings)
            restored = PLUGIN.read_settings(state_dir)

        self.assertEqual(restored, settings)

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
