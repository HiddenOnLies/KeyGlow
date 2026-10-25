"""Detecta qué teclas se pulsan, para los efectos reactivos (solo Windows).

Usa un gancho de teclado de bajo nivel (``WH_KEYBOARD_LL``), el mismo mecanismo que
emplean Synapse, iCUE o G HUB para sus efectos al pulsar. Solo se anota el nombre de
la tecla y el instante en :mod:`keyglow.input`; no se guarda texto, no se escribe nada
en disco y nada sale del PC. El gancho solo está activo mientras algún perfil en uso
tenga una capa reactiva.
"""

from __future__ import annotations

import sys
import threading

from .. import input as keyinput

# Códigos de tecla virtual de Windows -> ids de KeyGlow.
VK_TO_ID: dict[int, str] = {
    0x08: "BACKSPACE", 0x09: "TAB", 0x0D: "ENTER", 0x13: "PAUSE", 0x14: "CAPSLOCK", 0x1B: "ESC",
    0x20: "SPACE", 0x21: "PAGE_UP", 0x22: "PAGE_DOWN", 0x23: "END", 0x24: "HOME",
    0x25: "LEFT", 0x26: "UP", 0x27: "RIGHT", 0x28: "DOWN", 0x2C: "PRINTSCREEN",
    0x2D: "INSERT", 0x2E: "DELETE", 0x5B: "LWIN", 0x5C: "RWIN", 0x5D: "MENU",
    0x6A: "NUM_ASTERISK", 0x6B: "NUM_PLUS", 0x6D: "NUM_MINUS", 0x6E: "NUM_PERIOD", 0x6F: "NUM_SLASH",
    0x90: "NUMLOCK", 0x91: "SCROLLLOCK",
    0xA0: "LSHIFT", 0xA1: "RSHIFT", 0xA2: "LCTRL", 0xA3: "RCTRL", 0xA4: "LALT", 0xA5: "RALT",
    0xBA: "SEMICOLON", 0xBB: "EQUAL", 0xBC: "COMMA", 0xBD: "MINUS", 0xBE: "PERIOD", 0xBF: "SLASH",
    0xC0: "GRAVE", 0xDB: "LBRACKET", 0xDC: "BACKSLASH", 0xDD: "RBRACKET", 0xDE: "QUOTE",
}
VK_TO_ID.update({0x30 + i: str(i) for i in range(10)})
VK_TO_ID.update({0x41 + i: chr(0x41 + i) for i in range(26)})
VK_TO_ID.update({0x60 + i: f"NUM_{i}" for i in range(10)})
VK_TO_ID.update({0x70 + i: f"F{i + 1}" for i in range(12)})

_WH_KEYBOARD_LL = 13
_WM_KEYDOWN, _WM_KEYUP, _WM_SYSKEYDOWN, _WM_SYSKEYUP, _WM_QUIT = 0x100, 0x101, 0x104, 0x105, 0x12
_LLKHF_EXTENDED = 0x01


def caps_lock_on() -> bool:
    """Si Bloq Mayús está activado (solo Windows; en otros sistemas, siempre False)."""
    if sys.platform != "win32":
        return False
    import ctypes
    return bool(ctypes.windll.user32.GetKeyState(0x14) & 1)


_MODIFIER_VKS = (("ctrl", 0x11), ("shift", 0x10), ("alt", 0x12), ("win", 0x5B), ("win", 0x5C))


def held_modifiers() -> set[str]:
    """Modificadores que se mantienen ahora (``{"ctrl", "shift"}``). Solo pregunta a Windows
    por esas cinco teclas: no hace falta el gancho de teclado ni se mira lo que se escribe."""
    if sys.platform != "win32":
        return set()
    import ctypes
    state = ctypes.windll.user32.GetAsyncKeyState
    if state(0xA5) & 0x8000:  # Alt derecho = AltGr en muchos teclados (@, #, €...): se está escribiendo
        return set()
    return {name for name, vk in _MODIFIER_VKS if state(vk) & 0x8000}


def key_id(vk: int, flags: int) -> str | None:
    if vk == 0x0D and flags & _LLKHF_EXTENDED:
        return "NUM_ENTER"
    return VK_TO_ID.get(vk)


class KeyHook:
    def __init__(self):
        self._thread: threading.Thread | None = None
        self._tid = 0
        self._down: set[int] = set()

    @property
    def active(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if sys.platform != "win32" or self.active:
            return
        ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready,), name="keyglow-teclas",
                                        daemon=True)
        self._thread.start()
        ready.wait(2)

    def stop(self) -> None:
        if self.active and self._tid:
            import ctypes
            ctypes.windll.user32.PostThreadMessageW(self._tid, _WM_QUIT, 0, 0)
            self._thread.join(timeout=2)
        self._thread = None
        self._down.clear()

    def _run(self, ready: threading.Event) -> None:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        LRESULT = ctypes.c_ssize_t
        HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                        ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.c_size_t)]

        user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
        user32.CallNextHookEx.restype = LRESULT
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        def callback(n_code, w_param, l_param):
            if n_code == 0:
                info = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                if w_param in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
                    if info.vkCode not in self._down:  # ignora la autorrepetición
                        self._down.add(info.vkCode)
                        kid = key_id(info.vkCode, info.flags)
                        if kid:
                            keyinput.press(kid)
                elif w_param in (_WM_KEYUP, _WM_SYSKEYUP):
                    self._down.discard(info.vkCode)
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        proc = HOOKPROC(callback)  # se mantiene la referencia mientras dure el bucle
        self._tid = kernel32.GetCurrentThreadId()
        hook = user32.SetWindowsHookExW(_WH_KEYBOARD_LL, proc, kernel32.GetModuleHandleW(None), 0)
        ready.set()
        if not hook:
            return
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        user32.UnhookWindowsHookEx(hook)
