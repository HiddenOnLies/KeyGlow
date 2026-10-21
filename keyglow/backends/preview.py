"""Vista previa sin hardware: en la terminal (color real ANSI) o como HTML animado."""

from __future__ import annotations

import json
import sys
import time

from ..layout import Layout
from ..profile import Renderer

COLS_PER_U = 4


def render_ansi(layout: Layout, frame: dict[str, tuple[int, int, int]]) -> list[str]:
    width = int(round(layout.width * COLS_PER_U))
    nrows = int(layout.height + 0.01)
    grid = [[(" ", None) for _ in range(width)] for _ in range(nrows)]
    for k in layout.keys:
        c0 = int(round(k.x * COLS_PER_U))
        c1 = int(round((k.x + k.w) * COLS_PER_U)) - 1  # deja un hueco entre teclas
        rgb = frame[k.id]
        for row in range(int(k.y + 0.01), int(k.y + k.h + 0.01)):
            if row >= nrows:
                continue
            for col in range(c0, min(c1, width)):
                grid[row][col] = (" ", rgb)
        text = k.label[: max(c1 - c0, 0)]
        start = c0 + max((c1 - c0 - len(text)) // 2, 0)
        row = int(k.y + 0.01)
        for i, ch in enumerate(text):
            if start + i < width:
                grid[row][start + i] = (ch, rgb)
    lines = []
    for row in grid:
        parts = []
        for ch, rgb in row:
            if rgb is None:
                parts.append("\x1b[0m" + ch)
            else:
                r, g, b = rgb
                fg = "30" if (r * 299 + g * 587 + b * 114) / 1000 > 140 else "97"
                parts.append(f"\x1b[48;2;{r};{g};{b}m\x1b[{fg}m{ch}")
        lines.append("".join(parts) + "\x1b[0m")
    return lines


def play_terminal(renderer: Renderer, seconds: float, fps: float = 20) -> None:
    out = sys.stdout
    if seconds <= 0:
        out.write("\n".join(render_ansi(renderer.layout, renderer.frame(0))) + "\n")
        return
    start = time.monotonic()
    first = True
    while (t := time.monotonic() - start) < seconds:
        lines = render_ansi(renderer.layout, renderer.frame(t))
        if not first:
            out.write(f"\x1b[{len(lines)}A")
        out.write("\n".join(lines) + "\n")
        out.flush()
        first = False
        time.sleep(1 / fps)


def export_html(renderer: Renderer, path: str, seconds: float = 6, fps: float = 24) -> None:
    layout = renderer.layout
    n = max(1, int(seconds * fps))
    frames = []
    for i in range(n):
        f = renderer.frame(i / fps)
        frames.append(["%02x%02x%02x" % f[k] for k in layout.ids])
    keys = [{"x": k.x, "y": k.y, "w": k.w, "h": k.h, "l": k.label} for k in layout.keys]
    data = json.dumps({"keys": keys, "frames": frames, "fps": fps,
                       "w": layout.width, "h": layout.height})
    title = renderer.profile.name
    html = _HTML.replace("__TITLE__", _esc(title)).replace("__SUB__", _esc(layout.title)) \
        .replace("__DATA__", data.replace("</", "<\\/"))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root { --bg:#f4f4f6; --fg:#1b1b1f; --case:#2a2a30; --muted:#6b6b75; }
@media (prefers-color-scheme: dark) { :root { --bg:#111114; --fg:#ececf1; --case:#1c1c21; --muted:#9a9aa5; } }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.4 system-ui, sans-serif;
       display:flex; flex-direction:column; align-items:center; padding:32px 16px; }
h1 { font-size:20px; margin:0 0 4px; } p { margin:0 0 20px; color:var(--muted); }
.kb { position:relative; width:min(100%, 900px); background:var(--case); border-radius:12px;
      padding:2%; box-sizing:border-box; }
.inner { position:relative; width:100%; }
.k { position:absolute; border-radius:4px; display:flex; align-items:center; justify-content:center;
     font-size:clamp(7px, 1.2vw, 12px); color:#fff; text-shadow:0 0 2px #000;
     box-shadow:0 0 10px -2px currentColor; }
</style></head><body>
<h1>__TITLE__</h1><p>__SUB__</p>
<div class="kb"><div class="inner" id="kb"></div></div>
<script>
const D = __DATA__;
const kb = document.getElementById('kb');
kb.style.aspectRatio = D.w + ' / ' + D.h;
const els = D.keys.map(k => {
  const e = document.createElement('div'); e.className = 'k'; e.textContent = k.l;
  const g = 0.06;
  e.style.left = (k.x + g) / D.w * 100 + '%'; e.style.top = (k.y + g) / D.h * 100 + '%';
  e.style.width = (k.w - 2*g) / D.w * 100 + '%'; e.style.height = (k.h - 2*g) / D.h * 100 + '%';
  kb.appendChild(e); return e;
});
let i = 0;
function tick() {
  const f = D.frames[i % D.frames.length];
  els.forEach((e, j) => {
    const c = f[j], n = parseInt(c, 16);
    const lum = ((n >> 16) * 299 + ((n >> 8) & 255) * 587 + (n & 255) * 114) / 1000;
    e.style.background = '#' + c; e.style.boxShadow = '0 0 12px -3px #' + c;
    e.style.color = lum > 160 ? '#111' : '#fff'; e.style.textShadow = lum > 160 ? 'none' : '';
  });
  i++;
}
tick(); setInterval(tick, 1000 / D.fps);
</script></body></html>
"""
