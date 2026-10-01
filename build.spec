# PyInstaller: pyinstaller build.spec
from pathlib import Path

root = Path(SPECPATH)

a = Analysis(
    [str(root / "src" / "d_zen" / "main.py")],
    pathex=[str(root / "src")],
    datas=[(str(root / "src" / "d_zen" / "ui" / "arrow_down.png"), "d_zen/ui"),
           (str(root / "assets" / "icon.png"), "assets")],
    hiddenimports=["yt_dlp.postprocessor", "yt_dlp.extractor"],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="D-ZEN",
    console=False,
    icon=str(root / "assets" / "icon.ico"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="D-ZEN")
