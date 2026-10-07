import json
import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from app import media

pytestmark = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="no ffmpeg")


def make_video(tmp_path, suffix="mkv", codec="srt", english=True):
    fr = tmp_path / "fr.srt"
    en = tmp_path / "en.srt"
    fr.write_text("1\n00:00:00,000 --> 00:00:00,800\nBonjour.\n", encoding="utf-8")
    en.write_text("1\n00:00:00,000 --> 00:00:00,800\nTake your jacket.\n", encoding="utf-8")
    out = tmp_path / ("video." + suffix)
    cmd = [media._exe("ffmpeg"), "-y", "-f", "lavfi", "-i", "color=s=64x64:d=1",
           "-i", str(fr)]
    if english:
        cmd += ["-i", str(en)]
    cmd += ["-map", "0:v", "-map", "1:0"]
    if english:
        cmd += ["-map", "2:0"]
    cmd += ["-c:v", "libx264", "-c:s", codec, "-metadata:s:s:0", "language=fra"]
    if english:
        cmd += ["-metadata:s:s:1", "language=eng"]
    subprocess.run(cmd + [str(out)], check=True, capture_output=True)
    return out


@pytest.mark.parametrize(("suffix", "codec"), [("mkv", "srt"), ("mkv", "ass"), ("mp4", "mov_text")])
def test_extracts_english_not_first_foreign_track(tmp_path, suffix, codec):
    src = make_video(tmp_path, suffix, codec)
    text = media.extract_english_subtitles(src)
    assert "Take your jacket." in text
    assert "Bonjour" not in text
    playable = media.ensure_browser_playable(src, tmp_path)
    assert playable.exists()
    subprocess.run([media._exe("ffmpeg"), "-v", "error", "-i", str(playable),
                    "-f", "null", "-"], check=True, capture_output=True)


def test_non_english_track_does_not_disable_whisper(tmp_path):
    assert media.extract_english_subtitles(make_video(tmp_path, english=False)) == ""


def test_full_track_preferred_and_bitmap_ignored(monkeypatch, tmp_path):
    selected = []
    streams = [
        {"index": 1, "codec_name": "hdmv_pgs_subtitle", "tags": {"language": "eng"}},
        {"index": 2, "codec_name": "subrip", "tags": {"language": "eng"}, "disposition": {"forced": 1, "default": 1}},
        {"index": 3, "codec_name": "ass", "tags": {"language": "en-US"}, "disposition": {"forced": 0}},
    ]

    def run(cmd, **kwargs):
        if "-show_streams" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps({"streams": streams}))
        selected.append(cmd[cmd.index("-map") + 1])
        return subprocess.CompletedProcess(cmd, 0, stdout="1\n00:00:00,000 --> 00:00:01,000\nFull captions.\n")

    monkeypatch.setattr(media.subprocess, "run", run)
    assert "Full captions" in media.extract_english_subtitles(tmp_path / "test.mkv")
    assert selected == ["0:3"]


def test_upload_loads_original_subtitles_without_whisper(tmp_path, monkeypatch):
    from app import main, transcribe

    src = make_video(tmp_path)
    dl = tmp_path / "downloads"
    dl.mkdir()
    monkeypatch.setattr(main.config, "DL_DIR", dl)
    monkeypatch.setattr(main, "CON", main.db.connect(tmp_path / "app.db"))
    monkeypatch.setattr(main.nlp, "tokenize", lambda text: [])
    monkeypatch.setattr(main.languages, "active_code", lambda: "en")

    def no_whisper(*args, **kwargs):
        pytest.fail("Whisper must not run for original English subtitles")

    monkeypatch.setattr(transcribe, "transcribe", no_whisper)
    c = TestClient(main.app)
    with src.open("rb") as f:
        jid = c.post("/api/sessions/upload", files={"file": (src.name, f)}).json()["job_id"]
    for _ in range(200):
        job = c.get("/api/jobs/" + jid).json()
        if job["status"] != "running":
            break
        time.sleep(0.05)
    assert job["status"] == "done", job
    sid = job["result"]["session_id"]
    session = main.db.get_session(main.CON, sid)
    assert session["srt_source"] == "embedded"
    assert json.loads(session["transcript_json"])[0]["text"] == "Take your jacket."
    response = c.post(f"/api/sessions/{sid}/transcribe", json={"model": "small"})
    assert response.status_code == 400
    assert response.json()["error_key"] == "err.original_subs"
