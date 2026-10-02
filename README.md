# D-ZEN

Descargador de video y audio de escritorio, hecho con Python, [yt-dlp](https://github.com/yt-dlp/yt-dlp) y PySide6.
Funciona en Windows y es compatible con Linux y macOS.

## Aviso legal

Úsalo solo con contenido propio, libre o que tengas permiso de descargar. Eres responsable de respetar los
términos de uso de cada plataforma y los derechos de autor. Los autores no se hacen responsables del mal uso.

## Características

- Analiza una URL sin descargar y muestra título, miniatura, duración y canal.
- Calidades realmente disponibles (2160p, 1080p, 720p…) con tamaño estimado, o «Mejor disponible».
- Modo **solo audio**: MP3, M4A, OPUS o WAV, con bitrate 128/192/320 kbps (cuando aplica).
- **Cola de descargas** procesada en orden, con progreso, velocidad y tiempo restante.
- Cancelación de la descarga en curso o de las pendientes.
- Recuerda la carpeta de destino, el formato de audio y la calidad preferida.
- Plantilla de nombre de archivo configurable (por defecto `%(title)s.%(ext)s`), con caracteres inválidos de Windows saneados.
- Menú **Herramientas**: versión y actualización de yt-dlp, plantilla de nombre, carpeta de logs, comprobación de ffmpeg.
- Mensajes claros ante URL inválida, video privado o no disponible, ffmpeg ausente y falta de conexión.

## Requisitos

- Python 3.11 o superior
- [ffmpeg](https://ffmpeg.org/) (para unir video+audio y convertir audio)

### Instalar ffmpeg

- **Windows:** `winget install Gyan.FFmpeg`, o descarga una build de <https://www.gyan.dev/ffmpeg/builds/> y copia
  `ffmpeg.exe` y `ffprobe.exe` a una carpeta `bin/` junto a D-ZEN (o al PATH).
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg` (o el gestor de tu distribución)

D-ZEN busca ffmpeg primero en la carpeta `bin/` junto al ejecutable y luego en el PATH. Al iniciar avisa si falta.

## Instalación (desde el código fuente)

```bash
git clone https://github.com/andresdvx/d-zen.git
cd d-zen
python -m venv .venv
.venv\Scripts\activate          # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

## Uso

```bash
python -m d_zen.main
```

1. Pega la URL y pulsa **Analizar**.
2. Elige **Video** (calidad) o **Solo audio** (formato y bitrate) y la carpeta de destino.
3. Pulsa **Agregar a la cola**. Puedes agregar tantos como quieras; se descargan uno tras otro.
4. La ✕ de cada elemento cancela (si está activo o en espera) o lo quita de la lista (si ya terminó).

Solo se descarga el video indicado, no la lista de reproducción completa.

### Plantilla de nombre

En *Herramientas → Plantilla de nombre de archivo…* puedes usar cualquier campo de yt-dlp, por ejemplo
`%(uploader)s - %(title)s.%(ext)s`. No se admiten rutas absolutas ni `..`.

### Archivos de la aplicación

- Configuración: `%LOCALAPPDATA%\d-zen\config.json` (Linux/macOS: directorio de configuración del usuario)
- Logs: `%LOCALAPPDATA%\d-zen\Logs\d-zen.log` (también desde el menú *Abrir carpeta de logs*)

## Actualizar yt-dlp

Los sitios cambian a menudo; si una descarga falla, actualiza yt-dlp desde *Herramientas → Actualizar yt-dlp*
(ejecuta `pip install -U yt-dlp`) y reinicia la aplicación. En el ejecutable empaquetado no hay pip: para
actualizar yt-dlp hay que recompilar (ver abajo).

## Pruebas

```bash
python -m pytest
```

Las pruebas usan datos simulados; no hacen llamadas a internet.

## Compilar el .exe

Para generar **un solo `D-ZEN.exe` con ffmpeg incluido**, coloca `ffmpeg.exe` y `ffprobe.exe` en `bin/` (raíz del
proyecto) y ejecuta:

```bash
pip install -e ".[dev]"
pyinstaller build.spec --noconfirm
```

El resultado es `dist/D-ZEN.exe` (~130 MB): no necesita Python ni ffmpeg instalados. Si hay una carpeta `bin/` junto al
`.exe`, se usa esa en lugar de la incluida (útil para cambiar de versión de ffmpeg).

Alternativa en carpeta (sin incluir ffmpeg): `D_ZEN_ONEDIR=1 pyinstaller build.spec --noconfirm` → `dist/D-ZEN/`.

> ffmpeg se distribuye bajo LGPL/GPL según la build. Si compartes el `.exe`, revisa la licencia de la build que
> incluyes (<https://ffmpeg.org/legal.html>).

### Icono

El icono está en `assets/` (`icon.ico` multitamaño y `icon.png`). Para regenerarlo: `python tools/make_icon.py`.

## Estructura

```
src/d_zen/
├── main.py
├── core/    # sin dependencias de PySide6: formats, downloader, queue, config, ffmpeg, updater, filenames
└── ui/      # main_window, workers (hilos), theme, widgets/
tests/
assets/      # icono (generado con tools/make_icon.py)
tools/       # utilidades de desarrollo
build.spec   # PyInstaller
```
