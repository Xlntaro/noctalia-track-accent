--!nonstrict
-- The plugin API itself has no MediaService object. The helper reads Noctalia's
-- documented-in-source MPRIS facade, so its active player matches the widget.
-- Blocking DBus/network/image work stays outside this VM.

local helper = noctalia.pluginDir() .. "/noctalia-track-accent.py"
local dataDir = noctalia.pluginDataDir()
local shader = "~/.config/umbriel/effects/audio-theme/shader.glsl"

local function paletteMode()
  return noctalia.getConfig("palette_mode")
end

local function start()
  noctalia.runAsync({ "python3", helper, "--watch", "--mode", paletteMode(), "--state-dir", dataDir, "--shader", shader })
end

local function applyPaletteMode()
  noctalia.runAsync({ "python3", helper, "--set-mode", "--mode", paletteMode(), "--state-dir", dataDir, "--shader", shader })
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
  applyPaletteMode()
end

function onExit(_signal, _reason)
  restore()
end
