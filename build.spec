# PyInstaller: pyinstaller build.spec --noconfirm
#   Por defecto genera UN solo .exe (dist/D-ZEN.exe) con ffmpeg/ffprobe de bin/ incluidos.
#   D_ZEN_ONEDIR=1 genera una carpeta (dist/D-ZEN/) en vez de un solo archivo.
import os
from pathlib import Path

root = Path(SPECPATH)
onedir = os.environ.get("D_ZEN_ONEDIR") == "1"

datas = [(str(root / "src" / "d_zen" / "ui" / "arrow_down.png"), "d_zen/ui"),
         (str(root / "assets" / "icon.png"), "assets")]
binaries = []
if not onedir:
    for name in ("ffmpeg.exe", "ffprobe.exe", "ffmpeg", "ffprobe"):
        f = root / "bin" / name
        if f.is_file():
            binaries.append((str(f), "bin"))
    if not binaries:
        raise SystemExit("Falta bin/ffmpeg.exe y bin/ffprobe.exe para incluirlos en el .exe")

a = Analysis(
    [str(root / "src" / "d_zen" / "main.py")],
    pathex=[str(root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=["yt_dlp.postprocessor", "yt_dlp.extractor"],
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
)
pyz = PYZ(a.pure)
icon = str(root / "assets" / "icon.ico")

if onedir:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="D-ZEN", console=False, icon=icon)
    coll = COLLECT(exe, a.binaries, a.datas, name="D-ZEN")
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="D-ZEN", console=False, icon=icon)
