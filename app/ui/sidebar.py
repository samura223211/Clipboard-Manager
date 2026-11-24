"""Бічна панель із трьома розділами застосунку."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app import __version__
from app.i18n import i18n, tr

SECTIONS = (
    ("all", "▤", "nav.all"),
    ("pinned", "★", "nav.pinned"),
    ("settings", "⚙", "nav.settings"),
)


class Sidebar(QFrame):
    """Панель навігації. Вибраний розділ підсвічується через QSS-властивість."""

    section_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(236)
        self._buttons: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 22, 16, 18)
        layout.setSpacing(4)

        header = QFrame(self)
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(11)

        logo = QLabel("C", header)
        logo.setObjectName("app-logo")
        logo.setFixedSize(40, 40)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        self._title = QLabel()
        self._title.setObjectName("app-title")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("app-subtitle")
        titles.addWidget(self._title)
        titles.addWidget(self._subtitle)

        header_layout.addWidget(logo)
        header_layout.addLayout(titles)
        layout.addWidget(header)
        layout.addSpacing(28)

        self._kicker = QLabel()
        self._kicker.setObjectName("section-kicker")
        layout.addWidget(self._kicker)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for key, glyph, caption_key in SECTIONS:
            button = QPushButton(f"  {glyph}    {tr(caption_key)}")
            button.setObjectName("nav-button")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, k=key: self._on_clicked(k))
            group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)

        layout.addStretch(1)

        self._version = QLabel()
        self._version.setObjectName("version")
        layout.addWidget(self._version)

        i18n.language_changed.connect(self.retranslate)
        self.retranslate()
        self._set_active("all")

    def retranslate(self) -> None:
        self._title.setText(tr("app.title"))
        self._subtitle.setText(tr("app.subtitle"))
        self._kicker.setText(tr("nav.section"))
        self._version.setText(tr("nav.version", version=__version__))
        for key, glyph, caption_key in SECTIONS:
            button = self._buttons[key]
            button.setText(f"  {glyph}    {tr(caption_key)}")

    def select_section(self, key: str) -> None:
        """Програмно вибрати розділ (використовує, зокрема, меню трея)."""
        self._set_active(key)
        self.section_selected.emit(key)

    def _on_clicked(self, key: str) -> None:
        self.select_section(key)

    def _set_active(self, key: str) -> None:
        for name, button in self._buttons.items():
            active = name == key
            button.setProperty("active", active)
            button.setChecked(active)
            button.style().polish(button)
