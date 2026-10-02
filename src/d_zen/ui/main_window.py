"""Ventana principal: analizar URL, elegir video/audio y administrar la cola de descargas."""
import logging
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QInputDialog, QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from d_zen import __version__
from d_zen.core import config as cfgmod
from d_zen.core import updater
from d_zen.core.downloader import Progress, VideoInfo
from d_zen.core.ffmpeg import INSTALL_INSTRUCTIONS, ffmpeg_location, find_ffmpeg
from d_zen.core.formats import AUDIO_BITRATES, AUDIO_FORMATS, Mode, bitrate_applies, build_options
from d_zen.core.queue import DownloadJob, DownloadQueue, JobStatus
from d_zen.ui.widgets.queue_item import QueueItem
from d_zen.ui.workers import AnalyzeWorker, DownloadWorker, UpdateWorker


def _card() -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 22)
    layout.setSpacing(14)
    return frame, layout


def _section(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setObjectName("section")
    return lbl


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("D-ZEN")
        self.resize(1180, 760)
        self.setMinimumSize(1000, 660)

        self._info: VideoInfo | None = None
        self._analyze_worker: AnalyzeWorker | None = None
        self._workers: set[DownloadWorker] = set()
        self._active_worker: DownloadWorker | None = None
        self.cfg = cfgmod.load()
        self._dest = self.cfg.dest_dir
        self._update_worker: UpdateWorker | None = None
        self.queue = DownloadQueue()
        self._items: dict[int, QueueItem] = {}

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(32, 26, 32, 28)
        outer.setSpacing(22)
        self._build_menu()
        outer.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setSpacing(24)
        body.addWidget(self._build_left(), 11)
        body.addWidget(self._build_right(), 9)
        outer.addLayout(body, 1)
        self._restore_preferences()
        self._refresh_empty_state()
        QTimer.singleShot(300, self._check_ffmpeg)

    # ---------- menú, configuración y herramientas ----------
    def _build_menu(self) -> None:
        tools = self.menuBar().addMenu("Herramientas")
        for text, slot in [
            ("Versión de yt-dlp…", self.show_versions),
            ("Actualizar yt-dlp", self.update_ytdlp),
            ("Plantilla de nombre de archivo…", self.edit_template),
            ("Abrir carpeta de logs", lambda: QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(cfgmod.log_dir())))),
            ("Comprobar ffmpeg", lambda: self._check_ffmpeg(notify_ok=True)),
        ]:
            action = QAction(text, self)
            action.triggered.connect(slot)
            tools.addAction(action)
        self.update_action = tools.actions()[1]

    def _restore_preferences(self) -> None:
        i = self.audio_fmt_combo.findData(self.cfg.audio_format)
        self.audio_fmt_combo.setCurrentIndex(max(i, 0))
        self.bitrate_combo.setCurrentIndex(max(self.bitrate_combo.findData(self.cfg.audio_bitrate), 0))
        self._sync_bitrate()
        (self.audio_btn if self.cfg.audio_mode else self.video_btn).setChecked(True)

    def _save_preferences(self) -> None:
        self.cfg.dest_dir = self._dest
        self.cfg.audio_mode = self.audio_btn.isChecked()
        self.cfg.audio_format = self.audio_fmt_combo.currentData()
        self.cfg.audio_bitrate = self.bitrate_combo.currentData()
        if self.quality_combo.isEnabled():
            self.cfg.default_height = self.quality_combo.currentData()
        self.cfg.sanitize()
        cfgmod.save(self.cfg)

    def _check_ffmpeg(self, notify_ok: bool = False) -> None:
        found = find_ffmpeg()
        logging.getLogger(__name__).info("ffmpeg: %s", found or "no encontrado")
        if found is None:
            QMessageBox.warning(self, "D-ZEN — falta ffmpeg", INSTALL_INSTRUCTIONS)
        elif notify_ok:
            QMessageBox.information(self, "D-ZEN", f"ffmpeg disponible:\n{found}")

    def show_versions(self) -> None:
        QMessageBox.information(
            self, "Versiones",
            f"D-ZEN {__version__}\nyt-dlp {updater.installed_version()}\n\n"
            f"Configuración: {cfgmod.config_path()}\nLogs: {cfgmod.log_dir()}")

    def update_ytdlp(self) -> None:
        if self._update_worker and self._update_worker.isRunning():
            return
        if not updater.can_update():
            QMessageBox.information(
                self, "Actualizar yt-dlp",
                f"yt-dlp {updater.installed_version()}\n\n"
                "Esta versión empaquetada no puede actualizarse sola. "
                "Descarga una versión nueva de D-ZEN o ejecútalo desde el código fuente.")
            return
        self.update_action.setEnabled(False)
        self._set_feedback("Actualizando yt-dlp…")
        w = UpdateWorker()
        w.finished_ok.connect(self._on_update_ok)
        w.failed.connect(self._on_update_failed)
        self._update_worker = w
        w.start()

    def _on_update_ok(self, version: str) -> None:
        self.update_action.setEnabled(True)
        self._set_feedback(f"yt-dlp actualizado a {version}. Reinicia D-ZEN para usarlo.", "ok")

    def _on_update_failed(self, message: str) -> None:
        self.update_action.setEnabled(True)
        self._set_feedback(message, "error")

    def edit_template(self) -> None:
        text, ok = QInputDialog.getText(
            self, "Plantilla de nombre",
            "Plantilla de yt-dlp (p. ej. %(title)s.%(ext)s o %(uploader)s - %(title)s.%(ext)s):",
            text=self.cfg.filename_template)
        if ok:
            self.cfg.filename_template = text
            self.cfg.sanitize()
            cfgmod.save(self.cfg)
            self._set_feedback(f"Plantilla: {self.cfg.filename_template}", "ok")

    # ---------- construcción de UI ----------
    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(0)
        brand = QLabel("D-ZEN")
        brand.setObjectName("brand")
        tagline = QLabel("Descarga video y audio, sin ruido.")
        tagline.setObjectName("tagline")
        col.addWidget(brand)
        col.addWidget(tagline)
        row.addLayout(col)
        row.addStretch(1)
        return row

    def _build_left(self) -> QWidget:
        card, lay = _card()

        lay.addWidget(_section("Enlace"))
        row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Pega aquí la URL del video…")
        self.url_edit.setClearButtonEnabled(True)
        self.url_edit.returnPressed.connect(self.analyze)
        self.analyze_btn = QPushButton("Analizar")
        self.analyze_btn.setObjectName("primary")
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(self.analyze)
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.analyze_btn)
        lay.addLayout(row)
        self.feedback = QLabel("")
        self.feedback.setObjectName("feedback")
        self.feedback.setWordWrap(True)
        lay.addWidget(self.feedback)

        info = QHBoxLayout()
        info.setSpacing(18)
        self.thumb = QLabel("Sin miniatura")
        self.thumb.setObjectName("thumb")
        self.thumb.setFixedSize(256, 144)
        self.thumb.setAlignment(Qt.AlignCenter)
        meta = QGridLayout()
        meta.setVerticalSpacing(8)
        self.title_lbl = QLabel("Aún no hay video")
        self.title_lbl.setObjectName("videoTitle")
        self.title_lbl.setWordWrap(True)
        self.channel_lbl = QLabel("—")
        self.duration_lbl = QLabel("—")
        meta.addWidget(self.title_lbl, 0, 0, 1, 2)
        for i, (name, w) in enumerate([("Canal", self.channel_lbl), ("Duración", self.duration_lbl)], 1):
            k = QLabel(name)
            k.setObjectName("muted")
            meta.addWidget(k, i, 0)
            meta.addWidget(w, i, 1)
        meta.setRowStretch(3, 1)
        meta.setColumnStretch(1, 1)
        info.addWidget(self.thumb)
        info.addLayout(meta, 1)
        lay.addLayout(info)

        lay.addWidget(_section("Formato"))
        seg = QHBoxLayout()
        seg.setSpacing(8)
        self.video_btn = QPushButton("Video")
        self.audio_btn = QPushButton("Solo audio")
        group = QButtonGroup(self)
        group.setExclusive(True)
        for b in (self.video_btn, self.audio_btn):
            b.setObjectName("seg")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            group.addButton(b)
            seg.addWidget(b)
        seg.addStretch(1)
        self.video_btn.setChecked(True)
        lay.addLayout(seg)

        self.stack = QStackedWidget()
        video_page = QWidget()
        vl = QHBoxLayout(video_page)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.addWidget(self._labeled("Calidad", self._make_quality_combo()))
        audio_page = QWidget()
        al = QHBoxLayout(audio_page)
        al.setContentsMargins(0, 0, 0, 0)
        self.audio_fmt_combo = QComboBox()
        for f in AUDIO_FORMATS:
            self.audio_fmt_combo.addItem(f.upper(), f)
        self.bitrate_combo = QComboBox()
        for b in AUDIO_BITRATES:
            self.bitrate_combo.addItem(f"{b} kbps", b)
        self.bitrate_combo.setCurrentIndex(1)
        self.audio_fmt_combo.currentIndexChanged.connect(self._sync_bitrate)
        al.addWidget(self._labeled("Formato", self.audio_fmt_combo), 1)
        al.addWidget(self._labeled("Bitrate", self.bitrate_combo), 1)
        self.stack.addWidget(video_page)
        self.stack.addWidget(audio_page)
        self.video_btn.toggled.connect(lambda on: self.stack.setCurrentIndex(0 if on else 1))
        lay.addWidget(self.stack)

        lay.addWidget(_section("Guardar en"))
        drow = QHBoxLayout()
        self.dest_edit = QLineEdit(self._dest)
        self.dest_edit.setReadOnly(True)
        browse = QPushButton("Examinar…")
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self.choose_folder)
        drow.addWidget(self.dest_edit, 1)
        drow.addWidget(browse)
        lay.addLayout(drow)

        lay.addStretch(1)
        self.add_btn = QPushButton("Agregar a la cola")
        self.add_btn.setObjectName("primary")
        self.add_btn.setCursor(Qt.PointingHandCursor)
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.add_to_queue)
        lay.addWidget(self.add_btn)
        return card

    def _make_quality_combo(self) -> QComboBox:
        self.quality_combo = QComboBox()
        self.quality_combo.setEnabled(False)
        return self.quality_combo

    @staticmethod
    def _labeled(text: str, widget: QWidget) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        lbl = QLabel(text)
        lbl.setObjectName("muted")
        v.addWidget(lbl)
        v.addWidget(widget)
        return box

    def _build_right(self) -> QWidget:
        card, lay = _card()
        head = QHBoxLayout()
        head.addWidget(_section("Cola de descargas"))
        head.addStretch(1)
        self.clear_btn = QPushButton("Limpiar terminadas")
        self.clear_btn.setObjectName("link")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self.clear_finished)
        head.addWidget(self.clear_btn)
        lay.addLayout(head)

        self.empty_lbl = QLabel("La cola está vacía.\nAnaliza un enlace y agrégalo para empezar.")
        self.empty_lbl.setObjectName("muted")
        self.empty_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.empty_lbl, 1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        host = QWidget()
        self.list_layout = QVBoxLayout(host)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(10)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(host)
        lay.addWidget(self.scroll, 1)
        return card

    # ---------- análisis ----------
    def _set_feedback(self, text: str, kind: str = "") -> None:
        self.feedback.setText(text)
        self.feedback.setProperty("kind", kind)
        self.feedback.style().unpolish(self.feedback)
        self.feedback.style().polish(self.feedback)

    def analyze(self) -> None:
        if self._analyze_worker and self._analyze_worker.isRunning():
            return
        self.analyze_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self._set_feedback("Analizando…")
        w = AnalyzeWorker(self.url_edit.text())
        w.finished_ok.connect(self._on_analyzed)
        w.failed.connect(self._on_analyze_failed)
        self._analyze_worker = w
        w.start()

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
        self._select_default_quality()
        self.add_btn.setEnabled(True)
        self._set_feedback("Listo. Elige el formato y agrégalo a la cola.", "ok")

    def _select_default_quality(self) -> None:
        """Elige la calidad por defecto guardada o, si no existe, la mayor que no la supere."""
        want = self.cfg.default_height
        if want is None:
            return
        for i in range(self.quality_combo.count()):
            h = self.quality_combo.itemData(i)
            if h is not None and h <= want:
                self.quality_combo.setCurrentIndex(i)
                return

    def _on_analyze_failed(self, message: str) -> None:
        self.analyze_btn.setEnabled(True)
        self._set_feedback(message, "error")

    # ---------- opciones ----------
    def _sync_bitrate(self) -> None:
        self.bitrate_combo.setEnabled(bitrate_applies(self.audio_fmt_combo.currentData()))

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Carpeta de destino", self._dest)
        if folder:
            self._dest = folder
            self.dest_edit.setText(folder)
            self._save_preferences()

    def add_to_queue(self) -> None:
        if not self._info:
            return
        self._save_preferences()
        common = {"dest_dir": self._dest, "ffmpeg_dir": ffmpeg_location(),
                  "outtmpl": self.cfg.filename_template}
        if self.audio_btn.isChecked():
            fmt = self.audio_fmt_combo.currentData()
            bitrate = self.bitrate_combo.currentData() if bitrate_applies(fmt) else None
            options = build_options(Mode.AUDIO, audio_format=fmt, audio_bitrate=bitrate, **common)
            label = f"{fmt.upper()} · {bitrate} kbps" if bitrate else fmt.upper()
        else:
            height = self.quality_combo.currentData()
            options = build_options(Mode.VIDEO, height=height, **common)
            label = f"{height}p" if height else "Mejor calidad"
        job = self.queue.add(self._info.url, self._info.title, options, label)
        item = QueueItem(job)
        item.action_requested.connect(self._on_item_action)
        self._items[job.id] = item
        self.list_layout.insertWidget(self.list_layout.count() - 1, item)
        self._refresh_empty_state()
        self._set_feedback(f"Agregado a la cola: {job.title}", "ok")
        self._pump()

    # ---------- cola ----------
    def _refresh_empty_state(self) -> None:
        empty = not self.queue.jobs
        self.empty_lbl.setVisible(empty)
        self.scroll.setVisible(not empty)
        self.clear_btn.setEnabled(any(j.finished for j in self.queue.jobs))

    def _pump(self) -> None:
        """Inicia el siguiente trabajo pendiente si no hay uno en curso."""
        job = self.queue.next_pending()
        if job is None:
            return
        self.queue.start(job.id)
        self._items[job.id].update_job(job, "Iniciando…")
        w = DownloadWorker(job.url, job.options)
        w.progress.connect(lambda p, jid=job.id: self._on_progress(jid, p))
        w.finished_ok.connect(lambda jid=job.id: self._on_job_end(jid, JobStatus.DONE))
        w.cancelled.connect(lambda jid=job.id: self._on_job_end(jid, JobStatus.CANCELLED, "Cancelado"))
        w.failed.connect(lambda msg, jid=job.id: self._on_job_end(jid, JobStatus.ERROR, msg))
        w.finished.connect(lambda w=w: self._workers.discard(w))
        self._workers.add(w)
        self._active_worker = w
        w.start()

    def _on_progress(self, job_id: int, p: Progress) -> None:
        job = self.queue.get(job_id)
        if job is None:
            return
        job.percent = p.percent
        detail = ("Procesando…" if p.status == "processing"
                  else f"{p.percent:.1f}%  ·  {p.speed_label}  ·  quedan {p.eta_label}")
        self._items[job_id].update_job(job, detail)

    def _on_job_end(self, job_id: int, status: JobStatus, message: str = "") -> None:
        job = self.queue.finish(job_id, status, message)
        self._items[job_id].update_job(job)
        self._active_worker = None
        self._refresh_empty_state()
        if status == JobStatus.ERROR and "\n" in message:
            QMessageBox.warning(self, "D-ZEN", message)
        QTimer.singleShot(0, self._pump)

    def _on_item_action(self, job_id: int) -> None:
        job = self.queue.get(job_id)
        if job is None:
            return
        if job.status == JobStatus.RUNNING:
            if self._active_worker:
                self._active_worker.cancel()
                self._items[job_id].status.setText("Cancelando…")
        elif job.status == JobStatus.PENDING:
            self.queue.cancel_pending(job_id)
            self._items[job_id].update_job(job)
            self._refresh_empty_state()
        else:
            self._remove_item(job_id)

    def _remove_item(self, job_id: int) -> None:
        if self.queue.remove(job_id):
            item = self._items.pop(job_id)
            self.list_layout.removeWidget(item)
            item.deleteLater()
            self._refresh_empty_state()

    def clear_finished(self) -> None:
        for job_id in self.queue.clear_finished():
            item = self._items.pop(job_id)
            self.list_layout.removeWidget(item)
            item.deleteLater()
        self._refresh_empty_state()

    # ---------- cierre ----------
    def closeEvent(self, event) -> None:
        for job in self.queue.jobs:
            if job.status == JobStatus.PENDING:
                self.queue.cancel_pending(job.id)
        self._save_preferences()
        for w in list(self._workers):
            w.cancel()
        for w in list(self._workers) + ([self._analyze_worker] if self._analyze_worker else []):
            if w.isRunning():
                w.wait(4000)
        super().closeEvent(event)
