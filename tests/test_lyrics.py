"""Tests for Phase 2 — fetch lyrics for the resolved tracks."""

from types import SimpleNamespace

from youtubemetadata.models import PlaylistResolution, TrackEntry
from youtubemetadata.phases import lyrics as lyrics_phase


def _resolution() -> PlaylistResolution:
    return PlaylistResolution(
        playlistId="PLabc",
        playlistTitle="Test",
        totalTracks=1,
        uniqueAlbums=1,
        tracks=[TrackEntry(index=1, videoId="atv1", title="Song One", isAvailable=True)],
    )


class FakeLyricsService:
    def __init__(self, watch: dict, lyrics: dict | None) -> None:
        self._watch = watch
        self._lyrics = lyrics
        self.watch_calls: list[str] = []
        self.lyrics_calls: list[str] = []

    def get_watch_playlist(self, video_id: str) -> dict:
        self.watch_calls.append(video_id)
        return self._watch

    def get_lyrics(self, browse_id: str) -> dict | None:
        self.lyrics_calls.append(browse_id)
        return self._lyrics


def test_phase_lyrics_sets_lyrics_from_string() -> None:
    svc = FakeLyricsService(
        watch={"lyrics": {"browseId": "LYR1"}}, lyrics={"lyrics": "la la", "source": "s"}
    )
    resolution = _resolution()
    result = lyrics_phase.phase_lyrics(resolution, service=svc)
    assert result is resolution
    assert resolution.tracks[0].lyrics == "la la"
    assert resolution.tracks[0].lyricsSource == "s"
    assert svc.watch_calls == ["atv1"]
    assert svc.lyrics_calls == ["LYR1"]


def test_phase_lyrics_joins_list_of_lines() -> None:
    svc = FakeLyricsService(
        watch={"lyrics": {"browseId": "LYR1"}},
        lyrics={
            "lyrics": [SimpleNamespace(text="Hello"), SimpleNamespace(text="World")],
            "source": "yt",
        },
    )
    resolution = _resolution()
    lyrics_phase.phase_lyrics(resolution, service=svc)
    assert resolution.tracks[0].lyrics == "Hello\nWorld"


def test_phase_lyrics_without_lyrics_id() -> None:
    svc = FakeLyricsService(watch={}, lyrics=None)
    resolution = _resolution()
    result = lyrics_phase.phase_lyrics(resolution, service=svc)
    assert result is resolution
    assert resolution.tracks[0].lyrics is None


def test_phase_lyrics_handles_service_error() -> None:
    class ExplodingService(FakeLyricsService):
        def get_watch_playlist(self, video_id: str) -> dict:
            msg = "boom"
            raise RuntimeError(msg)

    resolution = _resolution()
    result = lyrics_phase.phase_lyrics(resolution, service=ExplodingService(watch={}, lyrics=None))
    assert result is resolution
    assert resolution.tracks[0].lyrics is None
