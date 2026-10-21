"""Genera docs/images/demo.gif: el teclado animado con varios presets.

Uso: python tools/make_demo_gif.py
Usa el mismo motor que la app (Renderer), así que el GIF muestra los efectos reales.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from keyglow.keynames import label
from keyglow.layout import load_layout
from keyglow.profile import Profile, Renderer

ROOT = Path(__file__).resolve().parent.parent
PRESETS = ["aurora", "rainbow", "fire", "synthwave", "ripple"]
U = 44            # píxeles por unidad de tecla
PAD = 26
FPS = 12
SECONDS = 2.0     # por preset


def _font(size: int):
    # PIL no lee woff2; se usa la fuente monoespaciada del sistema si está
    for name in ("CascadiaMono.ttf", "consola.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def frame_image(layout, colors: dict[str, tuple[int, int, int]], font, title: str, tfont) -> Image.Image:
    w = int(layout.width * U) + PAD * 2
    h = int(layout.height * U) + PAD * 2 + 40
    top = 40
    img = Image.new("RGB", (w, h), (0, 0, 0))
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for k in layout.keys:
        x0, y0 = PAD + k.x * U + 3, top + PAD + k.y * U + 3
        x1, y1 = PAD + (k.x + k.w) * U - 3, top + PAD + (k.y + k.h) * U - 3
        c = colors.get(k.id, (0, 0, 0))
        gd.rounded_rectangle((x0, y0, x1, y1), 7, fill=c)
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(14)), 0.55)
    d = ImageDraw.Draw(img)
    for k in layout.keys:
        x0, y0 = PAD + k.x * U + 3, top + PAD + k.y * U + 3
        x1, y1 = PAD + (k.x + k.w) * U - 3, top + PAD + (k.y + k.h) * U - 3
        c = colors.get(k.id, (0, 0, 0))
        edge = tuple(int(v * 0.75 + 30) for v in c)
        d.rounded_rectangle((x0, y0, x1, y1), 6, fill=(14, 14, 14), outline=edge, width=2)
        text = label(k.id)
        if text:
            legend = tuple(min(255, int(v * 0.8 + 60)) for v in c)
            d.text(((x0 + x1) / 2, (y0 + y1) / 2), text, fill=legend, font=font, anchor="mm")
    d.text((PAD, 22), title, fill=(236, 236, 236), font=tfont, anchor="lm")
    return img


def main() -> int:
    layout = load_layout("alloy_origins_65")
    font, tfont = _font(12), _font(17)
    frames = []
    for name in PRESETS:
        data = json.loads((ROOT / "keyglow" / "presets" / f"{name}.json").read_text(encoding="utf-8"))
        renderer = Renderer(Profile.from_dict(data), layout)
        for i in range(int(SECONDS * FPS)):
            colors = renderer.frame(1.0 + i / FPS)
            frames.append(frame_image(layout, colors, font, data["name"], tfont))
    out = ROOT / "docs" / "images" / "demo.gif"
    pal = [f.convert("P", palette=Image.ADAPTIVE, colors=96) for f in frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=True)
    print(f"{out} ({out.stat().st_size // 1024} KB, {len(frames)} frames)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
