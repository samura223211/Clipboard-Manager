"""Іконка в системному трею macOS / Windows.

Один екземпляр QSystemTrayIcon створюється на весь час роботи застосунку.
Платформні відмінності обмежені малюванням іконки: у macOS меню-бар
використовує монохромну(template-)іконку, у Windows — кольорову.
"""

import platform

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from app.i18n import i18n, tr
from app.theme import COLORS


def _make_icon() -> QIcon:
    """Створює іконку кодом — окремий файл-ресурс не потрібен."""
    size = 128
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor("transparent"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    if platform.system() == "Darwin":
        # Template-іконка: macOS сам фарбує її під вигляд меню-бару.
        painter.setPen(QPen(QColor("#FFFFFF")))
        font = QFont()
        font.setPixelSize(96)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    else:
        painter.setBrush(QColor(COLORS["accent"]))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawRoundedRect(8, 8, size - 16, size - 16, 28, 28)
        painter.setPen(QPen(QColor("#FFFFFF")))
        font = QFont()
        font.setPixelSize(84)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    painter.end()

    icon = QIcon(pixmap)
    if platform.system() == "Darwin":
        icon.setIsMask(True)
    return icon


class TrayIcon(QObject):
    """Тримає іконку й контекстне меню; не створює нових процесів."""

    open_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._icon = QSystemTrayIcon(_make_icon(), self)
        self._menu = QMenu()

        self._open_action = self._menu.addAction(tr("tray.open"))
        self._settings_action = self._menu.addAction(tr("nav.settings"))
        self._menu.addSeparator()
        self._quit_action = self._menu.addAction(tr("tray.quit"))

        self._open_action.triggered.connect(self.open_requested)
        self._settings_action.triggered.connect(self.settings_requested)
        self._quit_action.triggered.connect(self.quit_requested)

        # Саме це робить меню доступним по правій кнопці (Windows) і кліку (macOS).
        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._on_activated)

        self.retranslate()
        self._icon.show()
        i18n.language_changed.connect(self.retranslate)

    @property
    def is_available(self) -> bool:
        """Чи є трей у системі — від нього залежить поведінка закриття вікна."""
        return QSystemTrayIcon.isSystemTrayAvailable()

    def retranslate(self) -> None:
        self._icon.setToolTip(tr("app.title"))
        self._open_action.setText(tr("tray.open"))
        self._settings_action.setText(tr("nav.settings"))
        self._quit_action.setText(tr("tray.quit"))

    def hide(self) -> None:
        self._icon.hide()

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.open_requested.emit()
