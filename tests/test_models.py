"""Typed models for YouTube Music metadata (pydantic)."""

from youtubemetadata.models import (
    AlbumRef,
    PlaylistResolution,
    SongCredits,
    Track,
    TrackEntry,
)


def test_track_album_accepts_string() -> None:
    track = Track.model_validate({"videoId": "abc", "title": "Song", "album": "Album Title"})
    assert track.album == "Album Title"


def test_track_album_accepts_ref() -> None:
    track = Track.model_validate(
        {"videoId": "abc", "title": "Song", "album": {"name": "A", "id": "MPREb_x"}}
    )
    assert track.album == AlbumRef(name="A", id="MPREb_x")


def test_track_entry_defaults() -> None:
    entry = TrackEntry(index=1)
    assert entry.videoId == ""
    assert entry.title == "Unknown"
    assert entry.artist == "Unknown"
    assert entry.artists == []
    assert entry.album == "Unknown"
    assert entry.albumArtist == []
    assert entry.trackNumber is None
    assert entry.trackTotal is None
    assert entry.isMusicVideo is False
    assert entry.musicVideoOf is None


def test_playlist_resolution_defaults() -> None:
    resolution = PlaylistResolution(
        playlistId="PLabc", playlistTitle="Best", totalTracks=3, uniqueAlbums=1
    )
    assert resolution.playlistId == "PLabc"
    assert resolution.tracks == []


def test_song_credits_defaults() -> None:
    credits = SongCredits()
    assert credits.performed_by is None
    assert credits.written_by is None
    assert credits.produced_by is None
    assert credits.other_sections == []
