"""Phase 3 — download audio via yt-dlp Python API."""

from unittest.mock import MagicMock, patch

from youtubemetadata.models import PlaylistResolution, TrackEntry
from youtubemetadata.phases import download as download_phase


def _resolution() -> PlaylistResolution:
    return PlaylistResolution(
        playlistId="PLabc",
        playlistTitle="Test",
        totalTracks=1,
        uniqueAlbums=1,
        tracks=[TrackEntry(index=1, videoId="atv1", title="Song One", isAvailable=True)],
    )


def test_download_uses_yt_dlp_python_api() -> None:
    with patch("youtubemetadata.phases.download.yt_dlp.YoutubeDL") as mock_ydl:
        instance = MagicMock()
        instance.download.return_value = 0
        mock_ydl.return_value.__enter__.return_value = instance

        result = download_phase.phase_download(_resolution())

        assert result is not None
        assert mock_ydl.call_count == 1
        opts = mock_ydl.call_args.args[0]
        assert opts["format"] == "bestaudio[ext=m4a]/bestaudio"
        assert opts["merge_output_format"] == "m4a"
        assert opts["writethumbnail"] is True
        assert opts["noplaylist"] is True
        assert "atv1" in str(opts["outtmpl"])
        instance.download.assert_called_once_with(["https://www.youtube.com/watch?v=atv1"])
