# Compatibility

## Keyboards

KeyGlow drives keyboards through [OpenRGB](https://openrgb.org), so in principle it works with
any keyboard OpenRGB supports. What KeyGlow needs to know is the **layout**: where each key is,
so spatial effects (waves, gradients, ripples) look right.

### Automatic layout (default)

When KeyGlow connects, it reads the keyboard's LED names and key matrix from OpenRGB and builds
the layout itself:

1. It picks the built-in layout that fits the keyboard's keys best (see below).
2. It trims it to the keys the keyboard actually has.
3. Keys that aren't in any built-in layout (media keys, macro keys…) are placed using their
   position in OpenRGB's key matrix.
4. If the keyboard doesn't look like any standard layout at all (a macro pad, for instance),
   KeyGlow uses the matrix grid directly.

The layout is remembered, so the app starts with the right keyboard drawing even before
OpenRGB answers. You can force a layout in *Settings → Keyboard layout*.

If OpenRGB sees more than one keyboard, set *Settings → Keyboard to use* to part of its name.

### Built-in layouts

| Name | Layout | Keys |
|---|---|---|
| `alloy_origins_65` | HyperX Alloy Origins 65 | 68 |
| `ansi_60` | ANSI 60% | 61 |
| `ansi_65` | ANSI 65% (Del, PgUp, PgDn, End column) | 68 |
| `ansi_75` | ANSI 75% | 83 |
| `ansi_tkl` | ANSI tenkeyless (80%) | 87 |
| `ansi_full` | ANSI full size (100%) | 104 |
| `iso_60` | ISO 60% | 62 |
| `iso_tkl` | ISO tenkeyless (80%) | 88 |
| `iso_full` | ISO full size (100%) | 105 |

Run `keyglow layout <name>` to draw one in the terminal, or `keyglow layout <name> --json` to
export it, edit it and load it with `--layout my_layout.json`.

### Tested hardware

| Keyboard | Status |
|---|---|
| HyperX Alloy Origins 65 (`03f0:038f`) | Works, used daily (OpenRGB 1.1, Windows 11) |
| Anything else | Not tested yet — reports are very welcome |

If your keyboard isn't detected by OpenRGB, run `keyglow probe` to see its `VID:PID` and check
the [OpenRGB supported devices list](https://openrgb.org/devices.html) or its
[issue tracker](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues).

## Other programs

KeyGlow profiles have layers and animations that other programs can't represent, so
**exports are a snapshot**: the color of every key at one moment of the profile.

| Program / format | Import | Export | Notes |
|---|---|---|---|
| KeyGlow profile (`.json`) | ✅ | ✅ | Full profile, animations included |
| OpenRGB profile (`.json`, OpenRGB 1.0+) | ✅ | ✅ | Export targets the connected keyboard, so OpenRGB recognizes it |
| OpenRGB profile (`.orp`, older versions) | ✅ | — | Binary format; read support only |
| Key color map, OpenRGB names (`Key: Left Control`) | ✅ | ✅ | `{name: color}` JSON |
| Key color map, web key codes (`ControlLeft`) | ✅ | ✅ | What browsers report in `KeyboardEvent.code` |
| Key color map, QMK keycodes (`KC_LCTL`) | ✅ | ✅ | Useful when writing firmware lighting by hand |
| CSV (`key,color`) | ✅ | ✅ | Any of the key name styles above |

In the app: *⋯ → Import…* (or drag a file onto the window) and *⋯ → Export…*.
From the command line:

```bash
keyglow import my_openrgb_profile.orp -o mine.json
keyglow export examples/aurora.json --format openrgb --at 2 -o aurora.openrgb.json
keyglow export examples/aurora.json --format keys-qmk -o aurora-qmk.json
```

The OpenRGB reader follows the format as written in OpenRGB's own source
(`ProfileManager.cpp`, `RGBController.cpp`). It is tested against synthetic files and a real
keyboard's description for `.orp` versions 0–4. Newer `.orp` versions and loading KeyGlow's
exported profiles inside OpenRGB itself haven't been verified yet.

### Not supported (and why)

| Program | Reason |
|---|---|
| Corsair iCUE, Razer Synapse/Chroma, Logitech G HUB, SteelSeries GG | Closed, undocumented formats; most of their profiles are made for their own effect engines |
| SignalRGB | Effects are web pages (HTML + JavaScript), i.e. code, which KeyGlow deliberately never runs |
| Wootility | Profiles are shared as opaque codes inside the app |

Use *Capture from keyboard* as a workaround: apply a profile in the other program, then capture
the colors the keyboard shows (works for static lighting).
