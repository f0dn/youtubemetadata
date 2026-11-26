"""Phase 4 — write a Navidrome-compatible library."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from PIL import Image

from youtubemetadata.models import PlaylistResolution, TrackEntry
from youtubemetadata.phases import library as library_phase


def _resolution() -> PlaylistResolution:
    return PlaylistResolution(
        playlistId="PLabc",
        playlistTitle="Test",
        totalTracks=1,
        uniqueAlbums=1,
        tracks=[
            TrackEntry(
                index=1,
                videoId="atv1",
                title="Song One",
                artist="Artist One",
                album="Album One",
                albumArtist=["Artist One"],
                trackNumber=1,
                trackTotal=1,
                isAvailable=True,
            )
        ],
    )


def test_phase_library_copies_audio_and_writes_tags(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    raw_root = tmp_path / "raw"
    audio = raw_root / "atv1" / "audio.m4a"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"fake-audio")

    with (
        patch("youtubemetadata.phases.library.RAW_DIR", raw_root),
        patch("youtubemetadata.phases.library.MutagenFile") as mock_mutagen,
    ):
        mock_mutagen.return_value = MagicMock()
        result = library_phase.phase_library(_resolution(), lib)

    expected = lib / "Artist One" / "Album One" / "01 - Song One.m4a"
    assert result == lib
    assert expected.is_file()
    assert expected.read_bytes() == b"fake-audio"
    mock_mutagen.assert_called_once_with(expected)


def test_phase_library_does_not_clear_existing_library(tmp_path: Path) -> None:
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "keep.m4a").write_bytes(b"keep")

    with (
        patch("youtubemetadata.phases.library.RAW_DIR", tmp_path / "raw"),
        patch("youtubemetadata.phases.library.MutagenFile") as mock_mutagen,
    ):
        mock_mutagen.return_value = MagicMock()
        result = library_phase.phase_library(_resolution(), lib)

    assert result == lib
    assert (lib / "keep.m4a").exists()


def test_phase_library_skips_unavailable_tracks(tmp_path: Path) -> None:
    resolution = _resolution()
    resolution.tracks[0].isAvailable = False
    lib = tmp_path / "library"

    with (
        patch("youtubemetadata.phases.library.RAW_DIR", tmp_path / "raw"),
        patch("youtubemetadata.phases.library.MutagenFile") as mock_mutagen,
    ):
        mock_mutagen.return_value = MagicMock()
        result = library_phase.phase_library(resolution, lib)

    assert result == lib
    mock_mutagen.assert_not_called()


def test_phase_library_skips_unresolved_music_videos(tmp_path: Path) -> None:
    resolution = _resolution()
    resolution.tracks[0].isMusicVideo = True
    resolution.tracks[0].musicVideoOf = None
    resolution.tracks[0].videoId = ""
    lib = tmp_path / "library"

    with (
        patch("youtubemetadata.phases.library.RAW_DIR", tmp_path / "raw"),
        patch("youtubemetadata.phases.library.MutagenFile") as mock_mutagen,
    ):
        mock_mutagen.return_value = MagicMock()
        result = library_phase.phase_library(resolution, lib)

    assert result == lib
    mock_mutagen.assert_not_called()


def test_phase_library_includes_album_version_in_path(tmp_path: Path) -> None:
    resolution = _resolution()
    resolution.tracks[0].albumVersion = "Deluxe"
    lib = tmp_path / "library"
    raw_root = tmp_path / "raw"
    audio = raw_root / "atv1" / "audio.m4a"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"fake-audio")

    with (
        patch("youtubemetadata.phases.library.RAW_DIR", raw_root),
        patch("youtubemetadata.phases.library.MutagenFile") as mock_mutagen,
    ):
        mock_mutagen.return_value = MagicMock()
        result = library_phase.phase_library(resolution, lib)

    expected = lib / "Artist One" / "Album One (Deluxe)" / "01 - Song One.m4a"
    assert result == lib
    assert expected.is_file()
    assert expected.read_bytes() == b"fake-audio"


def test_write_tags_sets_navidrome_tags(tmp_path: Path) -> None:
    fake_mp4_class = type("FakeMP4", (), {"save": MagicMock()})
    tag = fake_mp4_class()
    tag.tags = MagicMock()

    with (
        patch("youtubemetadata.phases.library.MutagenFile", return_value=tag),
        patch("youtubemetadata.phases.library.MP4Tag", fake_mp4_class),
    ):
        ok = library_phase._write_tags(
            tmp_path / "song.m4a",
            {
                "title": "Song One",
                "artist": "Artist One",
                "artists": ["Artist One"],
                "track": 1,
                "tracktotal": 12,
                "lyrics": "la la la",
            },
        )

    assert ok is True
    tag.tags.__setitem__.assert_any_call("\N{COPYRIGHT SIGN}nam", "Song One")
    tag.tags.__setitem__.assert_any_call("\N{COPYRIGHT SIGN}ART", "Artist One")
    tag.tags.__setitem__.assert_any_call("----:com.apple.iTunes:artists", [b"Artist One"])
    tag.tags.__setitem__.assert_any_call("----:com.apple.iTunes:lyrics", b"la la la")
    tag.tags.__setitem__.assert_any_call("trkn", [(1, 12)])
    tag.save.assert_called_once()


def test_tag_values_map_navidrome_fields() -> None:
    entry = TrackEntry(
        index=1,
        title="Song One",
        artist="Artist One",
        album="Album One",
        trackNumber=3,
        trackTotal=12,
        isExplicit=True,
        albumVersion="Deluxe",
        writtenBy=["Writer A"],
        producedBy=["Producer B"],
    )
    values = library_phase._tag_values(entry)
    assert values["title"] == "Song One"
    assert values["artists"] == ["Unknown"]
    assert values["albumartists"] == ["Unknown"]
    assert values["album"] == "Album One"
    assert values["composer"] == "Writer A"
    assert values["producer"] == "Producer B"
    assert values["albumversion"] == "Deluxe"
    assert values["track"] == 3
    assert values["tracktotal"] == 12
    assert values.get("releasedate") is None
    assert values["explicitstatus"] == 1
    assert values.get("comment") is None


def test_tag_values_join_multiple_artists_with_feat() -> None:
    entry = TrackEntry(
        index=1,
        title="Empire State of Mind",
        artists=["Jay-Z", "Alicia Keys"],
        album="Album One",
        albumArtist=["Jay-Z"],
        trackNumber=1,
        trackTotal=2,
    )
    values = library_phase._tag_values(entry)
    assert values["artists"] == ["Jay-Z"]
    assert values["albumartists"] == ["Jay-Z"]
    assert values["album"] == "Album One"
    assert values["track"] == 1
    assert values["tracktotal"] == 2


def test_embed_cover_writes_apic(tmp_path: Path) -> None:
    audio = tmp_path / "song.m4a"
    audio.write_bytes(b"fake")
    cover = tmp_path / "art.jpg"
    Image.new("RGB", (1, 1)).save(cover, format="JPEG")

    fake_mp4_class = type("FakeMP4", (), {"save": MagicMock()})
    tag = fake_mp4_class()
    tag.tags = MagicMock()

    with (
        patch("youtubemetadata.phases.library.MutagenFile", return_value=tag),
        patch("youtubemetadata.phases.library.MP4Tag", fake_mp4_class),
    ):
        ok = library_phase._embed_cover(audio, cover)

    assert ok is True
    tag.tags.__setitem__.assert_called_once()
    assert tag.tags.__setitem__.call_args.args[0] == "covr"
    tag.save.assert_called_once()


def test_embed_cover_returns_false_without_cover(tmp_path: Path) -> None:
    audio = tmp_path / "song.m4a"
    audio.write_bytes(b"fake")
    assert library_phase._embed_cover(audio, None) is False
    assert library_phase._embed_cover(audio, tmp_path / "missing.webp") is False
