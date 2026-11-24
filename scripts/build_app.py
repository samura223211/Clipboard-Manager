"""Common PyInstaller build driver for macOS and Windows.

The application code is shared. Only the output format and the icon container
differ: macOS gets a .app bundle with an .icns icon, Windows gets a .exe with
an .ico icon. Run this script on the target OS; PyInstaller cannot cross-build
Windows executables from macOS with a normal installation.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QBuffer, QIODevice, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QPainter,
    QPen,
)

from app.theme import COLORS  # noqa: E402

# QFont needs a QGuiApplication; offscreen keeps the build usable on CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_APP = QGuiApplication.instance() or QGuiApplication([])

APP_NAME = "Clipboard Manager"
BUNDLE_ID = "com.clipboardmanager"  # same label as the macOS LaunchAgent
ICON_BASE_SIZE = 1024
MAC_ICONSET_ENTRIES = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)
WIN_ICON_SIZES = (16, 32, 48, 64, 128, 256)


def _draw_icon() -> QImage:
    """Draw the application icon from the same palette as the UI."""
    image = QImage(ICON_BASE_SIZE, ICON_BASE_SIZE, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(COLORS["accent"]))
    painter.setPen(QPen(Qt.PenStyle.NoPen))
    margin = 32
    radius = 224
    painter.drawRoundedRect(
        margin,
        margin,
        ICON_BASE_SIZE - 2 * margin,
        ICON_BASE_SIZE - 2 * margin,
        radius,
        radius,
    )
    painter.setPen(QPen(QColor(COLORS["text"])))
    font = QFont()
    font.setPixelSize(660)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, "C")
    painter.end()
    return image


def _scaled(base: QImage, size: int) -> QImage:
    if size == ICON_BASE_SIZE:
        return base
    return base.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _png_bytes(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Не вдалося згенерувати PNG-іконку")
    data = bytes(buffer.data())
    buffer.close()
    return data


def _write_ico(images: list[tuple[int, bytes]], target: Path) -> None:
    """Write a Vista-compatible ICO using PNG-compressed entries."""
    count = len(images)
    offset = 6 + 16 * count
    entries = bytearray()
    payload = bytearray()
    for size, data in images:
        dimension = 0 if size >= 256 else size  # 0 means 256 in the ICO header
        entries += struct.pack(
            "<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset
        )
        payload += data
        offset += len(data)
    target.write_bytes(struct.pack("<HHH", 0, 1, count) + bytes(entries) + bytes(payload))


def _make_icon(system: str) -> Path:
    """Build a platform-native icon in build/icons (ignored by Git)."""
    icons_dir = ROOT / "build" / "icons"
    icons_dir.mkdir(parents=True, exist_ok=True)
    base = _draw_icon()
    base.save(str(icons_dir / "app.png"), "PNG")

    if system == "Darwin":
        iconset = icons_dir / "app.iconset"
        if iconset.exists():
            shutil.rmtree(iconset)
        iconset.mkdir()
        for filename, size in MAC_ICONSET_ENTRIES:
            _scaled(base, size).save(str(iconset / filename), "PNG")
        icns = icons_dir / "app.icns"
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)], check=True
        )
        return icns

    if system == "Windows":
        images = [
            (size, _png_bytes(_scaled(base, size))) for size in WIN_ICON_SIZES
        ]
        ico = icons_dir / "app.ico"
        _write_ico(images, ico)
        return ico

    raise SystemExit(f"Unsupported build platform: {system}")


def build(onefile: bool = False) -> Path:
    system = platform.system()
    if system not in ("Darwin", "Windows"):
        raise SystemExit("Builds are supported only on macOS and Windows.")

    try:
        import PyInstaller  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "PyInstaller is missing. Install it with: "
            "python -m pip install -r requirements-dev.txt"
        ) from exc

    if onefile and system != "Windows":
        raise SystemExit("--onefile applies to the Windows build only.")

    platform_dir = "macos" if system == "Darwin" else "windows"
    dist = ROOT / "dist" / platform_dir
    work = ROOT / "build" / platform_dir
    icon = _make_icon(system)

    # Qt plugins, the SQLite driver and the tray code are discovered by the
    # PyInstaller hooks. The extra switches make the runtime imports explicit;
    # translations live in app/i18n.py and are included with the app package.
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--distpath",
        str(dist),
        "--workpath",
        str(work),
        "--specpath",
        str(work),
        "--icon",
        str(icon),
        "--hidden-import",
        "PySide6.QtCore",
        "--hidden-import",
        "PySide6.QtGui",
        "--hidden-import",
        "PySide6.QtWidgets",
        "--hidden-import",
        "PySide6.QtNetwork",  # QLocalServer (single-instance guard)
        "--hidden-import",
        "sqlite3",
        "--hidden-import",
        "ctypes",  # Carbon / Win32 global hotkeys
        "--collect-submodules",
        "app",
        str(ROOT / "run.py"),
    ]
    if system == "Darwin":
        command += ["--osx-bundle-identifier", BUNDLE_ID]
    elif onefile:
        command += ["--onefile"]

    print("Building on", system)
    print(" ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)

    if system == "Darwin":
        expected = dist / f"{APP_NAME}.app"
    elif onefile:
        expected = dist / f"{APP_NAME}.exe"
    else:
        expected = dist / APP_NAME / f"{APP_NAME}.exe"

    if not expected.exists():
        raise SystemExit(f"Build finished but expected output is missing: {expected}")
    print(f"READY: {expected}")
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--onefile",
        action="store_true",
        help="Windows only: produce a single .exe instead of a distribution folder.",
    )
    args = parser.parse_args()
    build(onefile=args.onefile)


if __name__ == "__main__":
    main()
