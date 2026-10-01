"""Versión y actualización de yt-dlp (vía pip)."""
import logging
import subprocess
import sys

log = logging.getLogger(__name__)


class UpdateError(Exception):
    pass


def installed_version() -> str:
    from yt_dlp.version import __version__
    return __version__


def can_update() -> bool:
    """En un ejecutable de PyInstaller no hay pip: hay que recompilar con la versión nueva."""
    return not getattr(sys, "frozen", False)


def update_ytdlp(timeout: int = 300) -> str:
    """Ejecuta `pip install -U yt-dlp` y devuelve la versión instalada tras actualizar.

    La versión nueva se usa al reiniciar la aplicación (el módulo ya está cargado).
    """
    if not can_update():
        raise UpdateError(
            "Esta versión empaquetada no puede actualizar yt-dlp. "
            "Instala una versión nueva de D-ZEN o ejecútalo desde el código fuente."
        )
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise UpdateError("La actualización tardó demasiado. Revisa tu conexión.") from exc
    except OSError as exc:
        raise UpdateError(f"No se pudo ejecutar pip: {exc}") from exc
    log.info("pip: %s", result.stdout.strip()[-500:])
    if result.returncode != 0:
        log.error("pip falló: %s", result.stderr.strip())
        tail = (result.stderr.strip().splitlines() or ["error desconocido"])[-1]
        raise UpdateError(f"pip falló: {tail}")
    return _version_in_new_process()


def _version_in_new_process() -> str:
    out = subprocess.run(
        [sys.executable, "-c", "from yt_dlp.version import __version__ as v; print(v)"],
        capture_output=True, text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return out.stdout.strip() or installed_version()
