"""Автозапуск застосунку: macOS LaunchAgent / Windows Registry Run.

Платформні відмінності ізольовані в цьому модулі; решта коду однакова.
"""

import logging
import platform
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "ClipboardManager"
LABEL = "com.clipboardmanager"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _agent_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _launch_command() -> list[str]:
    """Команда запуску: у збірці — бінарник, у розробці — python + run.py."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    script = Path(__file__).resolve().parents[2] / "run.py"
    return [sys.executable, str(script)]


def is_enabled() -> bool:
    """Повертає True, якщо автозапуск уже налаштований у системі."""
    system = platform.system()
    try:
        if system == "Darwin":
            return _agent_path().exists()
        if system == "Windows":
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
    except (OSError, ImportError, FileNotFoundError) as exc:
        logger.warning("Не вдалося перевірити автозапуск: %s", exc)
    return False


def set_enabled(enabled: bool) -> bool:
    """Вмикає/вимикає автозапуск. Повертає True у разі успіху."""
    system = platform.system()
    try:
        if system == "Darwin":
            agent = _agent_path()
            if enabled:
                import plistlib

                agent.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "Label": LABEL,
                    "ProgramArguments": _launch_command(),
                    "RunAtLoad": True,
                }
                with agent.open("wb") as file:
                    plistlib.dump(payload, file)
            else:
                agent.unlink(missing_ok=True)
            return True

        if system == "Windows":
            import winreg

            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                if enabled:
                    command = " ".join(f'"{arg}"' for arg in _launch_command())
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, APP_NAME)
                    except FileNotFoundError:
                        pass
            return True
    except (OSError, ImportError, ValueError) as exc:
        logger.warning("Не вдалося змінити автозапуск: %s", exc)
    return False
