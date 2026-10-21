# KeyGlow

RGB keyboard lighting with **portable profiles**: a profile made for another keyboard
(a full-size, a 60%, another brand) adapts itself to yours, and the other way round.

> **Early preview.** KeyGlow works day to day on a **HyperX Alloy Origins 65** on Windows,
> but it hasn't been tested on other keyboards yet and there is still plenty to do.
> See [Status and roadmap](#status-and-roadmap). Feedback and issues are welcome.

![KeyGlow](docs/images/screenshot.png)

## Why another RGB app?

| Problem | How KeyGlow handles it |
|---|---|
| Profiles are tied to one keyboard model | Colors are stored by **key name** and **physical position**, not by LED index |
| Every program names keys differently | Key names from OpenRGB, browsers, QMK and Linux are translated both ways |
| A 104-key profile gets "cut off" on a 65% | Two modes: **by name** (W stays W) or **portable** (the whole design is rescaled to your keyboard, like an image) |
| Profiles are locked inside each app | Import and export **OpenRGB profiles**, key color maps and CSV ([details](docs/compatibility.md#other-programs)) |
| Sharing profiles is risky | A profile is **plain JSON, never code**, so it is safe to download from any URL |
| One app per brand | Hardware is driven through **[OpenRGB](https://openrgb.org)**, and the keyboard layout is **detected automatically** |

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
  Rain, Starlight, Ripple, Scanner, Heartbeat and Custom (paint keys with the mouse).
- **Layer editor**: each layer is an *Area* (all or some keys) + a *Color* (one, several,
  rainbow or hand-painted) + an *Animation*, with opacity and blend modes.
- **On key press**: light up the key you press, a ripple from it, or its row. It uses a Windows
  keyboard hook only while an active profile needs it, and only keeps which key was pressed and
  when, in memory, for a few seconds.
- **Profiles** (☰): built-in presets, your own (`Documents\KeyGlow\Perfiles`) and a community
  gallery that ships with **239 theme profiles** (Catppuccin, Dracula, Nord, base16).
- **Game profiles** (controller icon): one profile per game while it is in focus, plus optional
  recommended profiles for ~40 popular games.
- **Import / export** (⋯): KeyGlow and OpenRGB profiles, key color maps (OpenRGB, web, QMK names)
  and CSV. Drag a file onto the window to import it.
- **Any keyboard**: the layout comes from OpenRGB automatically; 9 standard layouts (ANSI/ISO,
  60% to full size) are built in. See [compatibility](docs/compatibility.md).

## Command line

```bash
keyglow layouts                                      # built-in keyboard layouts
keyglow preview examples/aurora.json --seconds 10    # animation in the terminal
keyglow import my_profile.orp -o mine.json           # OpenRGB, key maps, CSV, URLs…
keyglow export examples/aurora.json --format openrgb # for OpenRGB (or keys-web, keys-qmk, csv)
keyglow apply examples/aurora.json                   # play it on the real keyboard
keyglow capture -o what_i_had.json                   # save the colors the keyboard shows now
```

Run `keyglow --help` for everything else.

## Documentation

- [Compatibility](docs/compatibility.md): keyboards, layouts and other programs' formats
- [Profile format](docs/profile-format.md): layers, effects, key groups, galleries
- [Profile sources](docs/profile-sources.md): where the included profiles come from, and candidates
- [Contributing](CONTRIBUTING.md): development setup and repository layout
- [Changelog](CHANGELOG.md)

## Running from source

Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[app,hid,dev]"
keyglow-app                 # the desktop app
pytest                      # tests
powershell -ExecutionPolicy Bypass -File tools\build_exe.ps1   # builds dist\KeyGlow.exe
```

## Status and roadmap

- **Only tested on one keyboard** (HyperX Alloy Origins 65, Windows 11). The automatic layout
  should handle other OpenRGB keyboards, but reports from real hardware are the most useful
  contribution right now.
- **Windows only** for the desktop app (tray icon, keyboard hook, game detection). The library
  and CLI are plain Python.
- **Some code comments are still in Spanish**; they will be translated.
- Next: more profile sources ([candidates](docs/profile-sources.md#good-candidates)),
  audio-reactive effects, mice and other devices, a community gallery repository.

## License

[MIT](LICENSE). The theme profiles in `keyglow/community/themes/` are derived from
MIT-licensed palettes; see their [credits](keyglow/community/themes/CREDITS.md).
