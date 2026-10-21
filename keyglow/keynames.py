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
    # ISO: la tecla junto a Shift izquierdo y la de al lado de Enter
    "NONUS_BACKSLASH": "\\", "NONUS_HASH": "#",
    "MEDIA_PLAY": "⏯", "MEDIA_NEXT": "⏭", "MEDIA_PREV": "⏮", "MEDIA_STOP": "⏹",
    "MUTE": "🔇", "VOL_UP": "🔊", "VOL_DOWN": "🔉",
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
_add("FN", "function", "right fn", "left fn", "fn key", "mo(1)")
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
_add("NONUS_BACKSLASH", "intl backslash", "iso backslash", "nubs", "non us backslash")
_add("NONUS_HASH", "iso hash", "nuhs", "non us hash", "pound", "iso pound")
_add("MEDIA_PLAY", "media play pause", "media play", "play pause", "mply", "play")
_add("MEDIA_NEXT", "media next", "media next track", "next track", "mnxt", "media track next")
_add("MEDIA_PREV", "media previous", "media prev", "media previous track", "previous track", "mprv", "media track previous")
_add("MEDIA_STOP", "media stop", "stop", "mstp")
_add("MUTE", "media mute", "audio volume mute", "audio mute", "volume mute", "mute")
_add("VOL_UP", "volume up", "audio volume up", "media volume up", "volu")
_add("VOL_DOWN", "volume down", "audio volume down", "media volume down", "vold")

SYMBOLS = {
    "`": "GRAVE", "~": "GRAVE", "-": "MINUS", "_": "MINUS", "=": "EQUAL", "+": "EQUAL",
    "[": "LBRACKET", "{": "LBRACKET", "]": "RBRACKET", "}": "RBRACKET",
    "\\": "BACKSLASH", "|": "BACKSLASH", ";": "SEMICOLON", ":": "SEMICOLON",
    "'": "QUOTE", '"': "QUOTE", ",": "COMMA", "<": "COMMA", ".": "PERIOD", ">": "PERIOD",
    "/": "SLASH", "?": "SLASH", "#": "NONUS_HASH",
}

# Abreviaturas de QMK (sin el prefijo KC_) que no salen de los alias generales.
QMK = {
    "lctl": "LCTRL", "rctl": "RCTRL", "lsft": "LSHIFT", "rsft": "RSHIFT", "lopt": "LALT",
    "ropt": "RALT", "lcmd": "LWIN", "rcmd": "RWIN", "spc": "SPACE", "ent": "ENTER",
    "bspc": "BACKSPACE", "caps": "CAPSLOCK", "grv": "GRAVE", "mins": "MINUS", "eql": "EQUAL",
    "lbrc": "LBRACKET", "rbrc": "RBRACKET", "bsls": "BACKSLASH", "scln": "SEMICOLON",
    "quot": "QUOTE", "comm": "COMMA", "dot": "PERIOD", "slsh": "SLASH", "pscr": "PRINTSCREEN",
    "scrl": "SCROLLLOCK", "brk": "PAUSE", "paus": "PAUSE", "pgup": "PAGE_UP", "pgdn": "PAGE_DOWN",
    "app": "MENU", "num": "NUMLOCK", "psls": "NUM_SLASH", "past": "NUM_ASTERISK",
    "pmns": "NUM_MINUS", "ppls": "NUM_PLUS", "pent": "NUM_ENTER", "pdot": "NUM_PERIOD",
    "mute": "MUTE", "volu": "VOL_UP", "vold": "VOL_DOWN", "mply": "MEDIA_PLAY",
    "mnxt": "MEDIA_NEXT", "mprv": "MEDIA_PREV", "mstp": "MEDIA_STOP",
    "nubs": "NONUS_BACKSLASH", "nuhs": "NONUS_HASH", "up": "UP", "down": "DOWN",
    "left": "LEFT", "rght": "RIGHT", "ins": "INSERT", "del": "DELETE",
    **{f"p{d}": f"NUM_{d}" for d in DIGITS},
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
    if re.fullmatch(r"\\\s*\(iso\)", s, flags=re.I):  # OpenRGB: "Key: \ (ISO)"
        return "NONUS_BACKSLASH"
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)  # "\ (ANSI)" -> "\"
    if not s:
        return None
    if len(s) == 1:
        if s.isalnum():
            return s.upper()
        return SYMBOLS.get(s)
    m = re.fullmatch(r"(?:media\s*)?volume\s*([+-])", s, flags=re.I)  # OpenRGB: "Media Volume +"
    if m:
        return "VOL_UP" if m.group(1) == "+" else "VOL_DOWN"
    if re.match(r"kc_", s, flags=re.I):  # QMK: KC_A, KC_LCTL, KC_P1...
        return normalize(s[3:]) or QMK.get(_compact(s[3:]))
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


