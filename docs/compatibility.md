# Compatibility

## Keyboards

KeyGlow drives keyboards through [OpenRGB](https://openrgb.org), so in principle it works with
any keyboard OpenRGB supports. What KeyGlow needs to know is the **layout**: where each key is,
so spatial effects (waves, gradients, ripples) look right.

### Automatic layout (default)

When KeyGlow connects, it reads the keyboard's USB ID, LED names and key matrix from OpenRGB
and picks the most specific layout it can:

1. **Exact layout for the model**, if the keyboard is in KeyGlow's model database
   (`keyglow/layouts/`), recognized by its USB ID (or its name).
2. Otherwise, the **standard layout** that fits its keys best (see below), trimmed to the keys
   the keyboard actually has. Keys that OpenRGB's matrix puts in a different row (a 75% whose
   right column is in another order, for example) are moved next to their real neighbors, and
   keys that aren't in any standard layout (media keys, macro keys…) are placed from the matrix.
3. If the keyboard doesn't look like any standard layout at all (a macro pad, for instance),
   KeyGlow uses the matrix grid directly.

*Settings → Keyboard layout* shows which of these was used. The layout is remembered, so the
app starts with the right drawing even before OpenRGB answers. You can also force a layout there.

### Contributing the exact layout of your keyboard

If the drawing doesn't match your keyboard:

1. *Settings → Export this layout* saves a `.json` with your keyboard's keys, its USB ID and name.
2. Fix the positions (`x`, `y` in key units, `w`/`h` for wide or tall keys). Each key is
   `{"id": "LSHIFT", "x": 0, "y": 3, "w": 2.25}`; run `keyglow layout ansi_full --json` to see
   a complete example.
3. Add it to `keyglow/layouts/` in a pull request, or attach it to a
   [keyboard report](https://github.com/HiddenOnLies/KeyGlow/issues/new?template=keyboard_report.yml).

A model file can also reuse a built-in layout instead of listing keys:

```json
{"title": "HyperX Alloy Origins 65", "usb": ["03f0:038f"], "builtin": "alloy_origins_65"}
```

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

### Saving to the keyboard's memory

*⋯ → Save to keyboard memory…* stores the lighting in the keyboard itself, so it stays without
KeyGlow or OpenRGB running. It only works when OpenRGB's driver for that keyboard can save
(its modes are marked as savable). The keyboard only knows its own modes, so KeyGlow saves the
closest one (static, breathing, rainbow…) or, if the keyboard has a savable per-key mode, each
key's color at that moment.

The **HyperX Alloy Origins 65** can't do this through OpenRGB: its driver only has a "Direct"
mode that has to be refreshed every 50 ms, otherwise the keyboard goes back to its built-in
effect. The keyboard does have 3 onboard profiles, but they are written by HyperX NGENUITY with
an undocumented protocol. Supporting it means capturing NGENUITY's USB traffic and reproducing
it in a KeyGlow backend.

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

The OpenRGB reader and writer follow the format as written in OpenRGB's own source
(`ProfileManager.cpp`, `RGBController.cpp`). Verified so far:

- A profile exported by KeyGlow loads in **OpenRGB 1.1** and shows exactly the exported colors
  (tested on a HyperX Alloy Origins 65).
- `.orp` import is tested with a real keyboard's description for format versions 0–4. Newer
  `.orp` versions, and `.json` files saved by OpenRGB itself, are only tested with files built
  to the format.

To use an exported profile, put the `.json` in OpenRGB's profiles folder and restart OpenRGB
(it reads the folder at startup):

- OpenRGB running normally: `%APPDATA%\OpenRGB\profiles`
- OpenRGB 1.1 installed **as a Windows service**: `C:\Program Files\OpenRGB\service_config\profiles`
  (needs administrator rights to copy files there)

### Not supported (and why)

| Program | Reason |
|---|---|
| Corsair iCUE, Razer Synapse/Chroma, Logitech G HUB, SteelSeries GG | Closed, undocumented formats; most of their profiles are made for their own effect engines |
| SignalRGB | Effects are web pages (HTML + JavaScript), i.e. code, which KeyGlow deliberately never runs |
| Wootility | Profiles are shared as opaque codes inside the app |

Use *Capture from keyboard* as a workaround: apply a profile in the other program, then capture
the colors the keyboard shows (works for static lighting).
