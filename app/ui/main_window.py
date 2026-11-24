"""Головне вікно: поєднує бічну панель, список записів і налаштування."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QWidget,
)

from app import autostart
from app.clipboard_monitor import ClipboardMonitor
from app.hotkeys import HotkeyManager
from app.i18n import i18n, tr
from app.models.app_settings import AppSettings
from app.models.clipboard_store import ClipboardStore
from app.tray import TrayIcon
from app.ui.entries_view import EntriesView
from app.ui.settings_view import SettingsView
from app.ui.sidebar import Sidebar


class MainWindow(QMainWindow):
    """Компонує інтерфейс і реагує на дії користувача."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("app.title"))
        self.resize(1120, 720)
        self.setMinimumSize(760, 520)

        self._store = ClipboardStore()
        self._settings = self._store.settings()
        i18n.set_language(self._settings.language)
        self._monitor = ClipboardMonitor(self._store, self)
        self._monitor.start()
        self._section = "all"
        self._warning: QMessageBox | None = None
        self._quitting = False

        self._sidebar = Sidebar(self)
        self._entries_view = EntriesView(self)
        self._settings_view = SettingsView(self._settings, self)

        self._stack = QStackedWidget(self)
        self._stack.addWidget(self._entries_view)
        self._stack.addWidget(self._settings_view)

        content = QWidget(self)
        content.setObjectName("content")
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._stack)

        root = QWidget(self)
        root.setObjectName("app-root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._sidebar, 0)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)

        self._sidebar.section_selected.connect(self._on_section_selected)
        self._entries_view.search_changed.connect(self._refresh_entries)
        self._entries_view.clear_requested.connect(self._on_clear_requested)
        self._entries_view.copy_requested.connect(self._on_copy_requested)
        self._entries_view.pin_toggled.connect(self._store.toggle_pin)
        self._entries_view.delete_requested.connect(self._store.remove_entry)
        self._settings_view.settings_saved.connect(self._on_settings_saved)
        self._settings_view.language_changed.connect(i18n.set_language)
        self._store.entries_changed.connect(self._refresh_entries)
        i18n.language_changed.connect(self.retranslate)

        # Очищення пошуку — локальна комбінація, що діє у межах застосунку.
        self._clear_shortcut = QShortcut(QKeySequence(self._settings.clear_hotkey), self)
        self._clear_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._clear_shortcut.activated.connect(self._entries_view.clear_search)

        # Показ/приховування — глобальна комбінація, реєструється в системі.
        self._hotkeys = HotkeyManager(self)

        # Одна іконка трея на весь час роботи застосунку.
        self._tray = TrayIcon(self)
        self._tray.open_requested.connect(self.show_window)
        self._tray.settings_requested.connect(self.show_settings)
        self._tray.quit_requested.connect(self.quit_app)

        self._refresh_entries()
        self._register_toggle()

    def _register_toggle(self) -> None:
        """(Пере)реєструє глобальну комбінацію показу/приховування вікна."""
        self._hotkeys.unregister_all()
        if self._hotkeys.register(self._settings.toggle_hotkey, self._toggle_visibility):
            return
        self._warn("warning.hotkey", combo=self._settings.toggle_hotkey)

    def _toggle_visibility(self) -> None:
        """Глобальна комбінація: згорнути вікно або показати його знову."""
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    def show_window(self) -> None:
        """Показує вже існуюче вікно (використовує трей та новий процес)."""
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def show_settings(self) -> None:
        """Відкриває вікно одразу на розділі налаштувань."""
        self._sidebar.select_section("settings")
        self.show_window()

    def _warn(self, key: str, **kwargs: object) -> None:
        """Неблокуюче повідомлення про помилку реєстрації гарячих клавіш."""
        box = QMessageBox(
            QMessageBox.Icon.Warning,
            tr("app.title"),
            tr(key, **kwargs),
            QMessageBox.StandardButton.Ok,
            self,
        )
        box.setModal(False)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._warning = box  # тримаємо посилання, поки вікно не закриється
        self._warning_key = key
        self._warning_kwargs = kwargs
        box.destroyed.connect(self._on_warning_destroyed)
        box.show()

    def _on_warning_destroyed(self) -> None:
        self._warning = None

    def _on_section_selected(self, section: str) -> None:
        self._section = section
        if section == "settings":
            self._stack.setCurrentWidget(self._settings_view)
        else:
            self._stack.setCurrentWidget(self._entries_view)
            self._refresh_entries()

    def _refresh_entries(self) -> None:
        query = self._entries_view.search_text()
        if self._section == "pinned":
            self._entries_view.set_title_key("entries.pinned")
            self._entries_view.set_show_clear(False)
            entries = self._store.pinned_entries(query)
        else:
            self._entries_view.set_title_key("entries.all")
            self._entries_view.set_show_clear(True)
            entries = self._store.all_entries(query)
        self._entries_view.set_entries(entries)

    def _on_clear_requested(self) -> None:
        answer = QMessageBox.question(
            self,
            tr("dialog.clear.title"),
            tr("dialog.clear.text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._store.clear()

    def _on_copy_requested(self, entry_id: str) -> None:
        self._monitor.copy_to_clipboard(self._store.get_text(entry_id))

    def _on_settings_saved(self, settings: AppSettings) -> None:
        autostart_ok = autostart.set_enabled(settings.autostart)
        self._store.save_settings(settings)
        self._settings = settings
        self._clear_shortcut.setKey(QKeySequence(settings.clear_hotkey))

        self._hotkeys.unregister_all()
        hotkeys_ok = self._hotkeys.register(settings.toggle_hotkey, self._toggle_visibility)

        if not hotkeys_ok:
            self._settings_view.set_status("settings.saved.hotkey_failed", ok=False)
            self._warn("warning.hotkey.saved", combo=settings.toggle_hotkey)
        elif not autostart_ok:
            self._settings_view.set_status("settings.saved.autostart_failed", ok=False)
        else:
            self._settings_view.set_status("settings.saved")

    def retranslate(self) -> None:
        """Застосовує мову до всього вікна без перезапуску застосунку."""
        self.setWindowTitle(tr("app.title"))
        if self._warning is not None:
            self._warning.setText(tr(self._warning_key, **self._warning_kwargs))
        self._refresh_entries()

    def _cleanup(self) -> None:
        """Зупиняємо спостереження й знімаємо глобальні комбінації один раз."""
        if self._quitting:
            return
        self._quitting = True
        self._hotkeys.unregister_all()
        self._monitor.stop()
        self._tray.hide()
        if self._warning is not None:
            self._warning.close()

    def quit_app(self) -> None:
        """Повний вихід: зупиняємо монітор і завершуємо процес."""
        if self._quitting:
            return
        self._cleanup()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def closeEvent(self, event) -> None:
        """Закриття вікна ховає програму в трей, але не завершує її."""
        if self._quitting:
            super().closeEvent(event)
            return
        if self._tray.is_available:
            event.ignore()
            if self._warning is not None:
                self._warning.close()
            self.hide()
            return
        self._cleanup()
        super().closeEvent(event)
        app = QApplication.instance()
        if app is not None:
            app.quit()
