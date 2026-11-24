"""Екран налаштувань: ліміт, автозапуск і гарячі клавіші."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.hotkeys import parse_hotkey
from app.i18n import i18n, tr
from app.models.app_settings import MAX_HISTORY_LIMIT, MIN_HISTORY, AppSettings


def _portable(sequence: QKeySequence) -> str:
    """Стабільне рядкове подання для збереження й порівняння комбінацій."""
    return sequence.toString(QKeySequence.SequenceFormat.PortableText)


class HotkeySequenceEdit(QKeySequenceEdit):
    """Поле комбінації, яке не дає Backspace/Delete стирати значення."""

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            event.ignore()
            return
        super().keyPressEvent(event)


class SettingsView(QWidget):
    """Формує подію `settings_saved` із новими значеннями."""

    settings_saved = Signal(AppSettings)
    language_changed = Signal(str)

    def __init__(self, settings: AppSettings, parent=None):
        super().__init__(parent)
        self.setObjectName("settings-view")

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 26, 24, 14)
        root.setSpacing(18)

        self._title = QLabel(self)
        self._title.setObjectName("view-title")
        self._subtitle = QLabel(self)
        self._subtitle.setObjectName("view-subtitle")
        root.addWidget(self._title)
        root.addWidget(self._subtitle)

        card = QFrame(self)
        card.setObjectName("settings-card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(16)

        limit_row = QHBoxLayout()
        self._limit_label = QLabel(card)
        self._max_spin = QSpinBox(card)
        self._max_spin.setRange(MIN_HISTORY, MAX_HISTORY_LIMIT)
        self._max_spin.setValue(settings.max_history)
        limit_row.addWidget(self._limit_label, 1)
        limit_row.addWidget(self._max_spin)

        self._autostart = QCheckBox(card)
        self._autostart.setChecked(settings.autostart)

        self._note = QLabel(card)
        self._note.setObjectName("settings-note")

        language_row = QHBoxLayout()
        self._language_label = QLabel(card)
        self._language_combo = QComboBox(card)
        self._language_combo.setObjectName("language-combo")
        for code, name in i18n.languages.items():
            self._language_combo.addItem(name, code)
        index = self._language_combo.findData(settings.language)
        if index >= 0:
            self._language_combo.setCurrentIndex(index)
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        language_row.addWidget(self._language_label, 1)
        language_row.addWidget(self._language_combo)

        divider = QFrame(card)
        divider.setObjectName("settings-divider")
        divider.setFrameShape(QFrame.Shape.HLine)

        self._hotkeys_title = QLabel(card)
        self._hotkeys_title.setObjectName("settings-section-title")

        toggle_row = QHBoxLayout()
        self._toggle_label = QLabel(card)
        self._toggle_edit = HotkeySequenceEdit(QKeySequence(settings.toggle_hotkey), card)
        self._toggle_edit.setObjectName("hotkey-toggle")
        toggle_row.addWidget(self._toggle_label, 1)
        toggle_row.addWidget(self._toggle_edit)

        clear_row = QHBoxLayout()
        self._clear_label = QLabel(card)
        self._clear_edit = HotkeySequenceEdit(QKeySequence(settings.clear_hotkey), card)
        self._clear_edit.setObjectName("hotkey-clear")
        clear_row.addWidget(self._clear_label, 1)
        clear_row.addWidget(self._clear_edit)

        self._hotkeys_note = QLabel(card)
        self._hotkeys_note.setObjectName("settings-note")

        self._save_button = QPushButton(card)
        self._save_button.setObjectName("save-settings")
        self._save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_button.clicked.connect(self._on_save)

        self._status = QLabel("", card)
        self._status.setObjectName("settings-status")
        self._status_key = ""

        card_layout.addLayout(limit_row)
        card_layout.addWidget(self._autostart)
        card_layout.addWidget(self._note)
        card_layout.addLayout(language_row)
        card_layout.addWidget(divider)
        card_layout.addWidget(self._hotkeys_title)
        card_layout.addLayout(toggle_row)
        card_layout.addLayout(clear_row)
        card_layout.addWidget(self._hotkeys_note)
        card_layout.addWidget(self._save_button)
        card_layout.addWidget(self._status)

        root.addWidget(card)
        root.addStretch(1)

        i18n.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self) -> None:
        self._title.setText(tr("settings.title"))
        self._subtitle.setText(tr("settings.subtitle"))
        self._limit_label.setText(tr("settings.limit"))
        self._max_spin.setSuffix(tr("settings.limit.suffix"))
        self._autostart.setText(tr("settings.autostart"))
        self._note.setText(tr("settings.autostart.note"))
        self._language_label.setText(tr("settings.language"))
        self._hotkeys_title.setText(tr("settings.hotkeys"))
        self._toggle_label.setText(tr("settings.hotkeys.toggle"))
        self._clear_label.setText(tr("settings.hotkeys.clear"))
        self._toggle_edit.setToolTip(tr("settings.hotkeys.global_tip"))
        self._hotkeys_note.setText(tr("settings.hotkeys.note"))
        self._save_button.setText(tr("settings.save"))
        if self._status_key:
            self._status.setText(tr(self._status_key))

    def _on_language_changed(self) -> None:
        code = self._language_combo.currentData()
        if code:
            self.language_changed.emit(code)

    def _on_save(self) -> None:
        toggle = _portable(self._toggle_edit.keySequence())
        clear = _portable(self._clear_edit.keySequence())

        if not toggle or not clear:
            self.set_status("settings.error.both", ok=False)
            return
        if any(not (parsed and parsed.modifiers) for parsed in map(parse_hotkey, (toggle, clear))):
            self.set_status("settings.error.modifier", ok=False)
            return
        if toggle == clear:
            self.set_status("settings.error.conflict", ok=False)
            return

        self.settings_saved.emit(
            AppSettings(
                max_history=self._max_spin.value(),
                autostart=self._autostart.isChecked(),
                toggle_hotkey=toggle,
                clear_hotkey=clear,
                language=self._language_combo.currentData(),
            )
        )

    def set_status(self, key: str, ok: bool = True) -> None:
        """Показує перекладений результат збереження (зелений/червоний текст)."""
        self._status_key = key
        self._status.setText(tr(key))
        self._status.setProperty("ok", ok)
        self._status.style().polish(self._status)
