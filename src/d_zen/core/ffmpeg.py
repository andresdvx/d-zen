"""Localización de ffmpeg (PATH o carpeta bin/ junto al ejecutable)."""
import shutil
import sys
from pathlib import Path

INSTALL_INSTRUCTIONS = (
    "ffmpeg no se encontró. Es necesario para unir video+audio y convertir audio.\n"
    "• Windows: descarga una build desde https://www.gyan.dev/ffmpeg/builds/ y copia "
    "ffmpeg.exe (y ffprobe.exe) a la carpeta 'bin' junto a d-zen, o agrégala al PATH "
    "(o: winget install Gyan.FFmpeg).\n"
    "• macOS: brew install ffmpeg\n"
    "• Linux: sudo apt install ffmpeg (o el gestor de tu distribución)."
)


def app_bin_dir() -> Path:
    """Carpeta bin/ junto al ejecutable (empaquetado) o a la raíz del proyecto (código fuente)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "bin"
    return Path(__file__).resolve().parents[3] / "bin"


def bundled_bin_dir() -> Path | None:
    """Carpeta bin/ extraída dentro del ejecutable de un solo archivo (PyInstaller --onefile)."""
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) / "bin" if base else None


def find_ffmpeg(extra_dirs: list[Path] | None = None) -> str | None:
    """Ruta al ejecutable de ffmpeg, o None si no está disponible.

    Orden: bin/ junto al ejecutable (permite sustituirlo), ffmpeg incluido en el .exe, PATH.
    """
    exe = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    bundled = bundled_bin_dir()
    for folder in [app_bin_dir(), *([bundled] if bundled else []), *(extra_dirs or [])]:
        candidate = Path(folder) / exe
        if candidate.is_file():
            return str(candidate)
    return shutil.which("ffmpeg")


def ffmpeg_location() -> str | None:
    """Carpeta a pasar a yt-dlp como `ffmpeg_location` (None = que use el PATH)."""
    found = find_ffmpeg()
    if found is None:
        return None
    return str(Path(found).parent)
