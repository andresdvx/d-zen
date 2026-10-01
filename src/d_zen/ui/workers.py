"""Workers en hilo que envuelven `core` y emiten señales Qt."""
import threading
import urllib.request

from PySide6.QtCore import QObject, QThread, Signal

from d_zen.core import downloader
from d_zen.core.downloader import CancelledError, DownloaderError, Progress, VideoInfo


class AnalyzeWorker(QThread):
    finished_ok = Signal(object, object)  # VideoInfo, bytes de la miniatura (o None)
    failed = Signal(str)

    def __init__(self, url: str, parent: QObject | None = None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        try:
            info: VideoInfo = downloader.analyze(self._url)
        except DownloaderError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:  # no dejar morir el hilo en silencio
            self.failed.emit(f"Error inesperado: {exc}")
            return
        self.finished_ok.emit(info, self._fetch_thumbnail(info.thumbnail))

    @staticmethod
    def _fetch_thumbnail(url: str | None) -> bytes | None:
        if not url:
            return None
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.read()
        except Exception:
            return None


class DownloadWorker(QThread):
    progress = Signal(object)  # Progress
    finished_ok = Signal()
    cancelled = Signal()
    failed = Signal(str)

    def __init__(self, url: str, options: dict, parent: QObject | None = None):
        super().__init__(parent)
        self._url = url
        self._options = options
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        try:
            downloader.download(self._url, self._options,
                                on_progress=self.progress.emit, cancel=self._cancel)
        except CancelledError:
            self.cancelled.emit()
        except DownloaderError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"Error inesperado: {exc}")
        else:
            self.finished_ok.emit()
