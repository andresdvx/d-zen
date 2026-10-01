import pytest

from d_zen.core.formats import (
    AUDIO_BITRATES, BEST, Mode, build_options, format_size, parse_qualities,
)

INFO = {
    "formats": [
        {"format_id": "140", "vcodec": "none", "acodec": "mp4a", "filesize": 5_000_000, "tbr": 128},
        {"format_id": "251", "vcodec": "none", "acodec": "opus", "filesize": 4_000_000, "tbr": 130},
        {"format_id": "137", "vcodec": "avc1", "acodec": "none", "height": 1080,
         "filesize": 100_000_000, "tbr": 4000},
        {"format_id": "248", "vcodec": "vp9", "acodec": "none", "height": 1080,
         "filesize": 60_000_000, "tbr": 2500},
        {"format_id": "136", "vcodec": "avc1", "acodec": "none", "height": 720,
         "filesize_approx": 40_000_000, "tbr": 1500},
        {"format_id": "18", "vcodec": "avc1", "acodec": "mp4a", "height": 360,
         "filesize": 15_000_000, "tbr": 500},
        {"format_id": "sb0", "vcodec": "none", "acodec": "none", "height": 90},  # storyboard
        {"format_id": "x", "vcodec": "avc1", "acodec": "none", "height": 480},  # sin tamaño
    ]
}


def test_parse_qualities_sorted_and_best_first():
    opts = parse_qualities(INFO)
    assert opts[0] == BEST
    assert [o.height for o in opts[1:]] == [1080, 720, 480, 360]


def test_parse_qualities_ignores_storyboards_and_audio_only():
    heights = [o.height for o in parse_qualities(INFO)]
    assert 90 not in heights


def test_size_adds_best_audio_when_video_only():
    by_h = {o.height: o for o in parse_qualities(INFO)}
    assert by_h[1080].filesize == 100_000_000 + 5_000_000  # mayor tbr + mejor audio
    assert by_h[720].filesize == 40_000_000 + 5_000_000


def test_size_not_added_when_format_has_audio():
    by_h = {o.height: o for o in parse_qualities(INFO)}
    assert by_h[360].filesize == 15_000_000


def test_size_missing_gives_no_label():
    by_h = {o.height: o for o in parse_qualities(INFO)}
    assert by_h[480].filesize is None
    assert by_h[480].display == "480p"
    assert "~" in by_h[1080].display


def test_parse_qualities_empty_info():
    assert parse_qualities({}) == [BEST]


def test_format_size():
    assert format_size(None) == ""
    assert format_size(512) == "512 B"
    assert format_size(1536) == "1.5 KB"
    assert format_size(105_000_000) == "100.1 MB"


def test_video_best():
    o = build_options(Mode.VIDEO)
    assert o["format"] == "bestvideo+bestaudio/best"
    assert o["merge_output_format"] == "mp4"
    assert o["noplaylist"] is True
    assert "postprocessors" not in o


def test_video_height():
    o = build_options(Mode.VIDEO, height=720)
    assert o["format"] == "bestvideo[height<=720]+bestaudio/best[height<=720]/best"


def test_audio_mp3_with_bitrate():
    o = build_options(Mode.AUDIO, audio_format="mp3", audio_bitrate=320)
    assert o["format"] == "bestaudio/best"
    assert o["postprocessors"] == [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}
    ]


def test_audio_wav_has_no_bitrate():
    o = build_options(Mode.AUDIO, audio_format="wav", audio_bitrate=320)
    assert "preferredquality" not in o["postprocessors"][0]


@pytest.mark.parametrize("br", AUDIO_BITRATES)
def test_audio_bitrates_accepted(br):
    build_options(Mode.AUDIO, audio_format="m4a", audio_bitrate=br)


def test_invalid_audio_format_and_bitrate():
    with pytest.raises(ValueError):
        build_options(Mode.AUDIO, audio_format="flac")
    with pytest.raises(ValueError):
        build_options(Mode.AUDIO, audio_format="mp3", audio_bitrate=64)


def test_outtmpl_dest_and_ffmpeg():
    o = build_options(dest_dir="C:/Videos", ffmpeg_dir="C:/ff")
    assert o["outtmpl"] == "C:/Videos/%(title)s.%(ext)s"
    assert o["ffmpeg_location"] == "C:/ff"


def test_unsafe_template_falls_back():
    o = build_options(outtmpl="../../evil.%(ext)s")
    assert o["outtmpl"] == "%(title)s.%(ext)s"
