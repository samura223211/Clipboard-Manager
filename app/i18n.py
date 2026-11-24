"""Централізована система перекладів інтерфейсу.

Щоб додати мову: додати словник у TRANSLATIONS та назву в LANGUAGE_NAMES.
Англійська є повною і служить запасним варіантом для будь-якого ключа.
"""

from PySide6.QtCore import QObject, Signal

DEFAULT_LANGUAGE = "uk"
FALLBACK_LANGUAGE = "en"

# Назви мов пишемо рідною мовою — так вони зрозумілі у випадаючому списку.
LANGUAGE_NAMES: dict[str, str] = {
    "uk": "Українська",
    "en": "English",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "Clipboard Manager",
        "app.subtitle": "Clipboard history",
        "nav.section": "SECTIONS",
        "nav.all": "All entries",
        "nav.pinned": "Pinned",
        "nav.settings": "Settings",
        "nav.version": "v{version} · demo version",
        "tray.open": "Open app",
        "tray.quit": "Quit",
        "entries.all": "All entries",
        "entries.pinned": "Pinned",
        "entries.subtitle": "New entries appear automatically",
        "entries.clear": "Clear history",
        "entries.empty.title": "No matches found",
        "entries.empty.hint": "Try a different query",
        "entries.empty.history": "History is empty",
        "entries.empty.history_hint": "Copy any text and it will appear here",
        "search.placeholder": "Search history…",
        "search.clear": "Clear search",
        "card.pinned": "Pinned",
        "card.copy": "Copy text",
        "card.pin": "Pin",
        "card.unpin": "Unpin",
        "card.delete": "Delete entry",
        "card.today": "Today, {clock}",
        "settings.title": "Settings",
        "settings.subtitle": "Preferences are saved automatically in the database",
        "settings.limit": "Maximum number of entries",
        "settings.limit.suffix": " entries",
        "settings.autostart": "Run at system startup",
        "settings.autostart.note": "Autostart will take effect after the next sign-in.",
        "settings.hotkeys": "Hotkeys",
        "settings.hotkeys.toggle": "Show / hide window",
        "settings.hotkeys.clear": "Clear search field",
        "settings.hotkeys.global_tip": "Global shortcut — works in any application",
        "settings.hotkeys.note": (
            "Press the desired keys in the field — shortcuts are saved with "
            "other settings."
        ),
        "settings.language": "Language",
        "settings.save": "Save settings",
        "settings.saved": "Settings saved",
        "settings.saved.autostart_failed": (
            "Saved, but autostart could not be changed"
        ),
        "settings.saved.hotkey_failed": (
            "Saved, but the global shortcut could not be registered"
        ),
        "settings.error.both": "Specify both key combinations.",
        "settings.error.modifier": "Add Ctrl, Shift or Alt to the combination.",
        "settings.error.conflict": "The combinations must be different.",
        "dialog.clear.title": "Clear history",
        "dialog.clear.text": "Delete the entire copied-text history?",
        "warning.hotkey": (
            "Could not register the global shortcut «{combo}» for showing the "
            "window.\nIt may already be used by another application. Open "
            "Settings and choose a different combination."
        ),
        "warning.hotkey.saved": (
            "Could not register the global shortcut «{combo}» for showing the "
            "window.\nIt may already be used by another application. Try a "
            "different one."
        ),
        "hotkey.error.invalid": "Invalid key combination.",
        "hotkey.error.key": "The {key} key cannot be registered.",
        "hotkey.error.busy": (
            "The {key} combination is already used by another application or "
            "the system denied registration."
        ),
        "hotkey.error.platform": (
            "Global hotkeys are supported on macOS and Windows."
        ),
    },
    "uk": {
        "app.subtitle": "Історія буфера обміну",
        "nav.section": "РОЗДІЛИ",
        "nav.all": "Усі записи",
        "nav.pinned": "Закріплені",
        "nav.settings": "Налаштування",
        "nav.version": "v{version} · демо-версія",
        "tray.open": "Відкрити програму",
        "tray.quit": "Вихід",
        "entries.all": "Усі записи",
        "entries.pinned": "Закріплені",
        "entries.subtitle": "Нові записи з’являються автоматично",
        "entries.clear": "Очистити історію",
        "entries.empty.title": "Нічого не знайдено",
        "entries.empty.hint": "Спробуйте інший запит",
        "entries.empty.history": "Історія порожня",
        "entries.empty.history_hint": "Скопіюйте будь-який текст, і він з’явиться тут",
        "search.placeholder": "Пошук у історії…",
        "search.clear": "Очистити пошук",
        "card.pinned": "Закріплено",
        "card.copy": "Скопіювати текст",
        "card.pin": "Закріпити",
        "card.unpin": "Відкріпити",
        "card.delete": "Видалити запис",
        "card.today": "Сьогодні, {clock}",
        "settings.title": "Налаштування",
        "settings.subtitle": "Параметри зберігаються автоматично у базі даних",
        "settings.limit": "Максимальна кількість записів",
        "settings.limit.suffix": " записів",
        "settings.autostart": "Запускати при старті системи",
        "settings.autostart.note": (
            "Автозапуск набуде чинності після наступного входу в систему."
        ),
        "settings.hotkeys": "Гарячі клавіші",
        "settings.hotkeys.toggle": "Показати / приховати вікно",
        "settings.hotkeys.clear": "Очистити поле пошуку",
        "settings.hotkeys.global_tip": "Глобальна комбінація — діє в будь-якій програмі",
        "settings.hotkeys.note": (
            "Натисніть потрібні клавіші у полі — комбінації зберігаються разом "
            "з іншими налаштуваннями."
        ),
        "settings.language": "Мова",
        "settings.save": "Зберегти налаштування",
        "settings.saved": "Налаштування збережено",
        "settings.saved.autostart_failed": (
            "Збережено, але не вдалося змінити автозапуск"
        ),
        "settings.saved.hotkey_failed": (
            "Збережено, але глобальну комбінацію не зареєстровано"
        ),
        "settings.error.both": "Вкажіть обидві комбінації клавіш.",
        "settings.error.modifier": "Додайте до комбінації Ctrl, Shift або Alt.",
        "settings.error.conflict": "Комбінації мають бути різними.",
        "dialog.clear.title": "Очистити історію",
        "dialog.clear.text": "Видалити всю історію скопійованого тексту?",
        "warning.hotkey": (
            "Не вдалося зареєструвати глобальну комбінацію «{combo}» для показу "
            "вікна.\nМожливо, її вже використовує інша програма. Відкрийте "
            "«Налаштування» й виберіть іншу комбінацію."
        ),
        "warning.hotkey.saved": (
            "Не вдалося зареєструвати глобальну комбінацію «{combo}» для показу "
            "вікна.\nМожливо, її вже використовує інша програма. Спробуйте іншу."
        ),
        "hotkey.error.invalid": "Некоректна комбінація клавіш.",
        "hotkey.error.key": "Клавішу {key} неможливо зареєструвати.",
        "hotkey.error.busy": (
            "Комбінацію {key} вже використовує інша програма або система не "
            "дозволила її реєстрацію."
        ),
        "hotkey.error.platform": (
            "Глобальні гарячі клавіші підтримуються на macOS і Windows."
        ),
    },
}


_language = DEFAULT_LANGUAGE


def tr(message_key: str, **kwargs: object) -> str:
    """Повертає переклад ключа; за відсутності — англійський або сам ключ."""
    text = TRANSLATIONS.get(_language, {}).get(message_key)
    if text is None:
        text = TRANSLATIONS[FALLBACK_LANGUAGE].get(message_key, message_key)
    return text.format(**kwargs) if kwargs else text


class I18n(QObject):
    """Тримає поточну мову й сповіщає віджети про зміну."""

    language_changed = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._language = DEFAULT_LANGUAGE

    @property
    def language(self) -> str:
        return self._language

    @property
    def languages(self) -> dict[str, str]:
        return dict(LANGUAGE_NAMES)

    def set_language(self, code: str) -> None:
        code = code if code in TRANSLATIONS else DEFAULT_LANGUAGE
        if code == self._language:
            return
        global _language
        self._language = code
        _language = code
        self.language_changed.emit(code)


i18n = I18n()
