import pytest

from d_zen.core.queue import DownloadQueue, JobStatus


def make(n=3):
    q = DownloadQueue()
    return q, [q.add(f"https://e.com/{i}", f"T{i}", {}, "720p") for i in range(n)]


def test_fifo_order_and_single_running():
    q, jobs = make()
    first = q.next_pending()
    assert first is jobs[0]
    q.start(first.id)
    assert q.next_pending() is None  # hay uno en curso
    q.finish(first.id, JobStatus.DONE)
    assert q.next_pending() is jobs[1]


def test_done_sets_percent_and_error_keeps_message():
    q, jobs = make(2)
    q.start(jobs[0].id)
    q.finish(jobs[0].id, JobStatus.DONE)
    assert jobs[0].percent == 100.0
    q.start(jobs[1].id)
    q.finish(jobs[1].id, JobStatus.ERROR, "sin conexión")
    assert jobs[1].message == "sin conexión" and jobs[1].finished


def test_cancel_pending_skipped_by_next():
    q, jobs = make()
    assert q.cancel_pending(jobs[0].id) is True
    assert q.next_pending() is jobs[1]
    q.start(jobs[1].id)
    assert q.cancel_pending(jobs[1].id) is False  # en curso: se cancela con el worker


def test_remove_not_running():
    q, jobs = make(2)
    q.start(jobs[0].id)
    assert q.remove(jobs[0].id) is False
    assert q.remove(jobs[1].id) is True
    assert len(q.jobs) == 1


def test_clear_finished():
    q, jobs = make()
    q.start(jobs[0].id)
    q.finish(jobs[0].id, JobStatus.DONE)
    q.cancel_pending(jobs[1].id)
    assert sorted(q.clear_finished()) == [jobs[0].id, jobs[1].id]
    assert q.jobs == [jobs[2]]


def test_finish_requires_final_state_and_unknown_id():
    q, jobs = make(1)
    with pytest.raises(ValueError):
        q.finish(jobs[0].id, JobStatus.RUNNING)
    with pytest.raises(KeyError):
        q.start(999)
