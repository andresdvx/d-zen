"""Parseo de formatos disponibles y construcción de opciones de yt-dlp."""
from dataclasses import dataclass
from enum import Enum

from .filenames import DEFAULT_TEMPLATE, validate_template

AUDIO_FORMATS = ("mp3", "m4a", "opus", "wav")
AUDIO_BITRATES = (128, 192, 320)
# wav no tiene bitrate (sin pérdida)
_BITRATE_FORMATS = {"mp3", "m4a", "opus"}


class Mode(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(frozen=True)
class QualityOption:
    """Una resolución disponible. height=None significa «Mejor disponible»."""
    height: int | None
    label: str
    filesize: int | None = None  # bytes estimados

    @property
    def size_label(self) -> str:
        return format_size(self.filesize) if self.filesize else ""

    @property
    def display(self) -> str:
        return f"{self.label} (~{self.size_label})" if self.filesize else self.label


BEST = QualityOption(height=None, label="Mejor disponible")


def format_size(size: int | float | None) -> str:
    if not size:
        return ""
    size = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


def _size(fmt: dict) -> int | None:
    return fmt.get("filesize") or fmt.get("filesize_approx") or None


def _has_video(fmt: dict) -> bool:
    return fmt.get("vcodec") not in (None, "none") and bool(fmt.get("height"))


def _has_audio(fmt: dict) -> bool:
    return fmt.get("acodec") not in (None, "none")


def parse_qualities(info: dict) -> list[QualityOption]:
    """Resoluciones realmente disponibles (de mayor a menor), precedidas por «Mejor disponible».

    El tamaño estimado de cada resolución es el del mejor formato de esa altura más el del mejor
    audio cuando el formato de video no lo incluye. Si falta algún dato, no se muestra tamaño.
    """
    formats = info.get("formats") or []
    audio_only = [f for f in formats if _has_audio(f) and not _has_video(f)]
    best_audio_size = max((_size(f) or 0 for f in audio_only), default=0) or None

    by_height: dict[int, dict] = {}
    for fmt in formats:
        if not _has_video(fmt):
            continue
        h = int(fmt["height"])
        current = by_height.get(h)
        if current is None or (fmt.get("tbr") or 0) > (current.get("tbr") or 0):
            by_height[h] = fmt

    options = [BEST]
    for h in sorted(by_height, reverse=True):
        fmt = by_height[h]
        size = _size(fmt)
        if size and not _has_audio(fmt):
            size = size + best_audio_size if best_audio_size else None
        options.append(QualityOption(height=h, label=f"{h}p", filesize=size))
    return options


def build_options(
    mode: Mode = Mode.VIDEO,
    height: int | None = None,
    audio_format: str = "mp3",
    audio_bitrate: int | None = 192,
    outtmpl: str = DEFAULT_TEMPLATE,
    dest_dir: str | None = None,
    ffmpeg_dir: str | None = None,
) -> dict:
    """Opciones de yt-dlp para una descarga. No incluye hooks (los añade el downloader)."""
    template = validate_template(outtmpl)
    opts: dict = {
        "noplaylist": True,
        "windowsfilenames": True,
        "outtmpl": f"{dest_dir}/{template}" if dest_dir else template,
        "quiet": True,
        "no_warnings": True,
    }
    if ffmpeg_dir:
        opts["ffmpeg_location"] = ffmpeg_dir

    if mode == Mode.AUDIO:
        if audio_format not in AUDIO_FORMATS:
            raise ValueError(f"Formato de audio no soportado: {audio_format}")
        post: dict = {"key": "FFmpegExtractAudio", "preferredcodec": audio_format}
        if audio_format in _BITRATE_FORMATS and audio_bitrate:
            if audio_bitrate not in AUDIO_BITRATES:
                raise ValueError(f"Bitrate no soportado: {audio_bitrate}")
            post["preferredquality"] = str(audio_bitrate)
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [post]
        return opts

    if height:
        opts["format"] = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
    else:
        opts["format"] = "bestvideo+bestaudio/best"
    opts["merge_output_format"] = "mp4"
    return opts


def bitrate_applies(audio_format: str) -> bool:
    return audio_format in _BITRATE_FORMATS
