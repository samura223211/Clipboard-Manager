"""Кольорова палітра, типографіка й єдина таблиця стилів застосунку.

Уся візуальна частина зібрана тут, щоб змінити вигляд можна було в одному місці.
"""

from string import Template

from PySide6.QtGui import QFont, QGuiApplication

# Палітра в стилі темних macOS-застосунків.
COLORS = {
    "bg": "#1C1C1E",
    "sidebar": "#242426",
    "card": "#2C2C2E",
    "card_hover": "#353538",
    "border": "#3A3A3C",
    "border_hover": "#4A4A4E",
    "text": "#F5F5F7",
    "text_secondary": "#98989D",
    "accent": "#0A84FF",
    "accent_hover": "#3D9BFF",
    "accent_soft": "rgba(10, 132, 255, 0.16)",
    "hover": "#323235",
    "pin": "#FFD60A",
    "pin_soft": "rgba(255, 214, 10, 0.12)",
    "danger": "#FF453A",
    "danger_soft": "rgba(255, 69, 58, 0.12)",
    "scroll": "#48484A",
}

# Template використовує $name замість фігурних дужок Python —
# так QSS можна писати без подвоєння всіх { }.
_STYLE_TEMPLATE = Template(
    """
    QWidget#app-root, QWidget#content { background: $bg; }

    /* Бічна панель */
    QFrame#sidebar {
        background: $sidebar;
        border-right: 1px solid $border;
    }
    QLabel#app-logo {
        background: $accent;
        color: #FFFFFF;
        border-radius: 11px;
        font-size: 20px;
        font-weight: 700;
        qproperty-alignment: AlignCenter;
    }
    QLabel#app-title { color: $text; font-size: 15px; font-weight: 700; }
    QLabel#app-subtitle { color: $text_secondary; font-size: 11px; }
    QLabel#section-kicker {
        color: $text_secondary;
        font-size: 10px;
        font-weight: 700;
        padding: 0 12px;
    }
    QLabel#version { color: $text_secondary; font-size: 10px; padding: 0 12px; }

    QPushButton#nav-button {
        background: transparent;
        border: none;
        border-radius: 9px;
        padding: 10px 12px;
        color: $text_secondary;
        font-size: 13px;
        text-align: left;
    }
    QPushButton#nav-button:hover { background: $hover; color: $text; }
    QPushButton#nav-button[active="true"] {
        background: $accent_soft;
        color: $accent;
        font-weight: 700;
    }

    /* Заголовок центральної області */
    QLabel#view-title { color: $text; font-size: 26px; font-weight: 700; }
    QLabel#view-subtitle { color: $text_secondary; font-size: 12px; }
    QPushButton#clear-button {
        background: $danger_soft;
        color: $danger;
        border: none;
        border-radius: 9px;
        padding: 9px 14px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton#clear-button:hover { background: rgba(255, 69, 58, 0.20); }

    /* Поле пошуку */
    QFrame#search-box {
        background: $card;
        border: 1px solid $border;
        border-radius: 11px;
        padding: 1px 10px;
    }
    QLabel#search-icon { color: $text_secondary; font-size: 17px; }
    QLineEdit#search-input {
        background: transparent;
        border: none;
        color: $text;
        font-size: 13px;
        padding: 8px 0;
    }
    QLineEdit#search-input::placeholder { color: $text_secondary; }
    QToolButton#search-clear, QToolButton#pin-button,
    QToolButton#copy-button, QToolButton#delete-button {
        background: transparent;
        border: none;
        border-radius: 7px;
        color: $text_secondary;
    }
    QToolButton#search-clear:hover, QToolButton#pin-button:hover {
        background: $hover;
        color: $text;
    }
    QToolButton#copy-button:hover {
        background: $accent_soft;
        color: $accent;
    }
    QToolButton#delete-button:hover {
        background: $danger_soft;
        color: $danger;
    }
    QToolButton#search-clear { font-size: 16px; padding: 1px 5px; }
    QToolButton#copy-button { font-size: 16px; padding: 1px 6px; }
    QToolButton#delete-button { font-size: 14px; padding: 1px 6px; }
    QToolButton#pin-button { font-size: 18px; padding: 1px 7px; }
    QToolButton#pin-button[pinned="true"] { color: $pin; }

    /* Список і картки */
    QScrollArea#entry-scroll { background: transparent; border: none; }
    QScrollArea#entry-scroll QWidget#scroll-content { background: transparent; }
    QFrame#entry-card {
        background: $card;
        border: 1px solid $border;
        border-radius: 14px;
    }
    QFrame#entry-card[hovered="true"] {
        background: $card_hover;
        border-color: $border_hover;
    }
    QLabel#entry-time { color: $text_secondary; font-size: 11px; }
    QLabel#entry-badge {
        color: $pin;
        background: $pin_soft;
        border-radius: 6px;
        padding: 2px 7px;
        font-size: 10px;
    }
    QLabel#entry-text { color: $text; font-size: 13px; }

    /* Порожній стан */
    QLabel#empty-icon { color: $border_hover; font-size: 40px; }
    QLabel#empty-title { color: $text; font-size: 16px; font-weight: 600; }
    QLabel#empty-hint { color: $text_secondary; font-size: 12px; }

    /* Налаштування */
    QFrame#settings-card {
        background: $card;
        border: 1px solid $border;
        border-radius: 14px;
    }
    QLabel#settings-note { color: $text_secondary; font-size: 11px; }
    QLabel#settings-section-title {
        color: $text;
        font-size: 13px;
        font-weight: 700;
    }
    QFrame#settings-divider { color: $border; background: $border; max-height: 1px; }
    QKeySequenceEdit {
        background: $bg;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 5px 9px;
        min-width: 180px;
        color: $text;
        font-size: 12px;
        selection-background-color: $accent_soft;
    }
    QPushButton#save-settings {
        background: $accent;
        color: #FFFFFF;
        border: none;
        border-radius: 9px;
        padding: 9px 16px;
        font-size: 12px;
        font-weight: 600;
    }
    QPushButton#save-settings:hover { background: $accent_hover; }
    QLabel#settings-status { font-size: 11px; }
    QLabel#settings-status[ok="true"] { color: $accent; }
    QLabel#settings-status[ok="false"] { color: $danger; }
    QCheckBox, QSpinBox, QComboBox { color: $text; font-size: 13px; }
    QSpinBox, QComboBox {
        background: $bg;
        border: 1px solid $border;
        border-radius: 8px;
        padding: 5px 9px;
    }
    QSpinBox::up-button, QSpinBox::down-button { width: 14px; }

    /* Смуга прокрутки */
    QScrollBar:vertical {
        background: transparent;
        width: 9px;
        margin: 6px 2px 6px 0;
    }
    QScrollBar::handle:vertical {
        background: $scroll;
        border-radius: 4px;
        min-height: 32px;
    }
    QScrollBar::handle:vertical:hover { background: $border_hover; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
    """
)


def build_stylesheet() -> str:
    """Повертає готовий QSS з підставленими кольорами."""
    return _STYLE_TEMPLATE.substitute(COLORS)


def create_application_font() -> QFont:
    """Повертає системний UI-шрифт (SF на macOS, Segoe UI на Windows)."""
    font = QFont(QGuiApplication.font())
    font.setPointSize(13)
    return font
