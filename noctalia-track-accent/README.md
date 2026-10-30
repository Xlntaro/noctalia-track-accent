# Track Accent for Umbriel

Use the current Noctalia media cover as up to four accent colors on Umbriel's
audio-reactive `audio-theme` window border. The colors blend smoothly around
the border and change with Noctalia's active or pinned MPRIS player while the
existing spectrum and bass response remain intact.

## Plugin

| Field | Value |
| --- | --- |
| ID | `xintaro/noctalia-track-accent` |
| Entry | Service: `track-accent` |
| Plugin API | `24` |
| Version | `1.2.1` |

The service has no widget or panel. It starts automatically when the plugin is
enabled and restores the previous shader when it is disabled.

## Requirements

The following manifest dependencies must be available on `PATH`:

| Manifest dependency | Purpose |
| --- | --- |
| `systemd (busctl)` | Reads Noctalia's active MPRIS player through `GetActivePlayer`. |
| `dbus (dbus-monitor)` | Subscribes to Noctalia media changes without polling. |
| `python3` | Runs the small, non-UI helper. |
| `imagemagick (magick or convert)` | Extracts the cover accent; ImageMagick 7 and 6 are supported. |

You also need Noctalia 5.4.0 or newer, Umbriel with the `audio-theme` border
preset enabled, and an active MPRIS player in the same user session:

```toml
[effects]
border = "audio-theme"
```

Check the commands before enabling the plugin:

```sh
command -v python3 busctl dbus-monitor
command -v magick || command -v convert
```

## Umbriel setup

The plugin intentionally does not create or modify Umbriel configuration. Before
enabling it, create the `audio-theme` preset directory and its two files:

```sh
mkdir -p ~/.config/umbriel/effects/audio-theme
```

Create `~/.config/umbriel/effects/audio-theme/effect.toml`:

```toml
[effects.preset.audio-theme]
kind = "border"
shader = "shader.glsl"
palette = true
animated = true
speed = 1.0

[effects.preset.audio-theme.light]
spread = 45
intensity = 0.8
threshold = 0.4
```

Create `~/.config/umbriel/effects/audio-theme/shader.glsl`. This is the normal
palette-based fallback; the plugin saves it before replacing it and restores it
when disabled:

```glsl
vec4 border(vec2 uv) {
  vec2 center = uv - vec2(0.5);
  float position = atan(center.y, center.x) / 6.2831853 + 0.5;
  float band = abs(position * 2.0 - 1.0);
  float signal = umbriel_audio_spectrum(band);
  float bass = umbriel_audio_spectrum(0.0);
  vec4 color = umbriel_palette_at(0.0);
  float color_peak = max(max(color.r, color.g), color.b);
  vec3 visible_color = color_peak > 0.001
    ? color.rgb * max(1.0, 0.5 / color_peak)
    : vec3(0.5);
  float brightness = clamp(0.4 + signal * 1.8 + bass * 0.35, 0.0, 1.0);
  return vec4(visible_color * color.a * brightness, color.a);
}
```

In `~/.config/umbriel/config.toml`, add the preset file to the existing
`[include].files` array. Do not replace the rest of that array:

```toml
[include]
files = [
  # Keep all existing includes here.
  "~/.config/umbriel/effects/audio-theme/effect.toml",
]
```

Finally, add `border = "audio-theme"` to the existing `[effects]` table (or
create that table if it is absent):

```toml
[effects]
border = "audio-theme"
```

Validate the result before enabling the plugin:

```sh
umbriel config validate -c ~/.config/umbriel/config.toml
```

If the directory or `shader.glsl` is missing, the plugin deliberately leaves
Umbriel unchanged rather than creating or overwriting compositor configuration.

## Installation and usage

### Add through Noctalia Settings

To install from a Git repository without publishing to the Community source:

