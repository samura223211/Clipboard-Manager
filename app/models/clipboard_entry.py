"""Одна запис історії буфера обміну."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from app.i18n import tr


@dataclass
class ClipboardEntry:
    """Тестова модель запису. Реальне зчитування буфера поки не реалізоване."""

    text: str
    created_at: datetime = field(default_factory=datetime.now)
    pinned: bool = False
    id: str = field(default_factory=lambda: uuid4().hex[:8])


def format_timestamp(value: datetime) -> str:
    """Форматує час без залежності від системної локалі."""
    clock = value.strftime("%H:%M")
    if value.date() == datetime.now().date():
        return tr("card.today", clock=clock)
    return f"{value:%d.%m.%Y}, {clock}"
