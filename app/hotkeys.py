"""Глобальні гарячі клавіші: спільний парсер і платформені бекенди.

Спільна частина — розбір рядка комбінації та зіставлення ідентифікаторів із
функціями. Платформна частина ізольована в трьох маленьких бекендах:
MacOS (Carbon), Windows (Win32) і заглушка для інших систем.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QWidget

from app.i18n import tr

logger = logging.getLogger(__name__)

# Портативні назви модифікаторів (як їх пише QKeySequence::toString(PortableText)).
# На macOS Qt зіставляє Ctrl з Command, а Meta з Control — тому тут ctrl → cmdKey.
_MODIFIER_ALIASES = {
    "ctrl": "ctrl",
    "control": "ctrl",
    "cmd": "ctrl",
    "command": "ctrl",
    "shift": "shift",
    "alt": "alt",
    "option": "alt",
    "meta": "meta",
    "win": "meta",
    "windows": "meta",
    "super": "meta",
}

_KEY_ALIASES = {
    "esc": "Escape",
    "enter": "Return",
    "spacebar": "Space",
    "del": "Delete",
    "backspace": "Delete",
    "pgup": "PageUp",
    "pgdown": "PageDown",
}

_NAMED_KEYS = {
    name.casefold(): name
    for name in (
        "Return",
        "Space",
        "Escape",
        "Tab",
        "Delete",
        "Home",
        "End",
        "PageUp",
        "PageDown",
        "Left",
        "Right",
        "Up",
        "Down",
        "Plus",
    )
}
_NAMED_KEYS.update({f"f{i}".casefold(): f"F{i}" for i in range(1, 13)})


@dataclass(frozen=True)
class Hotkey:
    """Розібрана комбінація: набір модифікаторів і одна клавіша."""

    modifiers: frozenset[str]
    key: str


def parse_hotkey(sequence: str) -> Hotkey | None:
    """Перетворює 'Ctrl+Shift+Alt+H' на структуру, придатну для обох ОС."""
    sequence = sequence.strip()
    # QKeySequence пише чисту '+' як 'Ctrl++' — інакше розбір по '+' ламається.
    if sequence.endswith("++"):
        sequence = sequence[:-1] + "Plus"
    parts = [part.strip().casefold() for part in sequence.split("+") if part.strip()]
    if not parts:
        return None

    modifiers: set[str] = set()
    keys: list[str] = []
    for part in parts:
        if part in _MODIFIER_ALIASES:
            modifiers.add(_MODIFIER_ALIASES[part])
        else:
            keys.append(part)
    if len(keys) != 1:
        return None

    raw = keys[0]
    key = _KEY_ALIASES.get(raw) or _NAMED_KEYS.get(raw) or raw.upper()
    return Hotkey(modifiers=frozenset(modifiers), key=key)


class _Backend:
    """Загальний інтерфейс бекенда; `error` пояснює останню невдачу."""

    def __init__(self) -> None:
        self.error = ""

    def register(self, hotkey: Hotkey, hotkey_id: int) -> bool:
        raise NotImplementedError

    def unregister_all(self) -> None:
        raise NotImplementedError


# --- macOS (Carbon RegisterEventHotKey) -------------------------------------

_MAC_MODIFIERS = {
    "ctrl": 1 << 8,  # cmdKey — Command, бо Qt вважає Ctrl портативним Cmd
    "shift": 1 << 9,  # shiftKey
    "alt": 1 << 11,  # optionKey (1 << 10 — це alphaLock/Caps Lock)
    "meta": 1 << 12,  # controlKey — Qt вважає Meta фізичним Control
}

_MAC_KEYCODES = {
    "A": 0x00,
    "S": 0x01,
    "D": 0x02,
    "F": 0x03,
    "H": 0x04,
    "G": 0x05,
    "Z": 0x06,
    "X": 0x07,
    "C": 0x08,
    "V": 0x09,
    "B": 0x0B,
    "Q": 0x0C,
    "W": 0x0D,
    "E": 0x0E,
    "R": 0x0F,
    "Y": 0x10,
    "T": 0x11,
    "1": 0x12,
    "2": 0x13,
    "3": 0x14,
    "4": 0x15,
    "6": 0x16,
    "5": 0x17,
    "=": 0x18,
    "9": 0x19,
    "7": 0x1A,
    "-": 0x1B,
    "8": 0x1C,
    "0": 0x1D,
    "]": 0x1E,
    "O": 0x1F,
    "U": 0x20,
    "[": 0x21,
    "I": 0x22,
    "P": 0x23,
    "L": 0x25,
    "J": 0x26,
    "'": 0x27,
    "K": 0x28,
    ";": 0x29,
    "\\": 0x2A,
    ",": 0x2B,
    ".": 0x2C,
    "/": 0x2D,
    "N": 0x2E,
    "M": 0x2F,
    "Return": 0x24,
    "Tab": 0x30,
    "Space": 0x31,
    "Delete": 0x33,
    "Escape": 0x35,
    "F1": 0x7A,
    "F2": 0x78,
    "F3": 0x63,
    "F4": 0x76,
    "F5": 0x60,
    "F6": 0x61,
    "F7": 0x62,
    "F8": 0x64,
    "F9": 0x65,
    "F10": 0x6D,
    "F11": 0x6F,
    "F12": 0x69,
    "Left": 0x7B,
    "Right": 0x7C,
    "Down": 0x7D,
    "Up": 0x7E,
    "Home": 0x73,
    "End": 0x77,
    "PageUp": 0x74,
    "PageDown": 0x79,
    "`": 0x0A,
}


def _four(text: bytes) -> int:
    """Пакує чотири символи в UInt32 (FourCharCode)."""
    return int.from_bytes(text, "big")


class _EventTypeSpec(ctypes.Structure):
    _fields_ = [("event_class", ctypes.c_uint32), ("event_kind", ctypes.c_uint32)]


class _EventHotKeyID(ctypes.Structure):
    _fields_ = [("signature", ctypes.c_uint32), ("id", ctypes.c_uint32)]


class _MacBackend(_Backend):
    """Реєструє комбінації через Carbon і опитує чергу подій QTimer-ом."""

    _SIGNATURE = _four(b"CMHK")
    _HOTKEY_PRESSED = 5
    _DIRECT_PARAMETER = _four(b"----")
    _HOTKEY_ID_TYPE = _four(b"hkid")

    def __init__(self, trigger: Callable[[int], None]) -> None:
        super().__init__()
        self._trigger = trigger
        self._refs: dict[int, ctypes.c_void_p] = {}
        path = "/System/Library/Frameworks/Carbon.framework/Carbon"
        self._carbon = ctypes.CDLL(path)
        self._carbon.GetApplicationEventTarget.argtypes = []
        self._carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
        self._carbon.RegisterEventHotKey.argtypes = [
            ctypes.c_uint32,
            ctypes.c_uint32,
            _EventHotKeyID,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._carbon.RegisterEventHotKey.restype = ctypes.c_int32
        self._carbon.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]
        self._carbon.UnregisterEventHotKey.restype = ctypes.c_int32
        self._carbon.ReceiveNextEvent.argtypes = [
            ctypes.c_uint32,
            ctypes.POINTER(_EventTypeSpec),
            ctypes.c_double,
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self._carbon.ReceiveNextEvent.restype = ctypes.c_int32
        self._carbon.GetEventParameter.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.c_void_p,
        ]
        self._carbon.GetEventParameter.restype = ctypes.c_int32
        self._carbon.ReleaseEvent.argtypes = [ctypes.c_void_p]

        self._target = self._carbon.GetApplicationEventTarget()
        self._spec = _EventTypeSpec(_four(b"keyb"), self._HOTKEY_PRESSED)
        self._timer = QTimer()
        self._timer.timeout.connect(self._poll)

    def register(self, hotkey: Hotkey, hotkey_id: int) -> bool:
        modifiers = 0
        for name in hotkey.modifiers:
            modifiers |= _MAC_MODIFIERS.get(name, 0)
        keycode = _MAC_KEYCODES.get(hotkey.key)
        if keycode is None:
            self.error = tr("hotkey.error.key", key=hotkey.key)
            return False

        ref = ctypes.c_void_p()
        status = self._carbon.RegisterEventHotKey(
            keycode,
            modifiers,
            _EventHotKeyID(self._SIGNATURE, hotkey_id),
            self._target,
            0,
            ctypes.byref(ref),
        )
        if status != 0:
            self.error = tr("hotkey.error.busy", key=hotkey.key)
            return False

        self._refs[hotkey_id] = ref
        if not self._timer.isActive():
            self._timer.start(50)
        return True

    def unregister_all(self) -> None:
        for ref in self._refs.values():
            self._carbon.UnregisterEventHotKey(ref)
        self._refs.clear()
        self._timer.stop()

    def _poll(self) -> None:
        """Забираємо Carbon-події з черги й викликаємо відповідний callback."""
        event = ctypes.c_void_p()
        status = self._carbon.ReceiveNextEvent(
            1, ctypes.byref(self._spec), 0.0, True, ctypes.byref(event)
        )
        if status != 0 or not event.value:
            return

        hotkey_id = _EventHotKeyID()
        status = self._carbon.GetEventParameter(
            event,
            self._DIRECT_PARAMETER,
            self._HOTKEY_ID_TYPE,
            None,
            ctypes.sizeof(hotkey_id),
            None,
            ctypes.byref(hotkey_id),
        )
        self._carbon.ReleaseEvent(event)
        if status == 0 and hotkey_id.signature == self._SIGNATURE:
            self._trigger(hotkey_id.id)


# --- Windows (Win32 RegisterHotKey) -----------------------------------------

_WIN_MODIFIERS = {
    "ctrl": 0x0002,  # MOD_CONTROL
    "shift": 0x0004,  # MOD_SHIFT
    "alt": 0x0001,  # MOD_ALT
    "meta": 0x0008,  # MOD_WIN
}
_MOD_NOREPEAT = 0x4000
_WM_HOTKEY = 0x0312

_WIN_KEYCODES = {
    **{chr(code): code for code in range(ord("A"), ord("Z") + 1)},
    **{str(digit): 0x30 + digit for digit in range(10)},
    **{f"F{i}": 0x6F + i for i in range(1, 13)},
    "Return": 0x0D,
    "Tab": 0x09,
    "Space": 0x20,
    "Escape": 0x1B,
    "Delete": 0x2E,
    "Home": 0x24,
    "End": 0x23,
    "PageUp": 0x21,
    "PageDown": 0x22,
    "Left": 0x25,
    "Up": 0x26,
    "Right": 0x27,
    "Down": 0x28,
    ";": 0xBA,  # VK_OEM_1
    "=": 0xBB,  # VK_OEM_PLUS
    ",": 0xBC,  # VK_OEM_COMMA
    "-": 0xBD,  # VK_OEM_MINUS
    ".": 0xBE,  # VK_OEM_PERIOD
    "/": 0xBF,  # VK_OEM_2
    "`": 0xC0,  # VK_OEM_3
    "[": 0xDB,  # VK_OEM_4
    "\\": 0xDC,  # VK_OEM_5
    "]": 0xDD,  # VK_OEM_6
    "'": 0xDE,  # VK_OEM_7
}

# Зсунуті символи використовують ті самі фізичні клавіші, що й їх основа.
# Спільний список для обох ОС — QKeySequence пише саме зсунутий символ.
_SHIFTED_KEY_ALIASES = {
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "-",
    "+": "=",
    "Plus": "=",
    "{": "[",
    "}": "]",
    "|": "\\",
    ":": ";",
    '"': "'",
    "<": ",",
    ">": ".",
    "?": "/",
    "~": "`",
}
for _shifted, _base in _SHIFTED_KEY_ALIASES.items():
    _MAC_KEYCODES.setdefault(_shifted, _MAC_KEYCODES[_base])
    _WIN_KEYCODES.setdefault(_shifted, _WIN_KEYCODES[_base])


class _MSG(ctypes.Structure):
    """Мінімальна копія структури MSG — вистачає полів message і wParam."""

    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint32),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_ssize_t),
        ("time", ctypes.c_uint32),
        ("pt", ctypes.c_long * 2),
        ("lPrivate", ctypes.c_uint32),
    ]


class _HotkeyWindow(QWidget):
    """Невидиме нативне вікно, яке приймає WM_HOTKEY від системи."""

    triggered = Signal(int)

    def nativeEvent(self, eventType, message):
        try:
            pointer = int(message)
        except (TypeError, ValueError):
            return super().nativeEvent(eventType, message)
        msg = ctypes.cast(pointer, ctypes.POINTER(_MSG)).contents
        if msg.message == _WM_HOTKEY:
            self.triggered.emit(int(msg.wParam))
            return True, 0
        return super().nativeEvent(eventType, message)


class _WinBackend(_Backend):
    """Реєструє комбінації через RegisterHotKey на прихованому вікні."""

    def __init__(self, trigger: Callable[[int], None]) -> None:
        super().__init__()
        self._user32 = ctypes.windll.user32
        self._user32.RegisterHotKey.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_uint32,
            ctypes.c_uint32,
        ]
        self._user32.RegisterHotKey.restype = ctypes.c_bool
        self._user32.UnregisterHotKey.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self._user32.UnregisterHotKey.restype = ctypes.c_bool

        self._window = _HotkeyWindow()
        self._window.triggered.connect(trigger)
        self._hwnd = ctypes.c_void_p(int(self._window.winId()))
        self._ids: set[int] = set()

    def register(self, hotkey: Hotkey, hotkey_id: int) -> bool:
        modifiers = _MOD_NOREPEAT
        for name in hotkey.modifiers:
            modifiers |= _WIN_MODIFIERS.get(name, 0)
        keycode = _WIN_KEYCODES.get(hotkey.key)
        if keycode is None:
            self.error = tr("hotkey.error.key", key=hotkey.key)
            return False

        if not self._user32.RegisterHotKey(self._hwnd, hotkey_id, modifiers, keycode):
            self.error = tr("hotkey.error.busy", key=hotkey.key)
            return False

        self._ids.add(hotkey_id)
        return True

    def unregister_all(self) -> None:
        for hotkey_id in self._ids:
            self._user32.UnregisterHotKey(self._hwnd, hotkey_id)
        self._ids.clear()


class _NullBackend(_Backend):
    """Коректна поведінка на непідтримуваних платформах."""

    def register(self, hotkey: Hotkey, hotkey_id: int) -> bool:
        self.error = tr("hotkey.error.platform")
        return False

    def unregister_all(self) -> None:
        return None


def _make_backend(trigger: Callable[[int], None]) -> _Backend:
    if sys.platform == "darwin":
        return _MacBackend(trigger)
    if sys.platform == "win32":
        return _WinBackend(trigger)
    return _NullBackend()


class HotkeyManager(QObject):
    """Реєструє глобальні комбінації та викликає callback-и за ідентифікатором."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._backend = _make_backend(self._triggered)
        self._callbacks: dict[int, Callable[[], None]] = {}
        self._next_id = 1
        self.last_error = ""

    def register(self, sequence: str, callback: Callable[[], None]) -> bool:
        """Повертає True, якщо комбінацію зареєстровано в системі."""
        hotkey = parse_hotkey(sequence)
        if hotkey is None:
            self.last_error = tr("hotkey.error.invalid")
            return False

        hotkey_id = self._next_id
        self._next_id += 1
        self._backend.error = ""
        if not self._backend.register(hotkey, hotkey_id):
            self.last_error = self._backend.error or tr("hotkey.error.invalid")
            return False

        self._callbacks[hotkey_id] = callback
        return True

    def unregister_all(self) -> None:
        """Знімає всі реєстрації (викликається перед закриттям або зміною)."""
        self._backend.unregister_all()
        self._callbacks.clear()

    def _triggered(self, hotkey_id: int) -> None:
        callback = self._callbacks.get(hotkey_id)
        if callback is not None:
            callback()