1. Open **Settings → Plugins**.
2. In **Sources**, select **Add Source**.
3. Enter a unique source name, for example `xintaro-plugins`.
4. Select **Git** and enter the repository URL, for example
   `https://github.com/Xlntaro/noctalia-track-accent`.
   Use the repository URL only; do not use a GitHub `/tree/...` subdirectory
   URL.
5. Save the source, ensure its source toggle is enabled, then press **Update**
   (the circular-arrow button) on that source.
6. `Track Accent for Umbriel` appears in the **Plugins** section. Turn on its
   toggle to fetch and start `xintaro/noctalia-track-accent`.

Use the gear button on the plugin row to select **Cover color mode**:

- **Multi-color gradient** (default) extracts up to four distinct cover colors
  and blends them around the border.
- **Single accent** uses only the strongest cover color, matching the original
  behavior.

The choice applies immediately to the current cover; changing it does not wait
for a new track.

The repository must contain the root `catalog.toml` as well as the
`noctalia-track-accent/` plugin directory. Noctalia uses the catalog to list
the plugin before it exports that directory on enable.

To turn the plugin off, use its toggle in **Settings → Plugins**. To disconnect
the repository entirely, use the custom source's settings menu and choose
**Remove source**.

### Command line

When developing locally, add the repository containing this directory as a
path source, then enable the exact plugin id:

```sh
noctalia msg plugins source add dev path ~/dev/community-plugins
noctalia msg plugins enable xintaro/noctalia-track-accent
```

For a one-plugin local install, copy this directory under
`$XDG_DATA_HOME/noctalia/plugins/noctalia-track-accent/`, then run the same
enable command. The service starts immediately; play a track or change the
active Noctalia player to update the border.

To return to the ordinary Umbriel palette behavior, disable it:

```sh
noctalia msg plugins disable xintaro/noctalia-track-accent
```

If migrating from the earlier local id, disable it first so it can restore its
backup:

```sh
noctalia msg plugins disable local/noctalia-track-accent
noctalia msg plugins enable xintaro/noctalia-track-accent
```

## Distribution packages

| Distribution | Packages |
| --- | --- |
| NixOS / Home Manager | `python3 imagemagick` |
| Arch Linux | `python imagemagick systemd dbus` |
| Debian / Ubuntu | `python3 imagemagick systemd dbus` |
| Fedora | `python3 ImageMagick systemd dbus` |
| openSUSE | `python3 ImageMagick systemd dbus-1` |

For Home Manager:

```nix
home.packages = with pkgs; [ python3 imagemagick ];
```

## Notes

- **Media integration:** the public Luau API does not expose `MediaService`,
  so the helper calls Noctalia's `dev.noctalia.Mpris.GetActivePlayer` and
  watches its `ActivePlayerChanged`, `TrackChanged`, and `PlayersChanged`
  signals. This follows the media widget's active/pinned player without
  periodic polling.
- **Artwork and network:** local `file://` artwork is copied to the plugin's
  private state directory. Remote `http(s)` artwork is downloaded with an
  8 MiB limit and an 8-second timeout. No remote code is downloaded or run.
- **Color selection:** the helper selects up to four populous, vivid, and
  visually distinct colors, orders them by hue, and blends them into a closed
  gradient around the border. Transparent pixels, near-black, near-white, and
  weakly saturated colors are rejected when a usable accent exists. A
  monochrome or unavailable cover falls back to Umbriel's primary palette
  accent.
- **Files:** the helper writes only
  `~/.config/umbriel/effects/audio-theme/shader.glsl`, atomically and only if
  the color changed. Before its first write it saves the original shader and
  its artwork cache under the plugin's Noctalia state directory. It restores
  the original shader on disable only when the current file still has the
  plugin marker, so a manual edit is never overwritten.
- **Processes:** it starts `dbus-monitor`, makes short `busctl` queries, and
  runs ImageMagick only when artwork changes. All subprocesses use argument
  arrays; track titles, URLs, and other media metadata are never shell input.
- **Scope:** it does not modify `/nix/store`, Noctalia's global palette,
  wallpapers, or any effect except the configured `audio-theme` shader.
