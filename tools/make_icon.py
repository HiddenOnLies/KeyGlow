"""Genera el icono de KeyGlow (una tecla con brillo RGB) en PNG e ICO.

Uso: python tools/make_icon.py
Escribe keyglow/app/static/icon.png y assets/keyglow.ico.
"""

from __future__ import annotations

import colorsys
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
S = 1024  # se dibuja grande y se reduce para que quede suave


def hue_field(size: int) -> Image.Image:
    """Degradado cónico de todos los tonos alrededor del centro."""
    img = Image.new("RGB", (size, size))
    px = img.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            h = (math.atan2(y - c, x - c) / (2 * math.pi) + 0.6) % 1.0
            r, g, b = colorsys.hsv_to_rgb(h, 0.85, 1.0)
            px[x, y] = (int(r * 255), int(g * 255), int(b * 255))
    return img


def rounded(size, box, radius, width=0) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    if width:
        d.rounded_rectangle(box, radius, outline=255, width=width)
    else:
        d.rounded_rectangle(box, radius, fill=255)
    return m


def make() -> Image.Image:
    hues = hue_field(S // 4).resize((S, S), Image.BICUBIC)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))

    # fondo: cuadrado redondeado casi negro
    bg = Image.new("RGBA", (S, S), (14, 15, 24, 255))
    out.paste(bg, mask=rounded(S, (40, 40, S - 40, S - 40), 200))

    # halo de color detrás de la tecla
    cap = (210, 230, S - 210, S - 190)
    glow_mask = rounded(S, cap, 110).filter(ImageFilter.GaussianBlur(70))
    glow = Image.composite(hues, Image.new("RGB", (S, S)), glow_mask).convert("RGBA")
    glow.putalpha(ImageChops.multiply(glow_mask, rounded(S, (40, 40, S - 40, S - 40), 200)))
    out = Image.alpha_composite(out, glow)

    # cuerpo de la tecla
    body = Image.new("RGBA", (S, S), (24, 26, 38, 255))
    out.paste(body, mask=rounded(S, cap, 110))
    top = (cap[0] + 50, cap[1] + 36, cap[2] - 50, cap[3] - 90)
    face = Image.new("RGBA", (S, S), (34, 37, 54, 255))
    out.paste(face, mask=rounded(S, top, 80))

    # borde RGB de la tecla
    ring = rounded(S, cap, 110, width=26)
    out.paste(hues, mask=ring)

    # letra K con el mismo degradado
    k = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(k)
    cx, cy = (top[0] + top[2]) / 2, (top[1] + top[3]) / 2
    h, w = 300, 52
    x0 = cx - 95
    d.rectangle((x0 - w / 2, cy - h / 2, x0 + w / 2, cy + h / 2), fill=255)
    d.line((x0 + 10, cy + 10, cx + 120, cy - h / 2 + 10), fill=255, width=w)
    d.line((x0 + 40, cy - 20, cx + 125, cy + h / 2 - 8), fill=255, width=w)
    out.paste(hues, mask=k.filter(ImageFilter.GaussianBlur(1.5)))
    return out


def main() -> None:
    img = make()
    png = ROOT / "keyglow" / "app" / "static" / "icon.png"
    png.parent.mkdir(parents=True, exist_ok=True)
    img.resize((256, 256), Image.LANCZOS).save(png)
    ico = ROOT / "assets" / "keyglow.ico"
    ico.parent.mkdir(parents=True, exist_ok=True)
    img.resize((256, 256), Image.LANCZOS).save(
        ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icono guardado en {png} y {ico}")


if __name__ == "__main__":
    main()
