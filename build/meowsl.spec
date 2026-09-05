# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

# SPECPATH = папка build; корень проекта — на уровень выше
ROOT = Path(SPECPATH).parent

winocr_datas, winocr_binaries, winocr_hiddenimports = collect_all("winocr")
winrt_hiddenimports = collect_submodules("winrt")

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=winocr_binaries,
    datas=[
        (str(ROOT / "photo" / "logo.png"), "photo"),
        (str(ROOT / "photo" / "logo-icon.png"), "photo"),
        (str(ROOT / "photo" / "logo-icon.ico"), "photo"),
        *winocr_datas,
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "deep_translator",
        "requests",
        "bs4",
        "keyboard",
        "winocr",
        "PIL",
        "PIL.Image",
        "winrt.windows.media.ocr",
        "winrt.windows.globalization",
        "winrt.windows.graphics.imaging",
        "winrt.windows.storage.streams",
        "winrt.windows.foundation",
        "winrt.windows.foundation.collections",
        *winocr_hiddenimports,
        *winrt_hiddenimports,
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="MeowsL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(
        ROOT / "photo" / "logo-icon.ico"
        if (ROOT / "photo" / "logo-icon.ico").is_file()
        else "logo.png"
    ),
)
