# Where profiles come from

KeyGlow only ships profiles whose license allows redistribution, with attribution.
This page tracks the sources already used and the ones evaluated for the future.

## Already included

The [community gallery](https://github.com/HiddenOnLies/KeyGlow-profiles) has its own
repository. Its theme profiles use the official palettes of Catppuccin, Dracula, Nord, Gruvbox,
Tokyo Night, Rosé Pine, Solarized and Everforest (all MIT), each with its own design; credits and
license texts are in that repository's `CREDITS.md`.

Up to version 0.3.0 KeyGlow shipped 239 theme profiles generated from these palettes and from
Tinted Theming base16. They were replaced by fewer, hand-designed profiles because they all
looked alike and almost none were animated.

## Good candidates

| Source | License | Size | Idea |
|---|---|---|---|
| [uiGradients](https://github.com/ghosh/uiGradients) | MIT | 382 named gradients (`gradients.json`) | Gradient and wave profiles |
| [WebGradients](https://github.com/itmeo/webgradients) | MIT | 180 gradients with angles (`gradients.json`) | Gradient profiles that keep the original angle |
| [Aurora](https://github.com/Aurora-RGB/Aurora) | MIT | Lighting for ~45 games and apps (CS:GO, Dota 2, League of Legends, Rocket League, Minecraft…) | Recreate their static key highlights as game presets. Defined in C#, so it is a manual port |
| [Solarized](https://github.com/altercation/solarized), [Rosé Pine](https://github.com/rose-pine/neovim), [Everforest](https://github.com/sainnhe/everforest), [Nightfox](https://github.com/EdenEast/nightfox.nvim) | MIT | A few official palettes each | Theme profiles from the official repos (some are already in base16) |
| [SignalRGB_Effects](https://github.com/stronk-dev/SignalRGB_Effects) | Unlicense | 2 effects | Ideas for new effects (rewritten, never run as code) |
| [QMK RGB Matrix](https://docs.qmk.fm/features/rgb_matrix) | GPL-2.0 (code) | ~40 well-known keyboard animations | Reimplement the best-known animations (pinwheel, splash, cycle…) from their description, without copying code |

## Not usable

| Source | Why |
|---|---|
| rgbprofiles.com | Its terms forbid automated downloads, and its profiles are licensed for personal use only |
| Razer Chroma Workshop, Corsair iCUE profiles, Logitech G HUB | Owned by their authors or vendors, no redistribution license, closed formats |
| [WLED](https://github.com/wled/WLED) palettes | EUPL-1.2 (copyleft); the cpt-city palettes it includes have no clear license |
| [iTerm2-Color-Schemes](https://github.com/mbadolato/iTerm2-Color-Schemes), [Gogh](https://github.com/Gogh-Co/Gogh) | Mixed or unstated licenses per scheme |
| Most SignalRGB community effects | No license (all rights reserved) and they are code |
| Lospec palettes | No site-wide license; some authors forbid republishing |

Users can still bring profiles from closed programs into KeyGlow themselves with
*Capture from keyboard* (static lighting only), for their own use.
