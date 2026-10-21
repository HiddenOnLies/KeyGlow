# Changelog

## Unreleased

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
