import threading

import pytest

from d_zen.core import downloader as dl
from d_zen.core.downloader import (
    CancelledError, FfmpegMissingError, InvalidURLError, NetworkError, UnavailableError,
    classify_error,
)
from d_zen.core.filenames import sanitize_filename, validate_template


class FakeYDL:
    """Sustituto de yt_dlp.YoutubeDL sin red."""
    info: dict | None = {"title": "T", "uploader": "U", "duration": 3725, "thumbnail": "http://x/t.jpg",
                         "formats": [{"vcodec": "avc1", "acodec": "mp4a", "height": 720, "filesize": 1}]}
    raises: Exception | None = None
    events: list[dict] = []

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download=False):
        if self.raises:
            raise self.raises
        return self.info

    def download(self, urls):
        for ev in self.events:
            for h in self.opts["progress_hooks"]:
                h(ev)
        if self.raises:
            raise self.raises


def factory(**attrs):
    return type("F", (FakeYDL,), attrs)


def test_analyze_ok():
    info = dl.analyze("https://example.com/v", ydl_factory=factory())
    assert info.title == "T" and info.channel == "U"
    assert info.duration_label == "1:02:05"
    assert [q.height for q in info.qualities] == [None, 720]


@pytest.mark.parametrize("url", ["", "hola", "ftp://x.com/a", "http://a b.com"])
def test_analyze_invalid_url(url):
    with pytest.raises(InvalidURLError):
        dl.analyze(url, ydl_factory=factory())


def test_analyze_maps_errors():
    with pytest.raises(UnavailableError):
        dl.analyze("https://e.com/v", ydl_factory=factory(raises=Exception("ERROR: Private video")))
    with pytest.raises(NetworkError):
        dl.analyze("https://e.com/v", ydl_factory=factory(raises=Exception("getaddrinfo failed")))


def test_classify_error():
    assert isinstance(classify_error(Exception("Unsupported URL: x")), InvalidURLError)
    assert isinstance(classify_error(Exception("ffmpeg not found")), FfmpegMissingError)
    assert type(classify_error(Exception("algo raro"))) is dl.DownloaderError


def test_download_reports_progress():
    events = [
        {"status": "downloading", "downloaded_bytes": 50, "total_bytes": 200, "speed": 1048576, "eta": 75},
        {"status": "finished"},
    ]
    got = []
    dl.download("https://e.com/v", {"format": "best"}, on_progress=got.append,
                ydl_factory=factory(events=events))
    assert got[0].percent == 25.0 and got[0].eta_label == "01:15" and got[0].speed_label == "1.00 MB/s"
    assert got[1].status == "processing"


def test_download_cancel():
    cancel = threading.Event()
    cancel.set()
    events = [{"status": "downloading", "downloaded_bytes": 1, "total_bytes": 2}]
    with pytest.raises(CancelledError):
        dl.download("https://e.com/v", {"format": "best"}, cancel=cancel,
                    ydl_factory=factory(events=events))


def test_download_requires_ffmpeg(monkeypatch):
    monkeypatch.setattr(dl, "find_ffmpeg", lambda: None)
    with pytest.raises(FfmpegMissingError):
        dl.download("https://e.com/v", {"format": "bestvideo+bestaudio/best"}, ydl_factory=factory())
    # sin necesidad de ffmpeg no falla
    dl.download("https://e.com/v", {"format": "best"}, ydl_factory=factory())


def test_sanitize_filename():
    assert sanitize_filename('a<b>:c"d/e\\f|g?h*') == "a_b__c_d_e_f_g_h_"
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("fin. ") == "fin"
    assert sanitize_filename("   ") == "video"


def test_validate_template():
    assert validate_template("") == "%(title)s.%(ext)s"
    assert validate_template("%(uploader)s - %(title)s") == "%(uploader)s - %(title)s.%(ext)s"
    assert validate_template("C:\\x\\%(title)s.%(ext)s") == "%(title)s.%(ext)s"
    assert validate_template("%(title)s.%(ext)s") == "%(title)s.%(ext)s"
