"""Ventana principal (etapa 2): analizar URL y descargar un video con progreso."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from d_zen.core.downloader import Progress, VideoInfo
from d_zen.core.ffmpeg import ffmpeg_location
from d_zen.core.formats import Mode, build_options
from d_zen.ui.workers import AnalyzeWorker, DownloadWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("d-zen")
        self.resize(640, 520)
        self._info: VideoInfo | None = None
        self._analyze_worker: AnalyzeWorker | None = None
        self._download_worker: DownloadWorker | None = None
        self._dest = str(Path.home() / "Downloads")

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Pega aquí la URL del video…")
        self.url_edit.returnPressed.connect(self.analyze)
        self.analyze_btn = QPushButton("Analizar")
        self.analyze_btn.clicked.connect(self.analyze)
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.analyze_btn)
        layout.addLayout(row)

        info_row = QHBoxLayout()
        self.thumb = QLabel()
        self.thumb.setFixedSize(220, 124)
        self.thumb.setAlignment(Qt.AlignCenter)
        self.thumb.setStyleSheet("background:#222;color:#888;")
        self.thumb.setText("Sin miniatura")
        grid = QGridLayout()
        self.title_lbl = QLabel("—")
        self.title_lbl.setWordWrap(True)
        self.channel_lbl = QLabel("—")
        self.duration_lbl = QLabel("—")
        for i, (name, w) in enumerate(
            [("Título:", self.title_lbl), ("Canal:", self.channel_lbl), ("Duración:", self.duration_lbl)]
        ):
            grid.addWidget(QLabel(name), i, 0, Qt.AlignTop)
            grid.addWidget(w, i, 1)
        grid.setColumnStretch(1, 1)
        info_row.addWidget(self.thumb)
        info_row.addLayout(grid, 1)
        layout.addLayout(info_row)

        qrow = QHBoxLayout()
        qrow.addWidget(QLabel("Calidad:"))
        self.quality_combo = QComboBox()
        self.quality_combo.setEnabled(False)
        qrow.addWidget(self.quality_combo, 1)
        layout.addLayout(qrow)

        drow = QHBoxLayout()
        drow.addWidget(QLabel("Carpeta:"))
        self.dest_edit = QLineEdit(self._dest)
        self.dest_edit.setReadOnly(True)
        browse = QPushButton("Examinar…")
        browse.clicked.connect(self.choose_folder)
        drow.addWidget(self.dest_edit, 1)
        drow.addWidget(browse)
        layout.addLayout(drow)

        self.download_btn = QPushButton("Descargar")
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.status_lbl = QLabel("Listo.")
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_lbl)
        layout.addStretch(1)

    # --- análisis ---
    def analyze(self) -> None:
        if self._analyze_worker and self._analyze_worker.isRunning():
            return
        self.analyze_btn.setEnabled(False)
        self.download_btn.setEnabled(False)
        self.status_lbl.setText("Analizando…")
        self._analyze_worker = AnalyzeWorker(self.url_edit.text())
        self._analyze_worker.finished_ok.connect(self._on_analyzed)
        self._analyze_worker.failed.connect(self._on_analyze_failed)
        self._analyze_worker.start()

    def _on_analyzed(self, info: VideoInfo, thumb_data: bytes | None) -> None:
        self._info = info
        self.analyze_btn.setEnabled(True)
        self.title_lbl.setText(info.title)
        self.channel_lbl.setText(info.channel)
        self.duration_lbl.setText(info.duration_label)
        pix = QPixmap()
        if thumb_data and pix.loadFromData(thumb_data):
            self.thumb.setPixmap(pix.scaled(self.thumb.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.thumb.setPixmap(QPixmap())
            self.thumb.setText("Sin miniatura")
        self.quality_combo.clear()
        for q in info.qualities:
            self.quality_combo.addItem(q.display, q.height)
        self.quality_combo.setEnabled(True)
        self.download_btn.setEnabled(True)
        self.status_lbl.setText("Video analizado.")

    def _on_analyze_failed(self, message: str) -> None:
        self.analyze_btn.setEnabled(True)
        self.status_lbl.setText("Error.")
        QMessageBox.warning(self, "No se pudo analizar", message)

    # --- descarga ---
    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de destino", self._dest)
        if folder:
            self._dest = folder
            self.dest_edit.setText(folder)

    def start_download(self) -> None:
        if not self._info or (self._download_worker and self._download_worker.isRunning()):
            return
        options = build_options(
            Mode.VIDEO, height=self.quality_combo.currentData(),
            dest_dir=self._dest, ffmpeg_dir=ffmpeg_location(),
        )
        self.download_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_lbl.setText("Iniciando descarga…")
        w = DownloadWorker(self._info.url, options)
        w.progress.connect(self._on_progress)
        w.finished_ok.connect(self._on_download_done)
        w.failed.connect(self._on_download_failed)
        self._download_worker = w
        w.start()

    def _on_progress(self, p: Progress) -> None:
        self.progress_bar.setValue(int(p.percent))
        if p.status == "processing":
            self.status_lbl.setText("Procesando…")
        else:
            self.status_lbl.setText(f"{p.percent:.1f}% — {p.speed_label} — quedan {p.eta_label}")

    def _on_download_done(self) -> None:
        self.progress_bar.setValue(100)
        self.status_lbl.setText("Descarga completada.")
        self.download_btn.setEnabled(True)

    def _on_download_failed(self, message: str) -> None:
        self.status_lbl.setText("Error.")
        self.download_btn.setEnabled(True)
        QMessageBox.warning(self, "Error de descarga", message)

    def closeEvent(self, event) -> None:
        for w in (self._analyze_worker, self._download_worker):
            if w and w.isRunning():
                if isinstance(w, DownloadWorker):
                    w.cancel()
                w.wait(3000)
        super().closeEvent(event)
