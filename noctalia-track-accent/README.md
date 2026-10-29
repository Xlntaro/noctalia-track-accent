# Track Accent for Umbriel

Use the current Noctalia media cover as the accent color of Umbriel's
audio-reactive `audio-theme` window border. The color changes with Noctalia's
active or pinned MPRIS player while the border's existing spectrum and bass
response remain intact.

## Plugin

| Field | Value |
| --- | --- |
| ID | `xintaro/noctalia-track-accent` |
| Entry | Service: `track-accent` |
| Plugin API | `24` |
| Version | `1.0.1` |

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

## Installation and usage

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
- **Color selection:** transparent pixels, near-black, near-white, and weakly
  saturated colors are rejected when a usable accent exists. A monochrome or
  unavailable cover falls back to Umbriel's primary palette accent.
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
