"""Nombres canónicos de teclas y traducción desde los nombres que usan otros programas.

Cada software llama distinto a la misma tecla ("Key: Left Control" en OpenRGB,
"ControlLeft" en navegadores, "LCTRL" en QMK...). Para poder importar perfiles de
otros teclados, todo se traduce a un identificador canónico (p. ej. ``LCTRL``).
"""

from __future__ import annotations

import re

LETTERS = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
DIGITS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

# Etiqueta corta para dibujar cada tecla en la vista previa.
LABELS = {
    "ESC": "Esc", "GRAVE": "`", "MINUS": "-", "EQUAL": "=", "BACKSPACE": "Bksp",
    "TAB": "Tab", "LBRACKET": "[", "RBRACKET": "]", "BACKSLASH": "\\",
    "CAPSLOCK": "Caps", "SEMICOLON": ";", "QUOTE": "'", "ENTER": "Enter",
    "LSHIFT": "Shift", "RSHIFT": "Shift", "COMMA": ",", "PERIOD": ".", "SLASH": "/",
    "LCTRL": "Ctrl", "RCTRL": "Ctrl", "LALT": "Alt", "RALT": "Alt",
    "LWIN": "Win", "RWIN": "Win", "MENU": "Menu", "FN": "Fn", "SPACE": "",
    "PRINTSCREEN": "PrS", "SCROLLLOCK": "ScL", "PAUSE": "Pau",
    "INSERT": "Ins", "HOME": "Hom", "PAGE_UP": "PgU", "DELETE": "Del", "END": "End",
    "PAGE_DOWN": "PgD", "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→",
    "NUMLOCK": "Num", "NUM_SLASH": "/", "NUM_ASTERISK": "*", "NUM_MINUS": "-",
    "NUM_PLUS": "+", "NUM_ENTER": "Ent", "NUM_PERIOD": ".",
}
for _d in DIGITS:
    LABELS[f"NUM_{_d}"] = _d


def label(key_id: str) -> str:
    return LABELS.get(key_id, key_id)


def _compact(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


ALIASES: dict[str, str] = {}


def _add(key_id: str, *names: str) -> None:
    for n in (key_id, *names):
        ALIASES[_compact(n)] = key_id


_add("ESC", "escape")
_add("GRAVE", "backquote", "backtick", "tilde", "grave accent")
_add("MINUS", "hyphen", "dash")
_add("EQUAL", "equals")
_add("BACKSPACE", "bksp", "back space")
_add("TAB")
_add("CAPSLOCK", "caps", "caps lock")
_add("ENTER", "return")
_add("LSHIFT", "left shift", "shift left", "shift")
_add("RSHIFT", "right shift", "shift right")
_add("LCTRL", "left ctrl", "left control", "control left", "lcontrol", "ctrl left", "ctrl", "control")
_add("RCTRL", "right ctrl", "right control", "control right", "rcontrol", "ctrl right")
_add("LALT", "left alt", "alt left", "alt", "left option", "loption")
_add("RALT", "right alt", "alt right", "alt gr", "altgr", "right option", "roption")
_add("LWIN", "left windows", "left win", "meta left", "lgui", "left gui", "left super",
     "lsuper", "win", "windows", "super", "left meta", "lmeta", "lcmd", "left command", "os left")
_add("RWIN", "right windows", "right win", "meta right", "rgui", "right gui", "right super",
     "rsuper", "right meta", "rmeta", "rcmd", "right command", "os right")
_add("MENU", "context menu", "apps", "application")
_add("FN", "function", "right fn", "left fn", "fn key")
# El Origins 65 expone la barra como tres LEDs: "Left Space", "Key: Space", "Right Space".
_add("SPACE", "spacebar", "space bar", "left space", "right space")
_add("LBRACKET", "bracket left", "left bracket", "open bracket")
_add("RBRACKET", "bracket right", "right bracket", "close bracket")
_add("BACKSLASH", "pipe")
_add("SEMICOLON")
_add("QUOTE", "apostrophe", "single quote")
_add("COMMA")
_add("PERIOD", "dot", "full stop")
_add("SLASH", "forward slash")
_add("PRINTSCREEN", "print screen", "prtsc", "prtscn", "print", "sysrq")
_add("SCROLLLOCK", "scroll lock", "scroll", "scrlk")
_add("PAUSE", "pause break", "break")
_add("INSERT", "ins")
_add("HOME")
_add("END")
_add("PAGE_UP", "page up", "pgup", "prior")
_add("PAGE_DOWN", "page down", "pgdn", "next")
_add("DELETE", "del")
_add("UP", "up arrow", "arrow up")
_add("DOWN", "down arrow", "arrow down")
_add("LEFT", "left arrow", "arrow left")
_add("RIGHT", "right arrow", "arrow right")
_add("NUMLOCK", "num lock", "numlk")

SYMBOLS = {
    "`": "GRAVE", "~": "GRAVE", "-": "MINUS", "_": "MINUS", "=": "EQUAL", "+": "EQUAL",
    "[": "LBRACKET", "{": "LBRACKET", "]": "RBRACKET", "}": "RBRACKET",
    "\\": "BACKSLASH", "|": "BACKSLASH", ";": "SEMICOLON", ":": "SEMICOLON",
    "'": "QUOTE", '"': "QUOTE", ",": "COMMA", "<": "COMMA", ".": "PERIOD", ">": "PERIOD",
    "/": "SLASH", "?": "SLASH",
}

_NUMPAD_REST = {
    "/": "SLASH", "divide": "SLASH", "slash": "SLASH",
    "*": "ASTERISK", "multiply": "ASTERISK", "asterisk": "ASTERISK",
    "-": "MINUS", "subtract": "MINUS", "minus": "MINUS",
    "+": "PLUS", "add": "PLUS", "plus": "PLUS",
    ".": "PERIOD", "decimal": "PERIOD", "period": "PERIOD", "del": "PERIOD",
    "enter": "ENTER", "return": "ENTER",
}
_NUMPAD_RE = re.compile(r"^(?:number\s*pad|numpad|keypad|kp|num)[\s_]*(.+)$")


def normalize(name: str) -> str | None:
    """Devuelve el id canónico de una tecla o ``None`` si no se reconoce."""
    s = name.strip()
    s = re.sub(r"^(?:key|led)\s*:\s*", "", s, flags=re.I)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)  # "\ (ANSI)" -> "\"
    if not s:
        return None
    if len(s) == 1:
        if s.isalnum():
            return s.upper()
        return SYMBOLS.get(s)
    c = _compact(s)
    if c in ALIASES:
        return ALIASES[c]
    m = _NUMPAD_RE.match(s.lower())
    if m:
        rest = m.group(1).strip()
        if rest.isdigit() and len(rest) == 1:
            return f"NUM_{rest}"
        if rest in _NUMPAD_REST:
            return f"NUM_{_NUMPAD_REST[rest]}"
    m = re.fullmatch(r"key([a-z])", c)  # códigos web: KeyA
    if m:
        return m.group(1).upper()
    m = re.fullmatch(r"digit([0-9])", c)  # códigos web: Digit1
    if m:
        return m.group(1)
    m = re.fullmatch(r"f([1-9]|1[0-9]|2[0-4])", c)
    if m:
        return f"F{m.group(1)}"
    return s.upper() if s.upper() in LABELS else None
