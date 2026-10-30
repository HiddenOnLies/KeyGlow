"""Otros programas de iluminación abiertos, que se pelean con KeyGlow por el teclado.

Si dos programas mandan colores al mismo teclado, las luces parpadean o uno no hace nada;
algunos (Armoury Crate, iCUE, Synapse...) además se quedan el dispositivo y OpenRGB ni lo
ve. Aquí solo se mira la lista de procesos de Windows (nombres de ejecutable); no se toca
nada de esos programas.
"""

from __future__ import annotations

import sys

# ejecutable (en minúsculas) -> nombre que se enseña
KNOWN = {
    "armourycrate.exe": "ASUS Armoury Crate",
    "armourycrate.service.exe": "ASUS Armoury Crate",
    "armourycrate.usersessionhelper.exe": "ASUS Armoury Crate",
    "lightingservice.exe": "ASUS Aura (Armoury Crate)",
    "icue.exe": "Corsair iCUE",
    "ngenuity.exe": "HyperX NGENUITY",
    "hyperx ngenuity.exe": "HyperX NGENUITY",
    "razer synapse 3.exe": "Razer Synapse",
    "razer synapse.exe": "Razer Synapse",
    "razercentralservice.exe": "Razer Synapse",
    "lghub.exe": "Logitech G HUB",
    "lghub_agent.exe": "Logitech G HUB",
    "steelseriesgg.exe": "SteelSeries GG",
    "steelseriesengine.exe": "SteelSeries GG",
    "signalrgb.exe": "SignalRGB",
    "signalrgblauncher.exe": "SignalRGB",
    "msi.centralserver.exe": "MSI Center",
    "msi_central_service.exe": "MSI Center",
    "ledkeeper2.exe": "MSI Mystic Light",
    "rgbfusion.exe": "Gigabyte RGB Fusion",
    "redragon.exe": "Redragon",
    "wootility.exe": "Wootility",
}


# programa -> palabras del nombre de los teclados que maneja (para avisar solo si es su marca)
BRANDS = {
    "ASUS Armoury Crate": ("asus", "rog", "tuf"), "ASUS Aura (Armoury Crate)": ("asus", "rog", "tuf"),
    "Corsair iCUE": ("corsair",), "HyperX NGENUITY": ("hyperx",), "Razer Synapse": ("razer",),
    "Logitech G HUB": ("logitech", "logi "), "SteelSeries GG": ("steelseries",), "SignalRGB": ("",),
    "MSI Center": ("msi",), "MSI Mystic Light": ("msi",), "Gigabyte RGB Fusion": ("gigabyte", "aorus"),
    "Redragon": ("redragon",), "Wootility": ("wooting",),
}


def for_keyboard(apps: list[str], keyboard: str) -> list[str]:
    """De ``apps``, los que manejan teclados de la marca de ``keyboard`` (SignalRGB, todos)."""
    name = keyboard.lower()
    return [a for a in apps if any(w in name for w in BRANDS.get(a, ()))]


def match(names) -> list[str]:
    """Los programas conocidos entre ``names`` (nombres de ejecutable), una vez cada uno."""
    found = {KNOWN[n.lower()] for n in names if n.lower() in KNOWN}
    return sorted(found)


def process_names() -> list[str]:
    """Nombres de ejecutable de todos los procesos (Windows; en otros sistemas, vacío)."""
    if sys.platform != "win32":
        return []
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    snap = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if snap in (None, wintypes.HANDLE(-1).value):
        return []
    names = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(entry)
        ok = k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            names.append(entry.szExeFile)
            ok = k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snap)
    return names


def running() -> list[str]:
    """Programas de iluminación abiertos ahora mismo."""
    return match(process_names())
