"""Сховище записів: операції в пам'яті + постійне збереження в SQLite."""

from dataclasses import replace

from PySide6.QtCore import QObject, Signal

from app.models.app_settings import DEFAULT_MAX_HISTORY, AppSettings
from app.models.clipboard_entry import ClipboardEntry
from app.storage.history_repository import HistoryRepository

# Залишаємо назву для сумісності; реальне значення тепер беремо з налаштувань.
MAX_HISTORY = DEFAULT_MAX_HISTORY


class ClipboardStore(QObject):
    """Керує записами, зберігає зміни й сповіщає інтерфейс про оновлення."""

    entries_changed = Signal()

    def __init__(self, repository: HistoryRepository | None = None, parent=None):
        super().__init__(parent)
        self._repository = repository or HistoryRepository()
        self._entries: list[ClipboardEntry] = self._repository.load()
        self._settings = AppSettings.from_dict(self._repository.load_settings())
        self._trim()

    def add_entry(self, text: str) -> None:
        """Додає текст із буфера, відкидаючи порожні та повторні значення."""
        cleaned = text.strip()
        if not cleaned:
            return
        if self._entries and self._entries[0].text == cleaned:
            return

        entry = ClipboardEntry(text=cleaned)
        self._entries.insert(0, entry)
        self._repository.insert(entry)
        self._trim()
        self.entries_changed.emit()

    def all_entries(self, query: str = "") -> list[ClipboardEntry]:
        """Повертає всі записи, що відповідають пошуковому запиту."""
        return self._filtered(query, pinned_only=False)

    def pinned_entries(self, query: str = "") -> list[ClipboardEntry]:
        """Повертає тільки закріплені записи."""
        return self._filtered(query, pinned_only=True)

    def toggle_pin(self, entry_id: str) -> None:
        """Перемикає стан закріплення запису й зберігає його."""
        for entry in self._entries:
            if entry.id == entry_id:
                entry.pinned = not entry.pinned
                self._repository.update_pin(entry.id, entry.pinned)
                self.entries_changed.emit()
                return

    def remove_entry(self, entry_id: str) -> None:
        """Видаляє один запис за його ідентифікатором."""
        remaining = [entry for entry in self._entries if entry.id != entry_id]
        if len(remaining) != len(self._entries):
            self._entries = remaining
            self._repository.delete(entry_id)
            self.entries_changed.emit()

    def get_text(self, entry_id: str) -> str:
        """Повертає текст запису для копіювання назад у буфер."""
        for entry in self._entries:
            if entry.id == entry_id:
                return entry.text
        return ""

    def clear(self) -> None:
        """Очищує всю історію в пам'яті й у базі даних."""
        self._entries.clear()
        self._repository.clear()
        self.entries_changed.emit()

    def settings(self) -> AppSettings:
        """Повертає копію поточних налаштувань, включно з гарячими клавішами."""
        return replace(self._settings)

    def save_settings(self, settings: AppSettings) -> None:
        """Зберігає налаштування й одразу застосовує новий ліміт."""
        previous_count = len(self._entries)
        self._settings = settings
        self._repository.save_settings(settings.to_dict())
        self._trim()
        if len(self._entries) != previous_count:
            self.entries_changed.emit()

    def _trim(self) -> None:
        """Лишає ліміт записів, спочатку видаляючи найстаріші незакріплені."""
        excess = len(self._entries) - self._settings.max_history
        if excess <= 0:
            return

        unpinned = [entry for entry in self._entries if not entry.pinned]
        if not unpinned:
            return  # Усі записи закріплені — автоматично не видаляємо.

        oldest = sorted(unpinned, key=lambda entry: entry.created_at)[:excess]
        removed_ids = {entry.id for entry in oldest}
        self._entries = [entry for entry in self._entries if entry.id not in removed_ids]
        self._repository.delete_many(removed_ids)

    def _filtered(self, query: str, pinned_only: bool) -> list[ClipboardEntry]:
        needle = query.strip().casefold()
        result = [
            entry
            for entry in self._entries
            if (not pinned_only or entry.pinned)
            and (not needle or needle in entry.text.casefold())
        ]
        # Закріплені зверху, серед них — найновіші.
        return sorted(result, key=lambda entry: (entry.pinned, entry.created_at), reverse=True)
