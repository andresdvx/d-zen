"""Wrapper de yt-dlp (usado como librería). No depende de PySide6."""
import logging
import threading
from dataclasses import dataclass
from typing import Callable

import yt_dlp
from yt_dlp.utils import DownloadError

from .ffmpeg import INSTALL_INSTRUCTIONS, find_ffmpeg
from .formats import QualityOption, parse_qualities

log = logging.getLogger(__name__)


class DownloaderError(Exception):
    """Error con mensaje apto para mostrar al usuario."""


class InvalidURLError(DownloaderError):
    pass


class UnavailableError(DownloaderError):
    pass


class FfmpegMissingError(DownloaderError):
    pass


class NetworkError(DownloaderError):
    pass


class CancelledError(DownloaderError):
    pass


@dataclass(frozen=True)
class VideoInfo:
    url: str
    title: str
    channel: str
    duration: int | None  # segundos
    thumbnail: str | None
    qualities: list[QualityOption]

    @property
    def duration_label(self) -> str:
        if self.duration is None:
            return "—"
        h, rem = divmod(int(self.duration), 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


@dataclass(frozen=True)
class Progress:
    status: str  # "downloading" | "processing" | "finished"
    percent: float  # 0-100
    speed: float | None  # bytes/s
    eta: int | None  # segundos
    downloaded: int | None = None
    total: int | None = None

    @property
    def speed_label(self) -> str:
        if not self.speed:
            return "—"
        return f"{self.speed / (1024 * 1024):.2f} MB/s"

    @property
    def eta_label(self) -> str:
        if self.eta is None:
            return "—"
        m, s = divmod(int(self.eta), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


ProgressCallback = Callable[[Progress], None]

_NETWORK_HINTS = (
    "getaddrinfo failed", "name or service not known", "temporary failure in name resolution",
    "network is unreachable", "connection refused", "connection reset", "timed out",
    "unable to download", "no address associated", "urlopen error", "transporterror",
    "failed to resolve",
)
_UNAVAILABLE_HINTS = (
    "private video", "video unavailable", "this video is not available", "has been removed",
    "sign in to confirm", "members-only", "requires authentication", "login required",
    "this video is private", "age-restricted", "not available in your country", "geo restricted", "geo-restricted",
    "copyright", "been terminated", "does not exist",
)
_INVALID_HINTS = ("unsupported url", "is not a valid url", "no video formats", "invalid url")


def classify_error(exc: BaseException) -> DownloaderError:
    """Convierte excepciones de yt-dlp en errores con mensaje claro para el usuario."""
    if isinstance(exc, DownloaderError):
        return exc
    raw = str(exc)
    msg = raw.lower()
    if "ffmpeg" in msg or "ffprobe" in msg:
        return FfmpegMissingError(INSTALL_INSTRUCTIONS)
    if any(h in msg for h in _INVALID_HINTS):
        return InvalidURLError("La URL no es válida o el sitio no está soportado.")
    if any(h in msg for h in _UNAVAILABLE_HINTS):
        return UnavailableError(
            "El video no está disponible (privado, eliminado, con restricción de edad o de región)."
        )
    if any(h in msg for h in _NETWORK_HINTS):
        return NetworkError("No se pudo conectar. Revisa tu conexión a internet.")
    return DownloaderError(f"Error al procesar el video: {raw.splitlines()[0] if raw else exc!r}")


def _looks_like_url(url: str) -> bool:
    return url.lower().startswith(("http://", "https://")) and "." in url and " " not in url


def _find_cancel(exc: BaseException | None) -> bool:
    while exc is not None:
        if isinstance(exc, CancelledError):
            return True
        exc = exc.__cause__ or exc.__context__
    return False


def analyze(url: str, ydl_factory=yt_dlp.YoutubeDL) -> VideoInfo:
    """Obtiene la información del video sin descargarlo."""
    url = (url or "").strip()
    if not _looks_like_url(url):
        raise InvalidURLError("Pega una URL válida (debe empezar con http:// o https://).")
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "skip_download": True}
    try:
        with ydl_factory(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as exc:  # yt-dlp lanza varios tipos
        log.exception("Fallo al analizar %s", url)
        raise classify_error(exc) from exc
    if not info:
        raise UnavailableError("No se pudo obtener información del video.")
    return VideoInfo(
        url=url,
        title=info.get("title") or "Sin título",
        channel=info.get("channel") or info.get("uploader") or "—",
        duration=info.get("duration"),
        thumbnail=info.get("thumbnail"),
        qualities=parse_qualities(info),
    )


def _make_hook(on_progress: ProgressCallback | None, cancel: threading.Event | None):
    def hook(d: dict) -> None:
        if cancel is not None and cancel.is_set():
            raise CancelledError("Descarga cancelada.")
        if on_progress is None:
            return
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes")
            percent = (done / total * 100) if total and done is not None else 0.0
            on_progress(Progress("downloading", min(percent, 100.0), d.get("speed"),
                                 d.get("eta"), done, total))
        elif status == "finished":
            on_progress(Progress("processing", 100.0, None, None))

    return hook


def download(
    url: str,
    options: dict,
    on_progress: ProgressCallback | None = None,
    cancel: threading.Event | None = None,
    ydl_factory=yt_dlp.YoutubeDL,
) -> None:
    """Descarga con las opciones construidas por `formats.build_options`.

    Lanza CancelledError si `cancel` se activa, y errores DownloaderError claros en otros casos.
    """
    if not _looks_like_url(url or ""):
        raise InvalidURLError("Pega una URL válida (debe empezar con http:// o https://).")
    needs_ffmpeg = bool(options.get("postprocessors")) or "+" in str(options.get("format", ""))
    if needs_ffmpeg and not options.get("ffmpeg_location") and find_ffmpeg() is None:
        raise FfmpegMissingError(INSTALL_INSTRUCTIONS)

    opts = dict(options)
    opts["progress_hooks"] = [_make_hook(on_progress, cancel), *opts.get("progress_hooks", [])]
    try:
        with ydl_factory(opts) as ydl:
            ydl.download([url])
    except Exception as exc:
        if _find_cancel(exc) or (cancel is not None and cancel.is_set()):
            raise CancelledError("Descarga cancelada.") from exc
        if isinstance(exc, DownloadError) or not isinstance(exc, DownloaderError):
            log.exception("Fallo al descargar %s", url)
        raise classify_error(exc) from exc
