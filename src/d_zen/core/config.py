"""Configuración persistente en JSON, en el directorio de configuración del usuario."""
import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from platformdirs import user_config_dir, user_log_dir

from .filenames import DEFAULT_TEMPLATE, validate_template
from .formats import AUDIO_BITRATES, AUDIO_FORMATS

APP_NAME = "d-zen"
log = logging.getLogger(__name__)


def config_path() -> Path:
    return Path(user_config_dir(APP_NAME, appauthor=False)) / "config.json"


def log_dir() -> Path:
    return Path(user_log_dir(APP_NAME, appauthor=False))


def default_dest_dir() -> str:
    return str(Path.home() / "Downloads")


@dataclass
class Config:
    dest_dir: str = ""
    audio_mode: bool = False  # último modo usado: False = video, True = solo audio
    audio_format: str = "mp3"
    audio_bitrate: int = 192
    default_height: int | None = None  # None = mejor disponible
    filename_template: str = DEFAULT_TEMPLATE

    def __post_init__(self) -> None:
        self.sanitize()

    def sanitize(self) -> None:
        """Corrige valores inválidos (archivo editado a mano o de otra versión)."""
        if not isinstance(self.dest_dir, str) or not self.dest_dir:
            self.dest_dir = default_dest_dir()
        self.audio_mode = bool(self.audio_mode)
        if self.audio_format not in AUDIO_FORMATS:
            self.audio_format = "mp3"
        if self.audio_bitrate not in AUDIO_BITRATES:
            self.audio_bitrate = 192
        if not (isinstance(self.default_height, int) and not isinstance(self.default_height, bool)
                and self.default_height > 0):
            self.default_height = None
        if not isinstance(self.filename_template, str):
            self.filename_template = DEFAULT_TEMPLATE
        self.filename_template = validate_template(self.filename_template)


def load(path: Path | None = None) -> Config:
    """Carga la configuración; ante cualquier problema devuelve los valores por defecto."""
    path = path or config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("el JSON raíz no es un objeto")
    except FileNotFoundError:
        return Config()
    except (OSError, ValueError) as exc:
        log.warning("Configuración ilegible (%s); se usan valores por defecto", exc)
        return Config()
    known = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in known})


def save(cfg: Config, path: Path | None = None) -> None:
    path = path or config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        log.exception("No se pudo guardar la configuración en %s", path)
