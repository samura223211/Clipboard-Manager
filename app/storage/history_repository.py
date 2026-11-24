"""SQLite-репозиторій історії буфера обміну.

Файл бази лежить у системній папці даних користувача (визначає Qt),
а не в папці проєкту. Усі помилки SQLite обробляються: застосунок
продовжує працювати в пам'яті, якщо база тимчасово недоступна.
"""

import logging
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from app.models.clipboard_entry import ClipboardEntry

logger = logging.getLogger(__name__)

DB_FILE = "history.sqlite3"


class HistoryRepository:
    """Зчитує й зберігає записи в SQLite без участі GUI."""

    def __init__(self, db_path: Path | None = None):
        self._db_path = db_path or self._default_path()
        self._available = True
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._create_schema()
        except (OSError, sqlite3.Error) as exc:
            logger.warning("SQLite недоступний, працюємо в пам'яті: %s", exc)
            self._available = False

    @staticmethod
    def _default_path() -> Path:
        """macOS: ~/Library/Application Support/..., Windows: %APPDATA%/..."""
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if not base:
            base = str(Path.home() / ".clipboard_manager")
        return Path(base) / DB_FILE

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _create_schema(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    pinned INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_entries_created_at "
                "ON entries(created_at)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def _execute(self, sql: str, params: tuple = ()) -> None:
        if not self._available:
            return
        try:
            with closing(self._connect()) as conn, conn:
                conn.execute(sql, params)
        except (OSError, sqlite3.Error) as exc:
            logger.warning("Помилка запису до SQLite: %s", exc)

    def load(self) -> list[ClipboardEntry]:
        """Повертає збережені записи (найновіші першими)."""
        if not self._available:
            return []
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute(
                    "SELECT id, text, created_at, pinned FROM entries "
                    "ORDER BY created_at DESC, rowid DESC"
                ).fetchall()
        except (OSError, sqlite3.Error) as exc:
            logger.warning("Помилка читання з SQLite: %s", exc)
            return []

        entries: list[ClipboardEntry] = []
        for entry_id, text, created_at, pinned in rows:
            try:
                entries.append(
                    ClipboardEntry(
                        id=entry_id,
                        text=text,
                        created_at=datetime.fromisoformat(created_at),
                        pinned=bool(pinned),
                    )
                )
            except (TypeError, ValueError) as exc:
                logger.warning("Пропущено пошкоджений запис %s: %s", entry_id, exc)
        return entries

    def insert(self, entry: ClipboardEntry) -> None:
        self._execute(
            "INSERT OR REPLACE INTO entries(id, text, created_at, pinned) "
            "VALUES (?, ?, ?, ?)",
            (entry.id, entry.text, entry.created_at.isoformat(), int(entry.pinned)),
        )

    def update_pin(self, entry_id: str, pinned: bool) -> None:
        self._execute(
            "UPDATE entries SET pinned = ? WHERE id = ?", (int(pinned), entry_id)
        )

    def delete(self, entry_id: str) -> None:
        self._execute("DELETE FROM entries WHERE id = ?", (entry_id,))

    def delete_many(self, entry_ids: set[str]) -> None:
        if not entry_ids:
            return
        placeholders = ", ".join("?" for _ in entry_ids)
        self._execute(
            f"DELETE FROM entries WHERE id IN ({placeholders})", tuple(entry_ids)
        )

    def clear(self) -> None:
        self._execute("DELETE FROM entries")

    def load_settings(self) -> dict[str, str]:
        """Повертає збережені налаштування або порожній словник."""
        if not self._available:
            return {}
        try:
            with closing(self._connect()) as conn:
                rows = conn.execute("SELECT key, value FROM settings").fetchall()
        except (OSError, sqlite3.Error) as exc:
            logger.warning("Помилка читання налаштувань: %s", exc)
            return {}
        return {key: value for key, value in rows}

    def save_settings(self, values: dict[str, str]) -> None:
        """Зберігає налаштування як пари ключ-значення."""
        for key, value in values.items():
            self._execute(
                "INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)",
                (str(key), str(value)),
            )
