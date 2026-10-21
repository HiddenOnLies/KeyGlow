"""Detecta teclados HyperX conectados por USB.

Sirve para saber el VID:PID exacto de tu Alloy Origins 65 y comprobar si OpenRGB lo
soporta o si hará falta un driver HID propio (ver README, "Plan B").
"""

from __future__ import annotations

HYPERX_VENDORS = {0x0951: "Kingston/HyperX", 0x03F0: "HP (HyperX)"}


def probe(all_devices: bool = False) -> list[dict]:
    try:
        import hid
    except ImportError as e:
        raise RuntimeError("Falta hidapi: pip install keyglow[hid]") from e
    found = []
    for d in hid.enumerate():
        if all_devices or d["vendor_id"] in HYPERX_VENDORS:
            found.append({
                "vid_pid": f"{d['vendor_id']:04x}:{d['product_id']:04x}",
                "vendor": HYPERX_VENDORS.get(d["vendor_id"], d.get("manufacturer_string") or "?"),
                "product": d.get("product_string") or "?",
                "interface": d.get("interface_number"),
                "usage_page": f"0x{d.get('usage_page', 0):04x}",
                "path": d["path"].decode(errors="replace") if isinstance(d["path"], bytes) else d["path"],
            })
    return found