# ---------------------------------------------------------------------------
# Nombres en otros programas, para exportar (lo inverso de ``normalize``)
# ---------------------------------------------------------------------------
_SPECIAL = {
    # id: (OpenRGB, código web, QMK)
    "ESC": ("Escape", "Escape", "KC_ESC"), "GRAVE": ("`", "Backquote", "KC_GRV"),
    "MINUS": ("-", "Minus", "KC_MINS"), "EQUAL": ("=", "Equal", "KC_EQL"),
    "BACKSPACE": ("Backspace", "Backspace", "KC_BSPC"), "TAB": ("Tab", "Tab", "KC_TAB"),
    "LBRACKET": ("[", "BracketLeft", "KC_LBRC"), "RBRACKET": ("]", "BracketRight", "KC_RBRC"),
    "BACKSLASH": ("\\ (ANSI)", "Backslash", "KC_BSLS"), "CAPSLOCK": ("Caps Lock", "CapsLock", "KC_CAPS"),
    "SEMICOLON": (";", "Semicolon", "KC_SCLN"), "QUOTE": ("'", "Quote", "KC_QUOT"),
    "ENTER": ("Enter", "Enter", "KC_ENT"), "LSHIFT": ("Left Shift", "ShiftLeft", "KC_LSFT"),
    "RSHIFT": ("Right Shift", "ShiftRight", "KC_RSFT"), "COMMA": (",", "Comma", "KC_COMM"),
    "PERIOD": (".", "Period", "KC_DOT"), "SLASH": ("/", "Slash", "KC_SLSH"),
    "LCTRL": ("Left Control", "ControlLeft", "KC_LCTL"), "RCTRL": ("Right Control", "ControlRight", "KC_RCTL"),
    "LALT": ("Left Alt", "AltLeft", "KC_LALT"), "RALT": ("Right Alt", "AltRight", "KC_RALT"),
    "LWIN": ("Left Windows", "MetaLeft", "KC_LGUI"), "RWIN": ("Right Windows", "MetaRight", "KC_RGUI"),
    "MENU": ("Menu", "ContextMenu", "KC_APP"), "FN": ("Right Fn", "Fn", "MO(1)"),
    "SPACE": ("Space", "Space", "KC_SPC"), "PRINTSCREEN": ("Print Screen", "PrintScreen", "KC_PSCR"),
    "SCROLLLOCK": ("Scroll Lock", "ScrollLock", "KC_SCRL"), "PAUSE": ("Pause/Break", "Pause", "KC_PAUS"),
    "INSERT": ("Insert", "Insert", "KC_INS"), "HOME": ("Home", "Home", "KC_HOME"),
    "PAGE_UP": ("Page Up", "PageUp", "KC_PGUP"), "DELETE": ("Delete", "Delete", "KC_DEL"),
    "END": ("End", "End", "KC_END"), "PAGE_DOWN": ("Page Down", "PageDown", "KC_PGDN"),
    "UP": ("Up Arrow", "ArrowUp", "KC_UP"), "DOWN": ("Down Arrow", "ArrowDown", "KC_DOWN"),
    "LEFT": ("Left Arrow", "ArrowLeft", "KC_LEFT"), "RIGHT": ("Right Arrow", "ArrowRight", "KC_RGHT"),
    "NUMLOCK": ("Num Lock", "NumLock", "KC_NUM"), "NUM_SLASH": ("Number Pad /", "NumpadDivide", "KC_PSLS"),
    "NUM_ASTERISK": ("Number Pad *", "NumpadMultiply", "KC_PAST"),
    "NUM_MINUS": ("Number Pad -", "NumpadSubtract", "KC_PMNS"), "NUM_PLUS": ("Number Pad +", "NumpadAdd", "KC_PPLS"),
    "NUM_ENTER": ("Number Pad Enter", "NumpadEnter", "KC_PENT"), "NUM_PERIOD": ("Number Pad .", "NumpadDecimal", "KC_PDOT"),
    "NONUS_BACKSLASH": ("\\ (ISO)", "IntlBackslash", "KC_NUBS"), "NONUS_HASH": ("#", "Backslash", "KC_NUHS"),
    "MEDIA_PLAY": ("Media Play/Pause", "MediaPlayPause", "KC_MPLY"),
    "MEDIA_NEXT": ("Media Next", "MediaTrackNext", "KC_MNXT"),
    "MEDIA_PREV": ("Media Previous", "MediaTrackPrevious", "KC_MPRV"),
    "MEDIA_STOP": ("Media Stop", "MediaStop", "KC_MSTP"), "MUTE": ("Media Mute", "AudioVolumeMute", "KC_MUTE"),
    "VOL_UP": ("Media Volume +", "AudioVolumeUp", "KC_VOLU"), "VOL_DOWN": ("Media Volume -", "AudioVolumeDown", "KC_VOLD"),
}
NAME_STYLES = ("keyglow", "openrgb", "web", "qmk")


def external_name(key_id: str, style: str) -> str:
    """Nombre de la tecla ``key_id`` en otro programa: ``openrgb``, ``web`` o ``qmk``."""
    if style == "keyglow":
        return key_id
    col = {"openrgb": 0, "web": 1, "qmk": 2}[style]
    if key_id in _SPECIAL:
        name = _SPECIAL[key_id][col]
    elif len(key_id) == 1 and key_id.isalpha():
        name = (key_id, f"Key{key_id}", f"KC_{key_id}")[col]
    elif len(key_id) == 1 and key_id.isdigit():
        name = (key_id, f"Digit{key_id}", f"KC_{key_id}")[col]
    elif key_id.startswith("NUM_") and key_id[4:].isdigit():
        d = key_id[4:]
        name = (f"Number Pad {d}", f"Numpad{d}", f"KC_P{d}")[col]
    elif re.fullmatch(r"F\d+", key_id):
        name = (key_id, key_id, f"KC_{key_id}")[col]
    else:
        name = key_id
    return f"Key: {name}" if style == "openrgb" else name
