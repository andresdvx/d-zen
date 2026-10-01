"""Tarjeta de un trabajo de la cola."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy, QVBoxLayout

from d_zen.core.queue import DownloadJob, JobStatus

_STATE = {
    JobStatus.PENDING: ("En espera", "pending"),
    JobStatus.RUNNING: ("Descargando…", "running"),
    JobStatus.DONE: ("Completado", "done"),
    JobStatus.ERROR: ("Error", "error"),
    JobStatus.CANCELLED: ("Cancelado", "cancelled"),
}


class ElidedLabel(QLabel):
    """QLabel de una línea que recorta con «…» según el ancho disponible."""

    def __init__(self, text: str = "") -> None:
        super().__init__(text)
        self._full = text
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setToolTip(text)

    def paintEvent(self, event) -> None:
        self.setText(self.fontMetrics().elidedText(self._full, Qt.ElideRight, self.width()))
        super().paintEvent(event)


class QueueItem(QFrame):
    """Emite action_requested(job_id): cancelar si está activo/pendiente, quitar si terminó."""
    action_requested = Signal(int)

    def __init__(self, job: DownloadJob) -> None:
        super().__init__()
        self.job_id = job.id
        self.setObjectName("jobItem")

        self.title = ElidedLabel(job.title)
        self.title.setStyleSheet("font-weight: 600;")
        self.badge = QLabel(job.label)
        self.badge.setObjectName("muted")
        self.status = QLabel()
        self.status.setObjectName("muted")
        self.status.setWordWrap(True)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.button = QPushButton("✕")
        self.button.setObjectName("icon")
        self.button.setCursor(Qt.PointingHandCursor)
        self.button.clicked.connect(lambda: self.action_requested.emit(self.job_id))

        top = QHBoxLayout()
        top.addWidget(self.title, 1)
        top.addWidget(self.badge)
        top.addWidget(self.button)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 10, 12)
        root.setSpacing(6)
        root.addLayout(top)
        root.addWidget(self.bar)
        root.addWidget(self.status)
        self.update_job(job)

    def update_job(self, job: DownloadJob, detail: str = "") -> None:
        text, state = _STATE[job.status]
        if job.status == JobStatus.RUNNING and detail:
            text = detail
        elif job.status in (JobStatus.ERROR, JobStatus.CANCELLED) and job.message:
            text = job.message.splitlines()[0]
            self.status.setToolTip(job.message)
        self.status.setText(text)
        self.bar.setValue(int(job.percent * 10))
        for w in (self, self.bar):
            w.setProperty("state", state)
            w.style().unpolish(w)
            w.style().polish(w)
        self.button.setToolTip("Quitar de la lista" if job.finished else "Cancelar")
