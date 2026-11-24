"""Картка запису: текст, час, копіювання, закріплення й видалення."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

from app.i18n import i18n, tr
from app.models.clipboard_entry import ClipboardEntry, format_timestamp


class ClipboardCard(QFrame):
    """Картка з плавним hover-ефектом через QSS-властивість `hovered`."""

    copy_requested = Signal(str)
    pin_toggled = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, entry: ClipboardEntry, parent=None):
        super().__init__(parent)
        self._entry = entry
        self.setObjectName("entry-card")
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._build_ui()
        self._render()
        i18n.language_changed.connect(self.retranslate)
        self.retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 13)
        layout.setSpacing(9)

        top = QHBoxLayout()
        top.setSpacing(8)

        self._time_label = QLabel(self)
        self._time_label.setObjectName("entry-time")

        self._badge = QLabel(self)
        self._badge.setObjectName("entry-badge")

        self._copy_button = QToolButton(self)
        self._copy_button.setObjectName("copy-button")
        self._copy_button.setText("⧉")
        self._copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_button.clicked.connect(self._on_copy_clicked)

        self._pin_button = QToolButton(self)
        self._pin_button.setObjectName("pin-button")
        self._pin_button.setCheckable(True)
        self._pin_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pin_button.clicked.connect(self._on_pin_clicked)

        self._delete_button = QToolButton(self)
        self._delete_button.setObjectName("delete-button")
        self._delete_button.setText("✕")
        self._delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._delete_button.clicked.connect(self._on_delete_clicked)

        top.addWidget(self._time_label)
        top.addWidget(self._badge)
        top.addStretch(1)
        top.addWidget(self._copy_button)
        top.addWidget(self._pin_button)
        top.addWidget(self._delete_button)

        self._text_label = QLabel(self)
        self._text_label.setObjectName("entry-text")
        self._text_label.setWordWrap(True)
        self._text_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        layout.addLayout(top)
        layout.addWidget(self._text_label)

    def retranslate(self) -> None:
        self._badge.setText(tr("card.pinned"))
        self._copy_button.setToolTip(tr("card.copy"))
        self._delete_button.setToolTip(tr("card.delete"))
        self._render()

    def _render(self) -> None:
        self._time_label.setText(format_timestamp(self._entry.created_at))
        self._badge.setVisible(self._entry.pinned)
        self._text_label.setText(self._entry.text)

        pinned = self._entry.pinned
        self._pin_button.setChecked(pinned)
        self._pin_button.setText("★" if pinned else "☆")
        self._pin_button.setToolTip(
            tr("card.unpin") if pinned else tr("card.pin")
        )
        self._pin_button.setProperty("pinned", pinned)
        self._pin_button.style().polish(self._pin_button)

    def _on_copy_clicked(self) -> None:
        self.copy_requested.emit(self._entry.id)

    def _on_pin_clicked(self) -> None:
        self.pin_toggled.emit(self._entry.id)

    def _on_delete_clicked(self) -> None:
        self.delete_requested.emit(self._entry.id)

    def enterEvent(self, event):
        self.setProperty("hovered", True)
        self.style().polish(self)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setProperty("hovered", False)
        self.style().polish(self)
        self.update()
        super().leaveEvent(event)
