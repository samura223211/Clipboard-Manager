"""Спостереження за системним буфером обміну через QClipboard.

Однаковий код для macOS і Windows: Qt сам підписується на системні
повідомлення про зміну буфера.
"""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QClipboard, QGuiApplication


class ClipboardMonitor(QObject):
    """Перетворює зміни буфера на нові записи у сховищі.

    Поточний текст у `start()` запам'ятовуємо як початковий стан, щоб не
    додавати те, що вже було скопійовано до запуску програми.
    """

    def __init__(self, store, parent=None):
        super().__init__(parent)
        self._store = store
        self._clipboard = QGuiApplication.clipboard()
        self._last_text = ""
        self._running = False

        # Невелика затримка (0 мс) дає системі час ініціалізувати вміст
        # буфера й об'єднує кілька повідомлень в одне читання.
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._read_clipboard)

    def start(self) -> None:
        """Підключаємося до сигналів буфера після створення QApplication."""
        if self._running:
            return
        self._last_text = self._current_text()
        self._clipboard.dataChanged.connect(self._schedule_read)
        self._running = True

    def stop(self) -> None:
        """Відключаємося (викликається при закритті вікна)."""
        if not self._running:
            return
        self._clipboard.dataChanged.disconnect(self._schedule_read)
        self._timer.stop()
        self._running = False

    def copy_to_clipboard(self, text: str) -> None:
        """Копіює текст з історії, не додаючи новий запис у сховище."""
        cleaned = text.strip()
        if not cleaned:
            return

        # Оновлюємо еталон заздалегідь: dataChanged прийде з тим самим
        # текстом і _read_clipboard проігнорує його.
        self._last_text = cleaned
        self._timer.stop()
        self._clipboard.setText(cleaned, QClipboard.Mode.Clipboard)

    def _schedule_read(self) -> None:
        self._timer.start()

    def _current_text(self) -> str:
        return self._clipboard.text(QClipboard.Mode.Clipboard).strip()

    def _read_clipboard(self) -> None:
        text = self._current_text()
        if not text or text == self._last_text:
            return
        self._last_text = text
        self._store.add_entry(text)
