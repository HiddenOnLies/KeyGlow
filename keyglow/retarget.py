"""Adaptación de perfiles entre teclados distintos.

Estrategia "híbrida":
1. Las teclas con el mismo nombre conservan su color (la W sigue siendo la W).
2. Las teclas que el teclado destino tiene pero el original no, se rellenan con el
   color de la tecla más cercana físicamente (solo si la capa es un mapa completo,
   no un simple resaltado como WASD).
3. Las teclas que no existen en el destino (p. ej. el numpad en un 65%) se descartan
   y se informa de ellas.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from . import color as C
from .keynames import normalize
from .layout import Layout
from .profile import Profile

#: fracción mínima de teclas cubiertas para considerar una capa "mapa completo"
FULL_MAP_THRESHOLD = 0.5


@dataclass
class Report:
    dropped: list[str] = field(default_factory=list)
    filled: dict[str, str] = field(default_factory=dict)  # tecla destino -> tecla origen
    unknown: list[str] = field(default_factory=list)

    def lines(self) -> list[str]:
        out = []
        if self.unknown:
            out.append(f"Unrecognized key names ({len(self.unknown)}): {', '.join(self.unknown)}")
        if self.dropped:
            out.append(f"Keys your keyboard doesn't have ({len(self.dropped)}): {', '.join(self.dropped)}")
        if self.filled:
            pairs = ", ".join(f"{a}←{b}" for a, b in self.filled.items())
            out.append(f"Keys filled from their nearest neighbor ({len(self.filled)}): {pairs}")
        return out or ["Perfect fit: every key matches."]


def _nearest(src: Layout, colored: dict[str, tuple], target: Layout, key_id: str) -> str:
    tk = target.get(key_id)
    tu, tv = target.norm(tk)
    best, best_d = None, float("inf")
    for sid in colored:
        sk = src.get(sid)
        if sk is None:
            continue
        su, sv = src.norm(sk)
        # pondera más la fila (v) que la columna: preferimos no saltar de fila
        d = (su - tu) ** 2 + 4 * (sv - tv) ** 2
        if d < best_d:
            best, best_d = sid, d
    return best


def retarget(profile: Profile, target: Layout, source: Layout | None = None,
             fill: bool = True) -> tuple[Profile, Report]:
    rep = Report()
    out = copy.deepcopy(profile)
    for layer in out.layers:
        if "keys" in layer:
            for sel in layer["keys"]:
                if sel.startswith("@"):
                    continue
                kid = normalize(sel) or sel
                if kid not in target and kid not in rep.dropped:
                    rep.dropped.append(kid)
        if layer["effect"] != "static":
            continue
        colors: dict[str, str] = {}
        for name, value in layer.get("params", {}).get("keys", {}).items():
            kid = normalize(name)
            if kid is None:
                rep.unknown.append(name)
            elif kid in target:
                colors[kid] = value
            else:
                colors[kid] = value  # se usa como origen para rellenar; se quita abajo
                if kid not in rep.dropped:
                    rep.dropped.append(kid)
        if fill and source is not None:
            in_source = [k for k in colors if k in source]
            if len(in_source) >= FULL_MAP_THRESHOLD * len(source):
                src_colored = {k: colors[k] for k in in_source}
                for tid in target.ids:
                    if tid not in colors:
                        sid = _nearest(source, src_colored, target, tid)
                        if sid:
                            colors[tid] = src_colored[sid]
                            rep.filled[tid] = sid
        layer.setdefault("params", {})["keys"] = {k: v for k, v in colors.items() if k in target}
    out.designed_for = target.name
    return out, rep


def to_portable(profile: Profile, source: Layout) -> Profile:
    """Convierte capas estáticas por tecla en capas ``points`` basadas en posición.

    El resultado ya no depende de nombres de teclas: se adapta a cualquier
    distribución como si fuese una imagen estirada sobre el teclado.
    """
    out = copy.deepcopy(profile)
    for layer in out.layers:
        if layer["effect"] != "static":
            continue
        pts = []
        for name, value in layer.get("params", {}).get("keys", {}).items():
            k = source.get(normalize(name) or name)
            if k is None:
                continue
            u, v = source.norm(k)
            pts.append({"u": round(u, 4), "v": round(v, 4), "color": C.to_hex(C.parse(value))})
        layer["effect"] = "points"
        layer["params"] = {"points": pts}
    out.designed_for = ""
    return out
