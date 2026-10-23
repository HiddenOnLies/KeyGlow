# Changelog

## Unreleased

- **Caps Lock light**: while Caps Lock is on, KeyGlow lights the Caps Lock key (white by
  default) on keyboards that have no indicator of their own, since OpenRGB's direct control
  hides the keyboard's built-in Caps Lock highlight. *Settings → Caps Lock light*: Automatic,
  Always or Off, plus the color. Model layouts can say whether the keyboard has its own
  indicator (`caps_lock_indicator`); the HyperX Alloy Origins 65 doesn't.
- **New community gallery**: the 239 look-alike theme profiles are gone. The gallery now lives in
  its own repository, [KeyGlow-profiles](https://github.com/HiddenOnLies/KeyGlow-profiles), and
  the app downloads it at most once a day (one file, validated, cached for offline use; a copy
  ships with the app). It starts with 22 hand-designed profiles, most animated or reacting to
  typing, including 8 well-known themes (Catppuccin, Dracula, Nord, Gruvbox, Tokyo Night,
  Rosé Pine, Solarized, Everforest), each with its own design. New *reactive* filter.
- `keyglow gallery` checks profile files and builds the gallery bundle.
- Gallery: 11 more interactive profiles (Paint Splash, Sonar, Equalizer, Shockwave, Typing
  Rainbow, Ghost Trail, Pond, Negative, Magma Typing, Neon Pulse, Fireworks).
- Fix: in key-press layers with several colors, a lit key could change color when an older
  press faded out; each press now keeps its color.

## 0.3.0

- **Keyboard-specific layouts**: KeyGlow recognizes keyboards by their USB ID (read from
  OpenRGB) and uses an exact layout from its model database (`keyglow/layouts/`) when there is
  one. Otherwise it adapts the closest standard layout and now also moves keys that OpenRGB's
  matrix places in a different row.
- *Settings* shows where the keyboard drawing comes from and can export it, so users can
  contribute exact layouts for their models.
- **KeyGlow workshop**: exact layouts are also downloaded from a community repository
  (KeyGlow-layouts), at most once a day, as one file looked up locally (no device IDs are
  sent), cached for offline use and validated before use. Can be turned off in *Settings*.
- `keyglow workshop` checks layout files and builds the workshop bundle.
- Model layouts are only used when they contain every key the keyboard reports, so variants
  that share a USB ID (ANSI/ISO) get the right one. First workshop layouts: HyperX Alloy
  Origins 65 (verified) and ASUS ROG Azoth, US and ISO (not yet tested on hardware).
- Extra keys that a standard layout doesn't have are placed next to their neighbor in
  OpenRGB's key matrix.
- Fix: key-press lighting could reuse stale key presses on Windows.
- Fixes: switching a layer from One to Several colors with wave/cycle/plasma; editable numbers
  next to every slider; drag (or Alt+arrows) to reorder a layer's colors.

## 0.2.0

- **Any keyboard**: the layout is detected automatically from OpenRGB (LED names and key
  matrix); keys outside the standard layouts, like media keys, are placed from the matrix.
  New built-in layouts: ANSI 65%, 75% and TKL, and ISO 60%, TKL and full size.
  Settings can force a layout or pick a keyboard when OpenRGB sees several.
- **Other programs**: import OpenRGB profiles (`.json` from OpenRGB 1.0+ and legacy `.orp`);
  export to OpenRGB profiles, key color maps with OpenRGB, web or QMK key names, and CSV.
  New *Export…* dialog in the app and `keyglow export` command.
- Key names: ISO keys, media keys and QMK keycodes are recognized.
- **Save to keyboard memory** (*⋯ → Save to keyboard memory…*): on keyboards whose OpenRGB
  driver can store lighting, KeyGlow saves the closest hardware mode (or each key's color) so
  the keyboard keeps it without any software running. Keyboards that can't (like the HyperX
  Alloy Origins 65 through OpenRGB) get a clear explanation instead.
- **New look**: black interface with a single neutral accent, and bundled IBM Plex Sans,
  IBM Plex Mono and Space Grotesk fonts (SIL Open Font License).
- **Download and use**: KeyGlow opens OpenRGB by itself (minimized, SDK server on) when it's
  installed but not running, shows a step-by-step *Connect your keyboard* guide when the
  keyboard can't be reached, and can start with Windows in the background.
- Fix: the status no longer stays on "Connecting…" when OpenRGB is closed.
- Fix: profiles whose layers rely on default colors (e.g. Campfire) no longer crash the editor.
- Repository: theme profiles moved to `keyglow/community/themes/`; documentation split into
  `docs/` (compatibility, profile format, profile sources) and `CONTRIBUTING.md`.

## 0.1.0 — first public preview

First public version. It works day to day on a HyperX Alloy Origins 65 on Windows, but it is
still early and has only been tested on that keyboard.

- Portable profile format (`keyglow/1`): layers, blend modes, key groups, by-name and
  by-position adaptation between keyboard layouts.
- 17 effects, including key-press reactive lighting.
- Desktop app (`KeyGlow.exe`): live keyboard preview, layer editor, quick start effects,
  profile library, tray icon, per-game profiles.
- 54 built-in presets and a community gallery with 239 theme profiles generated from
  Catppuccin, Dracula, Nord and Tinted Theming (MIT).
- Importers for OpenRGB-style maps, web key codes, QMK names and CSV.
- Command line: `preview`, `import`, `apply`, `capture`, `probe`, `validate`.
