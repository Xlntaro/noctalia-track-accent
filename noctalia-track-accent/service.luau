--!nonstrict
-- The plugin API itself has no MediaService object. The helper reads Noctalia's
-- documented-in-source MPRIS facade, so its active player matches the widget.
-- Blocking DBus/network/image work stays outside this VM.

local helper = noctalia.pluginDir() .. "/noctalia-track-accent.py"
local dataDir = noctalia.pluginDataDir()
local shader = "~/.config/umbriel/effects/audio-theme/shader.glsl"

local defaults = {
  palette_mode = "gradient",
  idle_mode = "native",
  silence_brightness_percent = 40,
  dark_color_floor_percent = 50,
  spectrum_gain_percent = 180,
  bass_gain_percent = 35,
  max_colors = 4,
  gradient_speed_percent = 0,
  fallback_color = "#7C6FDC",
}

local function setting(key)
  local value = noctalia.getConfig(key)
  if value == nil then
    value = defaults[key]
  end
  return tostring(value)
end

local function scaledSetting(key)
  local value = noctalia.getConfig(key)
  if value == nil then
    value = defaults[key]
  end
  return tostring((tonumber(value) or defaults[key]) / 100.0)
end

local function helperArgs(action)
  return {
    "python3", helper, action,
    "--mode", setting("palette_mode"),
    "--idle-mode", setting("idle_mode"),
    "--silence-brightness", scaledSetting("silence_brightness_percent"),
    "--dark-color-floor", scaledSetting("dark_color_floor_percent"),
    "--spectrum-gain", scaledSetting("spectrum_gain_percent"),
    "--bass-gain", scaledSetting("bass_gain_percent"),
    "--max-colors", setting("max_colors"),
    "--gradient-speed", scaledSetting("gradient_speed_percent"),
    "--fallback-color", setting("fallback_color"),
    "--state-dir", dataDir,
    "--shader", shader,
  }
end

local function start()
  noctalia.runAsync(helperArgs("--watch"))
end

local function applySettings()
  noctalia.runAsync(helperArgs("--set-settings"))
end

local function restore()
  -- The helper first terminates its watcher, then restores only a shader it
  -- generated itself. It does not overwrite a user edit made while enabled.
  noctalia.runAsync({ "python3", helper, "--restore", "--state-dir", dataDir, "--shader", shader })
end

start()

function onEnable()
  start()
end

function onConfigChanged()
  applySettings()
end

function onExit(_signal, _reason)
  restore()
end
