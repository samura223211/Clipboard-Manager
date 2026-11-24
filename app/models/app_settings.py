"""Налаштування застосунку, які зберігаються в SQLite."""

from dataclasses import dataclass

from app.i18n import DEFAULT_LANGUAGE, LANGUAGE_NAMES

DEFAULT_MAX_HISTORY = 100
MIN_HISTORY = 1
MAX_HISTORY_LIMIT = 10_000

DEFAULT_TOGGLE_HOTKEY = "Ctrl+Shift+Alt+H"
DEFAULT_CLEAR_HOTKEY = "Ctrl+Shift+Alt+K"


@dataclass
class AppSettings:
    """Параметри історії, автозапуску та гарячих клавіш."""

    max_history: int = DEFAULT_MAX_HISTORY
    autostart: bool = False
    toggle_hotkey: str = DEFAULT_TOGGLE_HOTKEY
    clear_hotkey: str = DEFAULT_CLEAR_HOTKEY
    language: str = DEFAULT_LANGUAGE

    @classmethod
    def from_dict(cls, values: dict[str, str]) -> "AppSettings":
        """Безпечно зчитує значення з БД, підміняючи пошкоджені дефолтами."""
        try:
            max_history = int(values.get("max_history", DEFAULT_MAX_HISTORY))
        except (TypeError, ValueError):
            max_history = DEFAULT_MAX_HISTORY
        max_history = max(MIN_HISTORY, min(MAX_HISTORY_LIMIT, max_history))

        raw = str(values.get("autostart", "0")).strip().lower()
        autostart = raw in {"1", "true", "yes", "on"}

        language = values.get("language") or DEFAULT_LANGUAGE
        if language not in LANGUAGE_NAMES:
            language = DEFAULT_LANGUAGE

        return cls(
            max_history=max_history,
            autostart=autostart,
            toggle_hotkey=values.get("toggle_hotkey") or DEFAULT_TOGGLE_HOTKEY,
            clear_hotkey=values.get("clear_hotkey") or DEFAULT_CLEAR_HOTKEY,
            language=language,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "max_history": str(self.max_history),
            "autostart": "1" if self.autostart else "0",
            "toggle_hotkey": self.toggle_hotkey,
            "clear_hotkey": self.clear_hotkey,
            "language": self.language,
        }
