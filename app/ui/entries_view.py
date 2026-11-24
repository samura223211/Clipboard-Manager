"""Центральна область: заголовок, пошук, список карток і очищення історії."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.i18n import i18n, tr
from app.models.clipboard_entry import ClipboardEntry
from app.ui.clipboard_card import ClipboardCard
from app.ui.search_field import SearchField


class EntriesView(QWidget):
    """Список записів у QScrollArea: картки автоматично тягнуться по ширині."""

    search_changed = Signal(str)
    clear_requested = Signal()
    copy_requested = Signal(str)
    pin_toggled = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("entries-view")
        self._title_key = "entries.all"

        root = QVBoxLayout(self)
        root.setContentsMargins(32, 26, 24, 14)
        root.setSpacing(16)

        header = QFrame(self)
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        titles = QVBoxLayout()
        titles.setSpacing(4)
        self._title = QLabel(header)
        self._title.setObjectName("view-title")
        self._subtitle = QLabel(header)
        self._subtitle.setObjectName("view-subtitle")
        titles.addWidget(self._title)
        titles.addWidget(self._subtitle)

        self._clear_button = QPushButton(header)
        self._clear_button.setObjectName("clear-button")
        self._clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_button.clicked.connect(self.clear_requested)

        header_layout.addLayout(titles, 1)
        header_layout.addWidget(self._clear_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addWidget(header)

        self._search = SearchField(self)
        self._search.text_changed.connect(self.search_changed)
        root.addWidget(self._search)

        scroll = QScrollArea(self)
        scroll.setObjectName("entry-scroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget(scroll)
        content.setObjectName("scroll-content")
        self._cards_layout = QVBoxLayout(content)
        self._cards_layout.setContentsMargins(2, 2, 6, 2)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        i18n.language_changed.connect(self.retranslate)
        self.retranslate()

    def retranslate(self) -> None:
        self._title.setText(tr(self._title_key))
        self._subtitle.setText(tr("entries.subtitle"))
        self._clear_button.setText(tr("entries.clear"))
        if self.search_text().strip():
            title_key = "entries.empty.title"
            hint_key = "entries.empty.hint"
        else:
            title_key = "entries.empty.history"
            hint_key = "entries.empty.history_hint"
        for label in self.findChildren(QLabel, "empty-title"):
            label.setText(tr(title_key))
        for label in self.findChildren(QLabel, "empty-hint"):
            label.setText(tr(hint_key))

    def set_title_key(self, key: str) -> None:
        self._title_key = key
        self._title.setText(tr(key))

    def set_show_clear(self, visible: bool) -> None:
        self._clear_button.setVisible(visible)

    def search_text(self) -> str:
        return self._search.text()

    def clear_search(self) -> None:
        """Очищує пошук; сигнал text_changed сам оновить список."""
        self._search.clear()

    def set_entries(self, entries: list[ClipboardEntry]) -> None:
        """Перебудовує список карток; викликається після кожної зміни даних."""
        while self._cards_layout.count():
            item = self._cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        if entries:
            for entry in entries:
                card = ClipboardCard(entry, self)
                card.copy_requested.connect(self.copy_requested)
                card.pin_toggled.connect(self.pin_toggled)
                card.delete_requested.connect(self.delete_requested)
                self._cards_layout.addWidget(card)
        else:
            self._cards_layout.addWidget(self._empty_state())

        self._cards_layout.addStretch(1)

    def _empty_state(self) -> QWidget:
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(0, 60, 0, 0)
        layout.setSpacing(6)

        searching = bool(self.search_text().strip())
        icon = QLabel("◇" if searching else "◌", widget)
        icon.setObjectName("empty-icon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(
            tr("entries.empty.title" if searching else "entries.empty.history"),
            widget,
        )
        title.setObjectName("empty-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(
            tr("entries.empty.hint" if searching else "entries.empty.history_hint"),
            widget,
        )
        hint.setObjectName("empty-hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(hint)
        return widget
