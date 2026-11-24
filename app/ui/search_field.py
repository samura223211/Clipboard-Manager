"""Поле пошуку з іконкою та кнопкою очищення вводу."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QToolButton

from app.i18n import i18n, tr


class SearchField(QFrame):
    """Композитний віджет: рамка + іконка + QLineEdit + кнопка ×."""

    text_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("search-box")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 10, 0)
        layout.setSpacing(8)

        icon = QLabel("⌕", self)
        icon.setObjectName("search-icon")

        self._edit = QLineEdit(self)
        self._edit.setObjectName("search-input")
        self._edit.setFrame(False)

        self._clear = QToolButton(self)
        self._clear.setObjectName("search-clear")
        self._clear.setText("×")
        self._clear.setVisible(False)
        self._clear.clicked.connect(self.clear)

        layout.addWidget(icon)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._clear)

        self._edit.textChanged.connect(self._on_text_changed)
        i18n.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self) -> None:
        self._edit.setPlaceholderText(tr("search.placeholder"))
        self._clear.setToolTip(tr("search.clear"))

    def text(self) -> str:
        return self._edit.text()

    def clear(self) -> None:
        self._edit.clear()

    def _on_text_changed(self, text: str) -> None:
        self._clear.setVisible(bool(text))
        self.text_changed.emit(text)
