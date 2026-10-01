"""Sanitización de nombres de archivo para Windows."""
import re

DEFAULT_TEMPLATE = "%(title)s.%(ext)s"

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, replacement: str = "_") -> str:
    """Devuelve un nombre de archivo válido en Windows (y por tanto en Linux/macOS)."""
    cleaned = _INVALID_CHARS.sub(replacement, name).strip().rstrip(". ")
    if not cleaned:
        return "video"
    if cleaned.split(".")[0].upper() in _RESERVED:
        cleaned = f"{replacement}{cleaned}"
    return cleaned


def validate_template(template: str) -> str:
    """Normaliza una plantilla de yt-dlp; vuelve a la de por defecto si es inválida.

    No se permiten rutas absolutas ni '..' para que el archivo quede en la carpeta destino.
    Se deja intacto lo que está dentro de %(...)s.
    """
    template = (template or "").strip()
    if not template:
        return DEFAULT_TEMPLATE
    literal = re.sub(r"%\([^)]*\)[^a-zA-Z%]*[a-zA-Z]", "", template)
    if ".." in literal or re.match(r"^([a-zA-Z]:|[/\\])", literal):
        return DEFAULT_TEMPLATE
    if "%(ext)s" not in template:
        template += ".%(ext)s"
    return template
