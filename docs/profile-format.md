# Profile format

A KeyGlow profile is **plain JSON, never code**, so it is safe to download and share.

```json
{
  "format": "keyglow/1",
  "name": "Aurora",
  "author": "your_name",
  "description": "Northern lights with WASD highlighted.",
  "tags": ["animated", "gaming"],
  "designed_for": "ansi_full",
  "layers": [
    {"effect": "color_wave", "params": {"colors": ["#00ffa0", "#8040ff"], "speed": 0.15}},
    {"effect": "static", "params": {"keys": {"Escape": "#fff", "KeyW": "#f00"}}},
    {"effect": "solid", "params": {"color": "#ffffff"}, "keys": ["@wasd", "@arrows"], "opacity": 0.8}
  ]
}
```

## Layers

Layers are combined from bottom to top. Each layer has:

| Field | Meaning |
|---|---|
| `effect` | One of the effects below |
| `params` | The effect's parameters (run `keyglow effects` to list them with their defaults) |
| `keys` | Optional: which keys the layer affects. Key names or portable groups |
| `opacity` | Optional, `0`–`1` |
| `blend` | Optional: `normal`, `add`, `multiply` or `screen` |

**Portable key groups**: `@wasd`, `@arrows`, `@letters`, `@numbers`, `@fn_row`, `@numpad`,
`@modifiers`, `@nav`, `@all`. A group only includes the keys a keyboard actually has.

**Key names** can be written the way any of these programs write them; KeyGlow translates
them: OpenRGB (`Key: Left Control`), web key codes (`ControlLeft`, `KeyW`), QMK (`KC_LCTL`),
Linux (`KP_ENTER`) or plain names (`Left Ctrl`, `Esc`).

## Effects

`solid`, `static` (a color per key), `gradient`, `rainbow_wave`, `color_wave`, `spectrum`,
`breathing`, `ripple`, `starlight`, `plasma`, `rain`, `scanner`, `fire`, `heartbeat`,
`reactive` (lights up the keys you press), `points` (colors pinned to positions) and `image`
(a picture stretched over the keyboard).

## How a profile adapts to another keyboard

1. **By name**: every key that exists on both keyboards keeps its color.
2. **Nearest-neighbor fill**: if the profile is a full per-key map, keys your keyboard has and
   the original didn't (e.g. `Fn`) take the color of the physically closest key. Loose
   highlights (only WASD) are not filled.
3. **Dropped**: keys your keyboard lacks (numpad, F1–F12) are reported and ignored.
4. **Portable mode** (`keyglow import … --portable`): instead of names, colors are pinned to
   normalized positions, so the whole design is rescaled to any keyboard, like an image.

`designed_for` names the layout the profile was made for (see
[compatibility](compatibility.md#built-in-layouts)); it enables the nearest-neighbor fill.

## Galleries

KeyGlow's own gallery is [KeyGlow-profiles](https://github.com/HiddenOnLies/KeyGlow-profiles):
to share a profile with everyone, add it there with a pull request.

You can also publish your own gallery as an `index.json` anywhere (a GitHub repository works
well) and point KeyGlow to it in *Settings → Other community gallery*:

```json
{"format": "keyglow-gallery/1", "name": "My gallery",
 "profiles": [
   {"name": "Neon", "author": "someone", "tags": ["animated"], "url": "neon.json"},
   {"name": "Inline", "profile": {"format": "keyglow/1", "name": "Inline", "layers": [...]}}
 ]}
```

Relative `url`s are resolved against the index.
