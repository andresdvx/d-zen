"""Cola de descargas en orden FIFO. Lógica pura, sin dependencias de PySide6."""
from dataclasses import dataclass, field
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


_FINISHED = {JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED}


@dataclass
class DownloadJob:
    id: int
    url: str
    title: str
    options: dict
    label: str  # descripción corta de lo que se baja, p. ej. "1080p" o "MP3 · 192 kbps"
    status: JobStatus = JobStatus.PENDING
    percent: float = 0.0
    message: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def finished(self) -> bool:
        return self.status in _FINISHED


class DownloadQueue:
    def __init__(self) -> None:
        self._jobs: list[DownloadJob] = []
        self._next_id = 1

    @property
    def jobs(self) -> list[DownloadJob]:
        return list(self._jobs)

    def add(self, url: str, title: str, options: dict, label: str = "") -> DownloadJob:
        job = DownloadJob(self._next_id, url, title, options, label)
        self._next_id += 1
        self._jobs.append(job)
        return job

    def get(self, job_id: int) -> DownloadJob | None:
        return next((j for j in self._jobs if j.id == job_id), None)

    def running(self) -> DownloadJob | None:
        return next((j for j in self._jobs if j.status == JobStatus.RUNNING), None)

    def next_pending(self) -> DownloadJob | None:
        """Siguiente trabajo en orden de llegada; None si ya hay uno en curso o no hay pendientes."""
        if self.running():
            return None
        return next((j for j in self._jobs if j.status == JobStatus.PENDING), None)

    def start(self, job_id: int) -> DownloadJob:
        job = self._require(job_id)
        job.status = JobStatus.RUNNING
        job.percent = 0.0
        job.message = ""
        return job

    def finish(self, job_id: int, status: JobStatus, message: str = "") -> DownloadJob:
        if status not in _FINISHED:
            raise ValueError("finish() requiere un estado final")
        job = self._require(job_id)
        job.status = status
        job.message = message
        if status == JobStatus.DONE:
            job.percent = 100.0
        return job

    def cancel_pending(self, job_id: int) -> bool:
        """Cancela un trabajo que aún no empezó. Devuelve False si no estaba pendiente."""
        job = self._require(job_id)
        if job.status != JobStatus.PENDING:
            return False
        job.status = JobStatus.CANCELLED
        job.message = "Cancelado"
        return True

    def remove(self, job_id: int) -> bool:
        """Quita un trabajo de la lista (no se puede quitar uno en curso)."""
        job = self._require(job_id)
        if job.status == JobStatus.RUNNING:
            return False
        self._jobs.remove(job)
        return True

    def clear_finished(self) -> list[int]:
        removed = [j.id for j in self._jobs if j.finished]
        self._jobs = [j for j in self._jobs if not j.finished]
        return removed

    def _require(self, job_id: int) -> DownloadJob:
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        return job
