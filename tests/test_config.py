import json
import subprocess
import sys

import pytest

from d_zen.core import config, updater
from d_zen.core.config import Config


def test_defaults_when_missing(tmp_path):
    cfg = config.load(tmp_path / "nope.json")
    assert cfg.audio_format == "mp3" and cfg.audio_bitrate == 192
    assert cfg.default_height is None and cfg.filename_template == "%(title)s.%(ext)s"
    assert cfg.dest_dir  # carpeta de descargas por defecto


def test_roundtrip(tmp_path):
    p = tmp_path / "sub" / "c.json"
    cfg = Config(dest_dir="C:/V", audio_mode=True, audio_format="opus", audio_bitrate=320,
                 default_height=720, filename_template="%(uploader)s - %(title)s.%(ext)s")
    config.save(cfg, p)
    assert config.load(p) == cfg


@pytest.mark.parametrize("content", ["{no json", "[1, 2]", ""])
def test_corrupt_file_gives_defaults(tmp_path, content):
    p = tmp_path / "c.json"
    p.write_text(content, encoding="utf-8")
    assert config.load(p) == Config()


def test_invalid_values_are_fixed_and_unknown_keys_ignored(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "audio_format": "flac", "audio_bitrate": 64, "default_height": -5,
        "filename_template": "../x", "dest_dir": "", "otra_clave": 1,
    }), encoding="utf-8")
    cfg = config.load(p)
    assert cfg.audio_format == "mp3" and cfg.audio_bitrate == 192
    assert cfg.default_height is None and cfg.filename_template == "%(title)s.%(ext)s"
    assert cfg.dest_dir


def test_updater_refuses_when_frozen(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert updater.can_update() is False
    with pytest.raises(updater.UpdateError):
        updater.update_ytdlp()


def test_updater_pip_failure(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(
        a, 1, stdout="", stderr="ERROR: no network\n"))
    with pytest.raises(updater.UpdateError, match="no network"):
        updater.update_ytdlp()


def test_updater_success(monkeypatch):
    def fake(cmd, **k):
        return subprocess.CompletedProcess(cmd, 0, stdout="2099.01.01\n" if "-c" in cmd else "ok", stderr="")
    monkeypatch.setattr(subprocess, "run", fake)
    assert updater.update_ytdlp() == "2099.01.01"


def test_installed_version_is_string():
    assert updater.installed_version()
