# KeyGlow

RGB keyboard lighting with **portable profiles**: a profile made for another keyboard
(a full-size, a 60%, another brand) adapts itself to yours, and the other way round.

> **Early preview (v0.1.0).** KeyGlow works day to day on a **HyperX Alloy Origins 65**
> on Windows, but it hasn't been tested on other keyboards yet and there is still plenty
> to do. See [Status and roadmap](#status-and-roadmap). Feedback and issues are welcome.

![KeyGlow](docs/images/screenshot.png)

## Why another RGB app?

| Problem | How KeyGlow handles it |
|---|---|
| Profiles are tied to one keyboard model | Colors are stored by **key name** and **physical position**, not by LED index |
| Every program names keys differently | Name translation: OpenRGB (`Key: Left Control`), web key codes (`ControlLeft`, `KeyW`), QMK/Linux (`KP_ENTER`) and common names |
| A 104-key profile gets "cut off" on a 65% | Two modes: **by name** (W stays W) or **portable** (the whole design is rescaled to your keyboard, like an image) |
| Sharing profiles is risky or impossible | A profile is **plain JSON, never code**, so it is safe to download from any URL |
| One app per brand | Hardware is driven through **[OpenRGB](https://openrgb.org)**, which supports hundreds of devices |

## Download

Grab `KeyGlow.exe` from the [latest release](https://github.com/HiddenOnLies/KeyGlow/releases).
You also need [OpenRGB](https://openrgb.org) running with its **SDK Server** started
(KeyGlow talks to the keyboard through it). Close your vendor's software (NGenuity, iCUE,
Synapse…) first: two programs writing to the keyboard fight each other.

## The app

Double-click `KeyGlow.exe`. The interface opens in its own window and an icon appears in the
system tray with *Open KeyGlow*, *Lights off* and *Quit*. The lights keep running when you
close the window.

- **Quick start effects**: Static, Wave, Rainbow, Gradient, Breathing, Spectrum, Plasma, Fire,
  Rain, Starlight, Ripple, Scanner, Heartbeat and Custom (paint keys with the mouse; right-click
  erases).
- **Layer editor**: each layer is an *Area* (all or some keys) + a *Color* (one, several,
  rainbow or hand-painted) + an *Animation*, with opacity and blend modes.
- **On key press**: light up the key you press, a ripple from it, or its row. It uses a Windows
  keyboard hook (like Synapse or iCUE) only while an active profile needs it, and only keeps
  which key was pressed and when, in memory, for a few seconds.
- **Profiles** (☰ button): built-in presets, your own (`Documents\KeyGlow\Perfiles`) and the
  community gallery, which ships with **~240 theme profiles** (see below).
- **Game profiles** (controller icon): one profile per game while it is in focus. Optionally,
  a recommended profile by genre for ~40 popular games, detecting what's installed from Steam,
  Epic Games and Riot.
- Import (also by dragging a file in), export `.json`, capture the keyboard's current colors,
  undo with Ctrl+Z, save with Ctrl+S. The last profile is restored on start.

### Community gallery

The gallery is just an `index.json` published anywhere (for example a GitHub repository).
Point KeyGlow to it in *Settings*:

```json
{"format": "keyglow-gallery/1", "name": "My gallery",
 "profiles": [{"name": "Neon", "author": "someone", "tags": ["animated"], "url": "neon.json"}]}
```

Relative `url`s are resolved against the index; a profile can also be embedded with
`"profile": {...}`.

The built-in gallery includes 239 **Theme** profiles generated from MIT-licensed color themes:
[Catppuccin](https://github.com/catppuccin/palette), [Dracula](https://github.com/dracula/dracula-theme),
[Nord](https://github.com/nordtheme/nord) and the base16 schemes from
[Tinted Theming](https://github.com/tinted-theming/schemes). They are regenerated with
`python tools/make_theme_profiles.py`. Attribution and license texts are in
[`keyglow/community/THEME_CREDITS.md`](keyglow/community/THEME_CREDITS.md).

## Running from source

Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[app,hid,dev]"
keyglow-app                 # the desktop app (or: python -m keyglow.app.main)
pytest                      # tests
```

Extras: `openrgb` to drive real hardware, `image` to use pictures as an effect, `hid` for the
USB detector, `app` for the desktop app, `build` to make the executable:

```powershell
powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1   # writes dist\KeyGlow.exe
```

## Command line

```bash
keyglow layouts                                      # built-in keyboards
keyglow effects                                      # effects and their parameters
keyglow preview examples/aurora.json --seconds 10    # animation in the terminal
keyglow preview examples/fps_full_size.json --html preview.html   # preview in the browser

# Import a per-key map made for a full-size keyboard and adapt it to your 65%:
keyglow import examples/sunset_openrgb_style.json --from ansi_full -o my_sunset.json
# ...or save it "portable" (works the same on any keyboard):
keyglow import examples/sunset_openrgb_style.json --from ansi_full --portable -o sunset.json

# Download a community profile:
keyglow import https://example.com/profiles/neon.json -o neon.json

# Apply to the real keyboard (OpenRGB open with the SDK Server started):
keyglow apply examples/aurora.json
keyglow capture -o what_i_had.json       # save the colors the keyboard shows right now
```

## Profile format

```json
{
  "format": "keyglow/1",
  "name": "Aurora",
  "author": "your_name",
  "designed_for": "ansi_full",
  "layers": [
    {"effect": "color_wave", "params": {"colors": ["#00ffa0", "#8040ff"], "speed": 0.15}},
    {"effect": "static", "params": {"keys": {"Escape": "#fff", "KeyW": "#f00"}}},
    {"effect": "solid", "params": {"color": "#ffffff"}, "keys": ["@wasd", "@arrows"], "opacity": 0.8}
  ]
}
```

- **Layers** are combined bottom to top, with `opacity` and `blend` (`normal`, `add`, `multiply`, `screen`).
- **`keys`** limits which keys a layer affects. It accepts key names and portable groups:
  `@wasd`, `@arrows`, `@letters`, `@numbers`, `@fn_row`, `@numpad`, `@modifiers`, `@nav`, `@all`.
- **Effects**: `solid`, `static`, `gradient`, `rainbow_wave`, `color_wave`, `spectrum`,
  `breathing`, `ripple`, `starlight`, `plasma`, `rain`, `scanner`, `fire`, `heartbeat`,
  `reactive`, `points` (colors pinned to positions) and `image` (any picture stretched over the
  keyboard). Run `keyglow effects` for their parameters.
- **Import** also accepts bare maps `{"Escape": "#f00", ...}`, lists
  `[{"led": "Key: A", "color": [255,0,0]}]` and `key,color` CSV.

## How a profile adapts to another keyboard

1. **By name**: every key that exists on both keyboards keeps its color.
2. **Nearest-neighbor fill**: if the profile is a full map, keys your keyboard has and the
   original didn't (e.g. `Fn`) take the color of the physically closest key. Loose highlights
   (only WASD) are not filled.
3. **Dropped**: keys your keyboard lacks (numpad, F1–F12) are reported and ignored.
4. With `--portable`, normalized positions are used instead of names, so the whole design fits
   any size.

## Hardware support

KeyGlow sends colors through [OpenRGB](https://openrgb.org). **Confirmed:** OpenRGB 1.1 detects
the HyperX Alloy Origins 65 (`03f0:038f`) and KeyGlow drives it. Other keyboards that OpenRGB
supports should work, but only the 65% ANSI layout has been tested so far.

If your keyboard isn't detected:

1. Run `keyglow probe` and note its `VID:PID` (HyperX uses `0951`, newer HP-made models `03f0`).
2. Check whether it shows up in OpenRGB. If it does, `keyglow apply` works directly.
3. If it doesn't, ask for support in the [OpenRGB issue tracker](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues),
   or write a HID backend in `keyglow/backends/` (only `write(frame)` has to be implemented).

The `alloy_origins_65` layout is a typical ANSI 65% (right column: Home, Del, PgUp, PgDn, as
OpenRGB 1.1 reports it). If yours differs: `keyglow layout alloy_origins_65 --json > my65.json`,
edit it and use it with `--layout my65.json`.

## Project layout

```
keyglow/
  keynames.py   canonical key names + translation from other programs
  layout.py     keyboard geometry (65%, 60%, full size) and portable key groups
  effects.py    effects based on physical position
  profile.py    profile format and layer engine
  retarget.py   adapting profiles between keyboards
  importers.py  JSON, CSV, URLs
  backends/     preview (terminal/HTML), openrgb (hardware), hidprobe (USB)
  app/          desktop app: local server, light engine, game detection, web UI (static/)
  presets/      built-in profiles
  community/    built-in gallery (theme profiles + credits)
examples/       example profiles for the command line
tools/          build script, icon and theme profile generators
tests/          pytest
```

## Status and roadmap

This is a first public version. Known gaps and next steps:

- **Only tested on one keyboard** (HyperX Alloy Origins 65, Windows 11). Reports from other
  keyboards are the most useful contribution right now.
- **Windows only** for the desktop app (tray icon, keyboard hook, game detection). The library
  and CLI are plain Python.
- **Code comments and docstrings are still in Spanish**; they will be translated.
- More importers: OpenRGB `.orp` profiles, SignalRGB effects.
- Audio-reactive effects, more devices (mice, mousepads) with their own geometry.
- A community gallery repository that anyone can contribute profiles to.

## License

[MIT](LICENSE). The theme profiles in `keyglow/community/theme-*.json` are derived from
MIT-licensed palettes; see [THEME_CREDITS.md](keyglow/community/THEME_CREDITS.md).
