# Building on Windows

Build the Windows executable on Windows (native machine, Windows VM, or Windows
CI runner). A normal PyInstaller installation on macOS cannot produce a Windows
`.exe`.

## Prerequisites

- Windows 10/11 with Python 3.10+ (`py -3 --version`)
- Microsoft Visual C++ runtime is normally already present; no compiler is
  needed because PyInstaller ships prebuilt bootloaders.

## Build (onedir, recommended)

PowerShell from the repository root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
scripts\build_windows.bat
```

Output:

```text
dist\windows\Clipboard Manager\Clipboard Manager.exe
```

Distribute the whole `dist\windows\Clipboard Manager` folder, not just the
`.exe`: the Qt runtime lives next to it. The `.bat` file is a convenience
wrapper around `scripts\build_app.py`, so
`python scripts\build_app.py` works too.

## Build (single file, optional)

```powershell
python scripts\build_app.py --onefile
```

Output:

```text
dist\windows\Clipboard Manager.exe
```

This is a single `.exe` but starts slower because PyInstaller extracts Qt to a
temporary folder on every launch. The default onedir build is recommended for a
tray application that stays running.

## What the build includes

- **Qt runtime**: PySide6 hooks collect the Qt platform/style plugins.
  `QtNetwork` is imported explicitly for the single-instance `QLocalServer`.
- **Interface and translations**: all modules under `app/` are collected via
  `--collect-submodules app`. Translations are Python dictionaries in
  `app/i18n.py`, so no separate translation files are needed.
- **System tray**: `app/tray.py` creates one `QSystemTrayIcon` and draws its icon
  at runtime. Right-click the tray icon → **Quit** exits fully; closing the
  window only hides it.
- **SQLite**: the standard-library `sqlite3` module is included. The database is
  never stored next to the executable.
- **Global hotkeys**: `ctypes` calls `RegisterHotKey` from `user32.dll`, which is
  part of Windows. No extra DLL is bundled.
- **App icon**: `scripts\build_app.py` renders a PNG with Qt and writes a
  PNG-compressed `.ico` with sizes 16–256 into `build\icons\`. Generated files
  are ignored by Git.

## Where user data is stored

`QStandardPaths` uses organization `ClipboardManager` and application name
`Clipboard Manager`:

```text
%APPDATA%\ClipboardManager\Clipboard Manager\history.sqlite3
```

Autostart writes `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`. Both are
outside `dist\windows`, so rebuilding or deleting the build folder does not
remove history or settings.

## Troubleshooting

- If SmartScreen warns about a locally built file, choose **More info → Run
  anyway**. Code signing is out of scope for this project.
- If `Activate.ps1` is blocked, run
  `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.
- To remove stale artifacts: delete `build` and `dist`, then rebuild.
