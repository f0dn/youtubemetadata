"""Tests for the raw YouTube Music metadata disk cache."""

from pathlib import Path

from youtubemetadata import cache


def test_load_raw_returns_none_when_missing(tmp_path: Path) -> None:
    assert cache.load_raw(tmp_path / "missing.json") is None


def test_save_load_raw_roundtrip(tmp_path: Path) -> None:
    data = {"videoId": "abc", "title": "Song"}
    cache.save_raw(tmp_path / "abc.json", data)
    assert cache.load_raw(tmp_path / "abc.json") == data


def test_load_album_uses_album_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cache, "ALBUM_DIR", tmp_path)
    cache.save_album("ALB1", {"id": "ALB1"})
    assert cache.load_album("ALB1") == {"id": "ALB1"}


def test_load_song_uses_song_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(cache, "SONG_DIR", tmp_path)
    cache.save_song("S1", {"id": "S1"})
    assert cache.load_song("S1") == {"id": "S1"}
