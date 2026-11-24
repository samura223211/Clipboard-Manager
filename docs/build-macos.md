# Building on macOS

This produces a native `Clipboard Manager.app` bundle. Run these commands on a
Mac; PyInstaller does not cross-build macOS or Windows binaries from another OS.

## Prerequisites

- macOS with Python 3.10+ (`python3 --version`)
- Command Line Tools (needed by `iconutil`): `xcode-select --install` if missing

## Build

```bash
git clone <repository-url> ClipboardManager
cd ClipboardManager
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
bash scripts/build_macos.sh
```

The shared driver lives at `scripts/build_app.py`; the shell script is only a
convenience wrapper, so `python scripts/build_app.py` works as well.

Output:

```text
dist/macos/Clipboard Manager.app
```

Run it with `open "dist/macos/Clipboard Manager.app"` or by double-clicking in Finder.

## What the build includes

- **Qt runtime**: PySide6 hooks collect the required Qt plugins (platforms,
  styles, image formats). `QtNetwork` is imported explicitly for the
  single-instance `QLocalServer`.
- **Interface and translations**: all modules under `app/` are collected via
  `--collect-submodules app`. Translations are Python dictionaries in
  `app/i18n.py`, so there are no separate translation files to copy.
- **System tray**: `app/tray.py` draws its menu-bar icon at runtime with
  `QPainter`. No tray image file is required.
- **SQLite**: the standard-library `sqlite3` module and its extension are
  included. The database is **not** written into the bundle.
- **Global hotkeys**: `ctypes` calls into the macOS Carbon framework, which is
  part of the OS. No extra binary needs to be bundled. macOS may request
  Accessibility / Input Monitoring permission on first use.
- **App icon**: `scripts/build_app.py` renders a PNG with Qt, expands it into an
  `.iconset`, and converts it to `.icns` via `iconutil`. The generated files are
  kept in `build/icons/` and are ignored by Git.
- **Bundle identifier**: `com.clipboardmanager`, matching the LaunchAgent label
  used by the autostart feature.

## Where user data is stored

`QStandardPaths` is used with organization `ClipboardManager` and application
name `Clipboard Manager`:

```text
~/Library/Application Support/ClipboardManager/Clipboard Manager/history.sqlite3
```

Autostart writes `~/Library/LaunchAgents/com.clipboardmanager.plist`. Neither
path is inside the `.app` bundle, so rebuilding or deleting the bundle never
deletes the user's history or settings.

## Troubleshooting

- If macOS blocks the downloaded app, right-click it and choose **Open**, then
  confirm. For a locally built app this normally does not happen.
- If global hotkeys do not fire, check System Settings → Privacy & Security for
  Accessibility / Input Monitoring entries for the app.
- To remove stale build artifacts: `rm -rf build dist` and run the script again;
  PyInstaller also cleans automatically with `--clean`.
